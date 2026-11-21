"""日期种子的确定性随机数。

每个 (日期, 题型, 难度) 组合独立派生 RNG——新增题型不会扰动既有题目的
随机流，保证内容库在题型扩充后仍可稳定复现。
"""

from __future__ import annotations

import hashlib
import random

from . import GENERATOR_VERSION


def make_rng(date_str: str, type_name: str, difficulty: int, version: str = GENERATOR_VERSION) -> random.Random:
    """由日期+题型+难度派生确定性 RNG。"""
    material = f"puzzleforge|{version}|{date_str}|{type_name}|{difficulty}"
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], "big")
    return random.Random(seed)


def default_daily_difficulty(date_str: str) -> int:
    """每日默认难度：自 epoch 天数轮换 1..5，保证一周内难度有起伏。"""
    import datetime

    d = datetime.date.fromisoformat(date_str)
    return (d.toordinal() % 5) + 1
