"""数独题型注册。"""

from .. import register
from ..base import PuzzleType
from . import gen


@register
class Sudoku(PuzzleType):
    name = "sudoku"
    display_name = "数独"
    difficulty_range = (1, 5)

    def generate(self, rng, difficulty):
        return gen.generate(rng, difficulty)

    def verify(self, puzzle, solution):
        return gen.verify(puzzle, solution)
