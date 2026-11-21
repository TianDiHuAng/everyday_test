"""题型抽象契约：所有题型实现此基类并经 @register 注册。

新增题型清单：
1. 在 types/ 下新建子包（如 types/kenken/）；
2. 子包 __init__.py 里定义类继承 PuzzleType、实现 generate/verify，
   并用 @register 装饰；
3. 完成——注册表自动发现、CLI 自动生成、契约测试自动覆盖。

防重复：CLI 调 create(rng, difficulty, avoid) 而不是 generate——基类
负责「指纹撞车自动重摇」，子类只需实现 generate；对题库型内容（如
名言、算式），子类可覆写 fingerprint 给出语义身份（如名句本体），
程序化内容用默认的谜面哈希即可。
"""

from __future__ import annotations

import hashlib
import json
import random
from abc import ABC, abstractmethod


class PuzzleType(ABC):
    """题型契约。

    generate 返回 dict：
        puzzle: 给玩家看的谜面
        solution: 完整答案（唯一解）
        hints: 可选提示列表（可为空）
        difficulty_detail: 该难度下解题所需的技巧描述
    verify 用于对已生成内容独立复核（唯一解 + 答案一致）。
    """

    name: str = ""
    display_name: str = ""
    difficulty_range: tuple = (1, 5)

    @abstractmethod
    def generate(self, rng: random.Random, difficulty: int) -> dict:
        raise NotImplementedError

    @abstractmethod
    def verify(self, puzzle: dict, solution: dict) -> bool:
        """独立复核：解唯一且与存储答案一致。"""
        raise NotImplementedError

    def fingerprint(self, out: dict) -> str:
        """内容身份：默认谜面哈希；题库型子类覆写为语义身份。"""
        payload = json.dumps(out["puzzle"], sort_keys=True, ensure_ascii=False)
        return f"{self.name}:" + hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]

    def create(self, rng: random.Random, difficulty: int, avoid=()) -> dict:
        """生成 + 防重复包装：指纹命中已用集合时自动重摇。

        空间真正耗尽（全部撞车）时接受最后一次结果——由调用方的库存
        扩充（词库/名言/算式池）保证长期不耗尽。
        """
        out = None
        fp = ""
        for _ in range(60):
            out = self.generate(rng, difficulty)
            fp = self.fingerprint(out)
            if fp not in avoid:
                break
        out = dict(out)
        out["fingerprint"] = fp
        return out

    def describe(self, difficulty: int) -> str:
        return f"{self.display_name} · 难度 {difficulty}"
