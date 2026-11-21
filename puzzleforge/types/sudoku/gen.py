"""数独生成：随机满盘 → 控洞挖空（每挖一格验证唯一解）→ 目标技巧分级。

挖洞策略：按随机顺序逐格尝试移除，只有当「解仍唯一且分级不超过目标」
时才接受。因此产出难度 ≤ 目标且尽量接近目标；连挖 3 个满盘取最接近者。
"""

import random

from . import grade as G
from . import solver as S

_MIN_CLUES = 22  # 安全下限，防止过度挖洞


def _to_2d(grid):
    return [grid[r * 9 : (r + 1) * 9] for r in range(9)]


def random_full_grid(rng: random.Random, diagonals: bool = False):
    """随机回溯填满 9x9；diagonals=True 时两条主对角线也必须是 1-9。"""
    g = [0] * 81
    rows, cols, boxes = [0] * 9, [0] * 9, [0] * 9
    diag0, diag1 = 0, 0

    def fill(i):
        nonlocal diag0, diag1
        if i == 81:
            return True
        r, c, b = i // 9, i % 9, S.CELL_BOX[i]
        dm = 0
        if diagonals:
            if r == c:
                dm |= diag0
            if r + c == 8:
                dm |= diag1
        mask = S.DIGITS & ~(rows[r] | cols[c] | boxes[b] | dm)
        digits = [d for d in range(1, 10) if (mask >> (d - 1)) & 1]
        rng.shuffle(digits)
        for d in digits:
            bit = 1 << (d - 1)
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit
            if diagonals:
                if r == c:
                    diag0 |= bit
                if r + c == 8:
                    diag1 |= bit
            g[i] = d
            if fill(i + 1):
                return True
            rows[r] &= ~bit
            cols[c] &= ~bit
            boxes[b] &= ~bit
            if diagonals:
                if r == c:
                    diag0 &= ~bit
                if r + c == 8:
                    diag1 &= ~bit
            g[i] = 0
        return False

    fill(0)
    return g


def _dig_once(solution, rng, target, passes: int = 6, diagonals: bool = False):
    """挖洞：接受「解唯一且分级 ≤ 目标」的移除。

    单条贪心轨迹容易一路滑进「纯 singles 可解」分支而跳过目标档，因此
    跑多条不同随机顺序的轨迹，跨轨迹记录「分级恰好等于目标的最深状态」，
    最终优先返回它；从未命中时退回分级最接近目标的状态。
    """
    best_exact, best_exact_clues = None, 82
    best_any, best_any_grade = None, -1
    for _ in range(passes):
        puzzle = list(solution)
        order = list(range(81))
        rng.shuffle(order)
        for cell in order:
            if sum(1 for v in puzzle if v) <= _MIN_CLUES:
                break
            trial = list(puzzle)
            trial[cell] = 0
            if S.count_solutions(trial, 2, diagonals=diagonals) != 1:
                continue
            g = G.grade_puzzle(trial)
            if g > target:
                continue
            puzzle = trial
            clues = sum(1 for v in puzzle if v)
            if g == target and clues < best_exact_clues:
                best_exact, best_exact_clues = list(trial), clues
            if g > best_any_grade:
                best_any, best_any_grade = list(trial), g
    return best_exact if best_exact is not None else best_any


def generate(rng: random.Random, difficulty: int, diagonals: bool = False) -> dict:
    best = None
    for _attempt in range(3):
        solution = random_full_grid(rng, diagonals)
        puzzle = _dig_once(solution, rng, difficulty, diagonals=diagonals)
        final = G.grade_puzzle(puzzle)
        if best is None or abs(final - difficulty) < abs(best[1] - difficulty):
            best = (puzzle, final, solution)
        if best[1] == difficulty:
            break
    puzzle, final_grade, solution = best
    clues = sum(1 for v in puzzle if v)
    return {
        "puzzle": {"grid": _to_2d(puzzle)},
        "solution": {"grid": _to_2d(solution)},
        "hints": [],
        "difficulty_detail": f"需掌握技巧：{G.LEVEL_NAMES.get(final_grade, '?')}；已知 {clues} 格",
    }


def verify(puzzle: dict, solution: dict, diagonals: bool = False) -> bool:
    g = [v for row in puzzle["grid"] for v in row]
    s = [v for row in solution["grid"] for v in row]
    if S.count_solutions(g, 2, diagonals=diagonals) != 1:
        return False
    solved = S.solve(g, diagonals=diagonals)
    return solved == s
