from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed GridRAG demo residents, events, and visit records.")
    parser.add_argument(
        "--data-dir",
        default=str(PROJECT_ROOT / "data" / "structured"),
        help="Directory containing residents.csv, events.csv, and visits.csv",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate files and print counts without writing to DB")
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_dt(value: str) -> datetime | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    return datetime.fromisoformat(cleaned)


async def seed(data_dir: Path, dry_run: bool) -> dict[str, int]:
    residents_rows = read_csv_rows(data_dir / "residents.csv")
    events_rows = read_csv_rows(data_dir / "events.csv")
    visits_rows = read_csv_rows(data_dir / "visits.csv")

    if dry_run:
        return {
            "residents_to_process": len(residents_rows),
            "events_to_process": len(events_rows),
            "visits_to_process": len(visits_rows),
        }

    from sqlalchemy import select

    from app.core.database import AsyncSessionFactory
    from app.models.event import Event
    from app.models.resident import Resident, VisitRecord
    from app.services.utils import mask_id_number, mask_phone

    async with AsyncSessionFactory() as session:
        existing_residents = (
            await session.execute(select(Resident))
        ).scalars().all()
        resident_map = {(resident.name, resident.address): resident for resident in existing_residents}

        added_residents = 0
        for row in residents_rows:
            key = (row["name"], row["address"])
            if key in resident_map:
                continue
            resident = Resident(
                name=row["name"],
                id_number=mask_id_number(row["id_number"]),
                phone=mask_phone(row["phone"]),
                address=row["address"],
                tags=json.loads(row["tags_json"]),
                notes=row["notes"],
                created_at=parse_dt(row["created_at"]),
                updated_at=parse_dt(row["updated_at"]),
            )
            session.add(resident)
            resident_map[key] = resident
            added_residents += 1

        await session.commit()

        existing_events = (
            await session.execute(select(Event))
        ).scalars().all()
        existing_event_keys = {(event.title, event.address, event.created_at.isoformat()) for event in existing_events}

        added_events = 0
        for row in events_rows:
            created_at = parse_dt(row["created_at"])
            if created_at is None:
                continue
            event_key = (row["title"], row["address"], created_at.isoformat())
            if event_key in existing_event_keys:
                continue
            resident = resident_map.get((row["resident_name"], row["resident_address"])) if row["resident_name"] else None
            event = Event(
                title=row["title"],
                description=row["description"],
                category=row["category"],
                status=row["status"],
                priority=int(row["priority"]),
                address=row["address"],
                reporter_name=row["reporter_name"],
                resident_id=resident.id if resident else None,
                ai_suggestion=row["ai_suggestion"],
                attachments=json.loads(row["attachments_json"]),
                created_at=created_at,
                updated_at=parse_dt(row["updated_at"]),
                resolved_at=parse_dt(row["resolved_at"]),
            )
            session.add(event)
            existing_event_keys.add(event_key)
            added_events += 1

        await session.commit()

        existing_visits = (
            await session.execute(select(VisitRecord))
        ).scalars().all()
        existing_visit_keys = {(item.resident_id, item.visitor_name, item.created_at.isoformat()) for item in existing_visits}

        added_visits = 0
        updated_resident_counters = 0
        for row in visits_rows:
            resident = resident_map.get((row["resident_name"], row["resident_address"]))
            created_at = parse_dt(row["created_at"])
            if resident is None or created_at is None:
                continue
            visit_key = (resident.id, row["visitor_name"], created_at.isoformat())
            if visit_key in existing_visit_keys:
                continue
            visit = VisitRecord(
                resident_id=resident.id,
                visitor_name=row["visitor_name"],
                content=row["content"],
                summary=row["summary"],
                created_at=created_at,
            )
            session.add(visit)
            if resident.last_visit_at is None or created_at > resident.last_visit_at:
                resident.last_visit_at = created_at
            resident.visit_count = int(resident.visit_count or 0) + 1
            updated_resident_counters += 1
            existing_visit_keys.add(visit_key)
            added_visits += 1

        await session.commit()

    return {
        "residents_added": added_residents,
        "events_added": added_events,
        "visits_added": added_visits,
        "resident_visit_counters_updated": updated_resident_counters,
    }


async def main() -> None:
    args = parse_args()
    result = await seed(Path(args.data_dir), dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
