"""Tests for multi-format document loading."""

from __future__ import annotations

from app.ingest.loader import DocumentLoader


def test_txt_loader_returns_paragraph_blocks(tmp_path) -> None:
    """TXT files should be split into non-empty paragraph blocks."""

    path = tmp_path / "policy.txt"
    path.write_text("第一段政策内容。\n\n第二段办理材料。", encoding="utf-8")

    blocks = DocumentLoader().load(path)

    assert [block.text for block in blocks] == ["第一段政策内容。", "第二段办理材料。"]


def test_csv_loader_returns_structured_row_blocks(tmp_path) -> None:
    """CSV files should be converted into key-value textual blocks."""

    path = tmp_path / "tickets.csv"
    path.write_text("标题,类别\n楼道灯坏了,民生服务\n", encoding="utf-8-sig")

    blocks = DocumentLoader().load(path)

    assert len(blocks) == 1
    assert blocks[0].text == "标题: 楼道灯坏了；类别: 民生服务"
