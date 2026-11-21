"""契约测试：遍历题型注册表，对每个已注册题型自动验收。

新题型一注册就自动被这里覆盖：唯一解、确定性、难度档完整、JSON 往返。
"""

import json

import pytest

from puzzleforge.rng import make_rng
from puzzleforge.schema import DailyContent, PuzzleEntry
from puzzleforge.types import all_types

CONTRACT_DATE = "2026-11-21"


@pytest.mark.parametrize("type_name", sorted(all_types()))
def test_contract_uniqueness_all_difficulties(type_name):
    """每个难度档生成的题都必须通过独立复核（解唯一且答案一致）。"""
    t = all_types()[type_name]
    lo, hi = t.difficulty_range
    for diff in range(lo, hi + 1):
        rng = make_rng(CONTRACT_DATE, type_name, diff)
        out = t.generate(rng, diff)
        assert set(out) >= {"puzzle", "solution", "hints", "difficulty_detail"}
        assert t.verify(out["puzzle"], out["solution"]), f"{type_name} 难度{diff} 唯一解/答案验证失败"


@pytest.mark.parametrize("type_name", sorted(all_types()))
def test_contract_determinism(type_name):
    """同 (日期, 题型, 难度) 两次生成必须完全一致（每日一题可复现）。"""
    t = all_types()[type_name]
    a = t.generate(make_rng(CONTRACT_DATE, type_name, 3), 3)
    b = t.generate(make_rng(CONTRACT_DATE, type_name, 3), 3)
    ka = json.dumps(a, sort_keys=True, ensure_ascii=False)
    kb = json.dumps(b, sort_keys=True, ensure_ascii=False)
    assert ka == kb


@pytest.mark.parametrize("type_name", sorted(all_types()))
def test_contract_schema_roundtrip(type_name):
    """PuzzleEntry/DailyContent JSON 序列化往返无损。"""
    t = all_types()[type_name]
    out = t.generate(make_rng(CONTRACT_DATE, type_name, 2), 2)
    entry = PuzzleEntry(
        type=type_name,
        display_name=t.display_name,
        difficulty=2,
        difficulty_detail=out["difficulty_detail"],
        puzzle=out["puzzle"],
        solution=out["solution"],
        hints=out["hints"],
    )
    content = DailyContent(date=CONTRACT_DATE, generator_version="test")
    content.add(entry)
    restored = DailyContent.from_json(content.to_json())
    assert restored.puzzles[0].to_dict() == entry.to_dict()
    assert t.verify(restored.puzzles[0].puzzle, restored.puzzles[0].solution)


def test_registry_has_expected_types():
    types = all_types()
    assert {"sudoku", "logic", "crossword", "crypto"} <= set(types)
