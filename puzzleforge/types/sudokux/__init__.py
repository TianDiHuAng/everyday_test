"""对角线数独题型：在标准数独规则上要求两条主对角线也各含 1-9。

复用数独的生成与求解核心（diagonals=True）；唯一解验证天然带对角约束。
技巧分级沿用标准数独分级器——对角线作为额外约束只会让解题更简单或
持平，分级仍具参考性。
"""

import random

from .. import register
from ..base import PuzzleType
from ..sudoku import gen as sudoku_gen


def generate(rng: random.Random, difficulty: int) -> dict:
    out = sudoku_gen.generate(rng, difficulty, diagonals=True)
    out["puzzle"]["note"] = "规则：每行、每列、每个 3×3 宫，以及两条主对角线都必须包含 1-9。"
    out["difficulty_detail"] = "对角线数独（额外要求两条主对角线为 1-9）：" + out["difficulty_detail"]
    return out


def verify(puzzle: dict, solution: dict) -> bool:
    return sudoku_gen.verify(puzzle, solution, diagonals=True)


@register
class SudokuX(PuzzleType):
    name = "sudokux"
    display_name = "对角线数独"
    difficulty_range = (1, 5)

    def generate(self, rng, difficulty):
        return generate(rng, difficulty)

    def verify(self, puzzle, solution):
        return verify(puzzle, solution)
