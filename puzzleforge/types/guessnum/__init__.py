"""猜数字（1A2B）题型。

秘密 = L 位互不相同的数字串；线索是历次「xAyB」反馈（A=数字和位置都对，
B=数字对但位置不对）。唯一解通过对全部候选 P(10, L) 枚举计数恰为 1
保证——3 位 5040、5 位 30240 个候选，枚举成本可忽略。
"""

import random
from itertools import permutations

from .. import register
from ..base import PuzzleType

DIFFICULTY_CONFIG = {1: 3, 2: 4, 3: 4, 4: 5, 5: 5}

_NOTE = (
    "下面是对某个 {length} 位数字串（各位互不相同）的历次猜测反馈："
    "A = 数字和位置都对，B = 数字对但位置不对。推理出这个数字串。"
)


def _feedback(guess: str, secret: str):
    a = sum(1 for x, y in zip(guess, secret) if x == y)
    b = len(set(guess) & set(secret)) - a
    return a, b


def _candidates(length: int):
    return ["".join(p) for p in permutations("0123456789", length)]


def _consistent(candidate: str, clues) -> bool:
    return all(_feedback(c["guess"], candidate) == (c["a"], c["b"]) for c in clues)


def _count_solutions(candidates, clues, limit: int = 2) -> int:
    n = 0
    for c in candidates:
        if _consistent(c, clues):
            n += 1
            if n >= limit:
                return n
    return n


def _derive_clues(rng, candidates, secret, length):
    """随机猜候选并按反馈过滤，直到只剩秘密本身；再贪心删减线索。"""
    clues = []
    remaining = candidates
    while len(remaining) > 1:
        guess = rng.choice(remaining)
        a, b = _feedback(guess, secret)
        clues.append({"guess": guess, "a": a, "b": b})
        remaining = [c for c in remaining if _feedback(guess, c) == (a, b)]

    # 最小化：随机顺序尝试删除线索，仍唯一才删（按对象迭代避免索引移位）
    clue_objs = list(clues)
    rng.shuffle(clue_objs)
    for clue in clue_objs:
        trial = [c for c in clues if c is not clue]
        if _count_solutions(candidates, trial, limit=2) == 1:
            clues = trial
    return clues


def generate(rng: random.Random, difficulty: int) -> dict:
    length = DIFFICULTY_CONFIG[difficulty]
    secret = "".join(rng.sample("0123456789", length))
    candidates = _candidates(length)
    clues = _derive_clues(rng, candidates, secret, length)
    if _count_solutions(candidates, clues, limit=2) != 1:
        raise RuntimeError("猜数字生成失败：线索未收敛到唯一解")
    return {
        "puzzle": {
            "length": length,
            "clues": clues,
            "note": _NOTE.format(length=length),
        },
        "solution": {"secret": secret},
        "hints": [],
        "difficulty_detail": f"{length} 位不重复数字；已给出 {len(clues)} 条猜测反馈",
    }


def verify(puzzle: dict, solution: dict) -> bool:
    length = puzzle["length"]
    candidates = _candidates(length)
    sols = [c for c in candidates if _consistent(c, puzzle["clues"])]
    return len(sols) == 1 and sols[0] == solution["secret"]


@register
class GuessNum(PuzzleType):
    name = "guessnum"
    display_name = "猜数字"
    difficulty_range = (1, 5)

    def generate(self, rng, difficulty):
        return generate(rng, difficulty)

    def verify(self, puzzle, solution):
        return verify(puzzle, solution)
