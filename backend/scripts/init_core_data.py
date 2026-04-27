from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import delete, func, select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# 允许脚本在未安装 backend 包时直接从 backend/scripts 目录运行。
from app.core.database import AsyncSessionFactory  # noqa: E402
from app.core.security import mask_id_number, mask_phone  # noqa: E402
from app.models.event import Event  # noqa: E402
from app.models.resident import Resident, VisitRecord  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize core GridRAG data into the local database.")
    parser.add_argument("--residents", type=int, default=100, help="Number of residents to generate")
    parser.add_argument("--events", type=int, default=5, help="Number of events to generate")
    parser.add_argument("--visits", type=int, default=0, help="Number of visit records to generate")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing residents, events, and visit records before inserting new data",
    )
    return parser.parse_args()


def build_names(count: int) -> list[str]:
    surnames = ["王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴", "徐", "孙", "胡", "朱", "高", "林"]
    given_names = [
        "佳宁", "梓涵", "宇辰", "若彤", "晨曦", "思远", "雨桐", "书瑶", "嘉豪", "雅琴",
        "文昊", "怡然", "志强", "雪梅", "博文", "欣妍", "安琪", "明轩", "子瑜", "秋实",
        "玉兰", "海涛", "乐怡", "晓彤", "志鹏", "慧敏", "承泽", "雨菲", "凯文", "静怡",
        "俊杰", "春梅", "沐阳", "紫萱", "志宏", "月华", "嘉怡", "国强", "新月", "浩然",
        "思齐", "柳青", "小雨", "雪琴", "云峰", "锦程", "珊珊", "启明", "泽宇", "丹宁",
        "雨晨", "若琳", "依婷", "可心", "一鸣", "亦菲", "梦瑶", "天佑", "海燕", "文静",
    ]
    names: list[str] = []
    for surname in surnames:
        for given_name in given_names:
            names.append(f"{surname}{given_name}")
            if len(names) >= count:
                return names
    raise ValueError("Not enough generated names")


def build_resident_rows(count: int) -> list[dict[str, object]]:
    communities = [
        ("和宁社区", "惠民苑"),
        ("景和社区", "朝阳新村"),
        ("安泰社区", "福宁里"),
        ("德馨社区", "锦绣园"),
        ("柳岸社区", "安和里"),
        ("瑞和社区", "汇景苑"),
    ]
    tag_cycle = [
        ["ELDERLY_ALONE"],
        ["LOW_INCOME"],
        ["DISABLED"],
        ["CHRONIC_DISEASE"],
        ["LEFT_BEHIND_CHILD"],
        ["ELDERLY_ALONE", "CHRONIC_DISEASE"],
        ["LOW_INCOME", "DISABLED"],
        [],
        [],
        [],
    ]
    notes_by_tag = {
        "ELDERLY_ALONE": "子女常年在外，需关注用药、燃气和防跌倒风险。",
        "LOW_INCOME": "家庭收入波动较大，关注救助政策衔接和就业变化。",
        "DISABLED": "行动不便，办理事项和上门服务应尽量一次办结。",
        "CHRONIC_DISEASE": "长期服药，需提醒按时复诊并关注极端天气影响。",
        "LEFT_BEHIND_CHILD": "主要监护人为祖辈，需关注学习和情绪变化。",
    }

    names = build_names(count)
    created_anchor = datetime(2026, 1, 5, 9, 0, 0)
    rows: list[dict[str, object]] = []

    for index, name in enumerate(names, start=1):
        community_name, compound_name = communities[(index - 1) % len(communities)]
        building = (index % 12) + 1
        unit = (index % 4) + 1
        room = 101 + (index * 3) % 602
        tags = tag_cycle[(index - 1) % len(tag_cycle)]
        birth_year = 1952 + (index * 3) % 49
        if "LEFT_BEHIND_CHILD" in tags:
            birth_year = 2011 + index % 5
        birth_date = datetime(birth_year, ((index * 5) % 12) + 1, ((index * 7) % 27) + 1)
        address = f"{community_name}{compound_name}{building}号楼{unit}单元{room}室"
        note_parts = [notes_by_tag[tag] for tag in tags if tag in notes_by_tag] or ["常住居民，近期无异常风险。"]
        created_at = created_anchor + timedelta(hours=index * 6)
        rows.append(
            {
                "name": name,
                "id_number": f"310112{birth_date:%Y%m%d}{index:03d}{index % 10}",
                "phone": f"13{(500000000 + index * 27113) % 1000000000:09d}",
                "address": address,
                "tags": tags,
                "notes": " ".join(note_parts),
                "created_at": created_at,
                "updated_at": created_at + timedelta(days=(index % 9) + 1),
            }
        )
    return rows


def build_event_rows(residents: list[dict[str, object]], count: int) -> list[dict[str, object]]:
    templates = [
        {
            "title": "夜间广场舞扰民投诉",
            "description": "居民反映 {location} 20:30 后音响音量偏大，影响老人休息和学生作业，要求协调降噪。",
            "category": "COMPLAINT",
            "priority": 3,
            "status": "IN_PROGRESS",
            "ai_suggestion": "先行口头劝导并明确活动结束时间，必要时联合物业和社区民警晚间巡查。",
        },
        {
            "title": "楼道堆物阻塞消防通道",
            "description": "巡查发现 {location} 楼道堆放纸箱、旧家具和婴儿车，存在通行与消防隐患。",
            "category": "HAZARD",
            "priority": 4,
            "status": "PENDING",
            "ai_suggestion": "联合物业张贴清理通知，限时整改并安排次日复查。",
        },
        {
            "title": "电梯噪声引发邻里纠纷",
            "description": "{location} 相邻住户因夜间电梯启停噪声问题发生争执，希望社区出面协调。",
            "category": "DISPUTE",
            "priority": 3,
            "status": "RESOLVED",
            "ai_suggestion": "安排物业现场检测电梯运行噪声，组织双方住户面对面说明并形成书面意见。",
        },
        {
            "title": "独居老人上门回访",
            "description": "对 {location} 重点关注老人开展入户回访，核查用药、供餐、照明和紧急联系人信息。",
            "category": "VISIT",
            "priority": 2,
            "status": "CLOSED",
            "ai_suggestion": "完善走访记录，补充风险提示，并约定下次回访时间。",
        },
        {
            "title": "异地就医备案办理咨询",
            "description": "居民在 {location} 咨询异地就医备案所需材料和办理流程，希望一次性告知。",
            "category": "OTHER",
            "priority": 1,
            "status": "RESOLVED",
            "ai_suggestion": "按医保政策清单一次性说明材料要求，并同步告知线上办理渠道。",
        },
    ]
    reporters = ["张颖", "周晨", "李娜", "何雪", "王磊"]
    # Spread seeded events across the recent rolling window so the dashboard trend is populated.
    dashboard_window_days = 24
    created_anchor = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    denominator = max(count - 1, 1)
    focus_residents = [resident for resident in residents if resident["tags"]] or residents
    rows: list[dict[str, object]] = []

    for index in range(count):
        template = templates[index % len(templates)]
        resident = (
            focus_residents[index % len(focus_residents)]
            if template["category"] in {"COMPLAINT", "DISPUTE", "VISIT"}
            else None
        )
        address = str(resident["address"]) if resident else f"和宁社区公共区域{index + 1}号点位"
        days_back = 2 + round((count - 1 - index) * dashboard_window_days / denominator)
        created_at = created_anchor - timedelta(days=days_back) + timedelta(hours=index % 5)
        resolved_at = None
        if template["status"] in {"RESOLVED", "CLOSED"}:
            resolved_at = created_at + timedelta(hours=12 + index * 2)
        rows.append(
            {
                "title": template["title"],
                "description": template["description"].format(location=address),
                "category": template["category"],
                "status": template["status"],
                "priority": template["priority"],
                "address": address,
                "reporter_name": reporters[index % len(reporters)],
                "resident_name": resident["name"] if resident else "",
                "resident_address": resident["address"] if resident else "",
                "ai_suggestion": template["ai_suggestion"],
                "created_at": created_at,
                "updated_at": resolved_at + timedelta(hours=2) if resolved_at else created_at + timedelta(hours=6),
                "resolved_at": resolved_at,
            }
        )
    return rows


def build_visit_rows(residents: list[dict[str, object]], count: int) -> list[dict[str, object]]:
    visitors = ["张颖", "周晨", "李娜", "何雪", "王磊", "赵媛", "胡静", "马超"]
    templates = {
        "ELDERLY_ALONE": (
            "入户核查老人近期用药、早餐供应和紧急联系人联系方式，提醒不要在厨房长时间离火，并查看照明和防滑设施是否完好。",
            "已确认独居老人生活平稳，需继续关注防跌倒和燃气安全。",
        ),
        "LOW_INCOME": (
            "了解本月家庭收入和医疗支出，说明临时救助与低保复核的材料准备要求，提醒保存票据和收入证明。",
            "已完成政策提醒，建议补齐收入证明和票据材料。",
        ),
        "DISABLED": (
            "核对无障碍改造需求和辅助器具使用情况，确认是否需要上门代办和康复服务衔接。",
            "当前生活秩序稳定，建议继续跟踪出行便利性。",
        ),
        "CHRONIC_DISEASE": (
            "询问慢病复诊与购药情况，提醒近期气温变化较大，注意提前备药并按时复诊。",
            "健康风险整体可控，需保持复诊和用药提醒。",
        ),
        "LEFT_BEHIND_CHILD": (
            "与监护人沟通作息、上学接送和情绪变化，提醒周末可参加社区关爱活动并加强家校沟通。",
            "儿童状态平稳，建议学校和社区继续保持联系。",
        ),
    }
    focus_residents = [resident for resident in residents if resident["tags"]] or residents
    created_anchor = datetime(2026, 4, 6, 9, 30, 0)
    rows: list[dict[str, object]] = []

    for index in range(count):
        resident = focus_residents[index % len(focus_residents)]
        tags = list(resident["tags"])
        main_tag = tags[index % len(tags)] if tags else "ELDERLY_ALONE"
        content, summary = templates.get(main_tag, templates["ELDERLY_ALONE"])
        created_at = created_anchor + timedelta(days=index, hours=index % 4)
        rows.append(
            {
                "resident_name": resident["name"],
                "resident_address": resident["address"],
                "visitor_name": visitors[index % len(visitors)],
                "content": content,
                "summary": summary,
                "created_at": created_at,
            }
        )
    return rows


async def counts() -> dict[str, int]:
    async with AsyncSessionFactory() as session:
        resident_count = int((await session.execute(select(func.count()).select_from(Resident))).scalar_one())
        event_count = int((await session.execute(select(func.count()).select_from(Event))).scalar_one())
        visit_count = int((await session.execute(select(func.count()).select_from(VisitRecord))).scalar_one())
    return {"residents": resident_count, "events": event_count, "visits": visit_count}


async def reset_existing_data() -> None:
    async with AsyncSessionFactory() as session:
        await session.execute(delete(VisitRecord))
        await session.execute(delete(Event))
        await session.execute(delete(Resident))
        await session.commit()


async def insert_data(resident_total: int, event_total: int, visit_total: int) -> dict[str, int]:
    resident_rows_data = build_resident_rows(resident_total) if resident_total > 0 else []
    event_rows_data = build_event_rows(resident_rows_data, event_total) if event_total > 0 else []

    async with AsyncSessionFactory() as session:
        resident_rows: list[Resident] = []
        resident_map: dict[tuple[str, str], Resident] = {}

        for row in resident_rows_data:
            resident = Resident(
                name=str(row["name"]),
                id_number=mask_id_number(str(row["id_number"])),
                phone=mask_phone(str(row["phone"])),
                address=str(row["address"]),
                tags=list(row["tags"]),
                notes=str(row["notes"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            resident_rows.append(resident)
            resident_map[(resident.name, resident.address)] = resident

        session.add_all(resident_rows)
        if resident_rows:
            await session.flush()

        if not resident_rows:
            existing_residents = (await session.execute(select(Resident).order_by(Resident.created_at))).scalars().all()
            resident_map.update({(resident.name, resident.address): resident for resident in existing_residents})

        event_rows: list[Event] = []
        for row in event_rows_data:
            resident = None
            if row["resident_name"]:
                resident = resident_map.get((str(row["resident_name"]), str(row["resident_address"])))
            event_rows.append(
                Event(
                    title=str(row["title"]),
                    description=str(row["description"]),
                    category=str(row["category"]),
                    status=str(row["status"]),
                    priority=int(row["priority"]),
                    address=str(row["address"]),
                    reporter_name=str(row["reporter_name"]),
                    resident_id=resident.id if resident else None,
                    ai_suggestion=str(row["ai_suggestion"]),
                    attachments=[],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    resolved_at=row["resolved_at"],
                )
            )

        if event_rows:
            session.add_all(event_rows)

        visit_rows_data = (
            build_visit_rows(
                [
                    {
                        "name": resident.name,
                        "address": resident.address,
                        "tags": list(resident.tags or []),
                    }
                    for resident in resident_map.values()
                ],
                visit_total,
            )
            if visit_total > 0
            else []
        )

        visit_rows: list[VisitRecord] = []
        for row in visit_rows_data:
            resident = resident_map.get((str(row["resident_name"]), str(row["resident_address"])))
            if resident is None:
                continue
            created_at = row["created_at"]
            visit_rows.append(
                VisitRecord(
                    resident_id=resident.id,
                    visitor_name=str(row["visitor_name"]),
                    content=str(row["content"]),
                    summary=str(row["summary"]),
                    created_at=created_at,
                )
            )
            resident.visit_count = int(resident.visit_count or 0) + 1
            if resident.last_visit_at is None or created_at > resident.last_visit_at:
                resident.last_visit_at = created_at

        if visit_rows:
            session.add_all(visit_rows)
        await session.commit()

    return {
        "residents_inserted": len(resident_rows),
        "events_inserted": len(event_rows),
        "visits_inserted": len(visit_rows),
    }


async def main() -> None:
    args = parse_args()
    before = await counts()
    if args.reset:
        await reset_existing_data()
    inserted = await insert_data(args.residents, args.events, args.visits)
    after = await counts()
    print(json.dumps({"before": before, "inserted": inserted, "after": after}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
