"""密码谜题题型注册：算式谜题 + 替换密码两个子型。"""

import random

from .. import register
from ..base import PuzzleType
from . import cryptarithm, substitution

# 各难度可用的子型
_SUBTYPES = {
    1: ("substitution",),
    2: ("substitution", "cryptarithm"),
    3: ("cryptarithm", "substitution"),
    4: ("cryptarithm",),
    5: ("cryptarithm", "substitution"),
}


@register
class Crypto(PuzzleType):
    name = "crypto"
    display_name = "密码谜题"
    difficulty_range = (1, 5)

    def fingerprint(self, out):
        """语义身份：名句本体 / 算式本身（与密文随机映射无关）。"""
        p = out["puzzle"]
        if p.get("subtype") == "cryptarithm":
            return "cry:" + p["equation"]
        return "sub:" + out["solution"]["pinyin"]

    def generate(self, rng, difficulty):
        subtype = rng.choice(_SUBTYPES[difficulty])
        try:
            if subtype == "cryptarithm":
                out = cryptarithm.generate(rng, difficulty)
            else:
                out = substitution.generate(rng, difficulty)
        except RuntimeError:
            # 该难度的算式池为空时回退到替换密码
            subtype = "substitution"
            out = substitution.generate(rng, difficulty)
        out["puzzle"]["subtype"] = subtype
        return out

    def verify(self, puzzle, solution):
        if puzzle.get("subtype") == "cryptarithm":
            return cryptarithm.verify(puzzle, solution)
        return substitution.verify(puzzle, solution)
