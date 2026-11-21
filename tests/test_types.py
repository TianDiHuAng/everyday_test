"""各题型与公共组件单元测试。"""

from puzzleforge.common import csp
from puzzleforge.rng import make_rng
from puzzleforge.types import all_types
from puzzleforge.types.crossword import checker
from puzzleforge.types.crypto import cryptarithm, substitution
from puzzleforge.types.logic import gen as logic_gen
from puzzleforge.types.logic import solver as logic_solver
from puzzleforge.types.sudoku import grade as sudoku_grade
from puzzleforge.types.sudoku import solver as sudoku_solver


def _flatten(rows):
    return [v for row in rows for v in row]


# ── 公共 CSP ──


def test_csp_count_and_solve():
    domains = {"a": [0, 1], "b": [0, 1]}
    assert csp.count_solutions(domains, [], limit=99) == 4
    domains3 = {"a": [0, 1, 2], "b": [0, 1, 2], "c": [0, 1, 2]}
    assert csp.count_solutions(domains3, [], limit=50) == 27
    binary = [("a", "b", lambda x, y: x != y)]
    assert csp.count_solutions({"a": [0, 1], "b": [0, 1]}, binary, limit=9) == 2
    sol = csp.solve_one({"a": [0, 1], "b": [0, 1]}, binary)
    assert sol["a"] != sol["b"]
    # 一元约束（自环）
    binary_u = [("a", "a", lambda x, y: x == 1)]
    assert csp.count_solutions({"a": [0, 1]}, binary_u, limit=9) == 1


# ── 数独 ──


def test_sudoku_solver_counts():
    # 空盘多解（截断到 limit）
    assert sudoku_solver.count_solutions([0] * 81, limit=2) == 2
    # Wikipedia 经典例题，唯一解
    classic = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]
    flat = _flatten(classic)
    assert sudoku_solver.count_solutions(flat, limit=2) == 1
    solved = sudoku_solver.solve(flat)
    assert solved is not None and all(v != 0 for v in solved)


def test_sudoku_grade_bands():
    # 已解满盘 → 1 级（无需技巧）
    full = [1, 2, 3, 4, 5, 6, 7, 8, 9] * 9
    grid = []
    for r in range(9):
        grid.extend([((c + r * 3 + r // 3) % 9) + 1 for c in range(9)])
    assert sudoku_grade.grade_puzzle(grid) == 1
    # 数独生成器各难度可产出且分级不超过目标
    t = all_types()["sudoku"]
    for diff in (1, 5):
        out = t.generate(make_rng("2026-11-21", "sudoku", diff), diff)
        g = _flatten(out["puzzle"]["grid"])
        assert sudoku_grade.grade_puzzle(g) <= diff


# ── 逻辑题 ──


def test_logic_solver_detects_non_unique():
    # 无线索时解数远大于 1
    cats = [{"name": "颜色", "values": ["红", "蓝", "绿"]}, {"name": "宠物", "values": ["猫", "狗", "鸟"]}]
    assert logic_solver.count_solutions(3, cats, [], limit=2) == 2
    # 全部直接肯定线索 → 唯一
    rng = make_rng("t", "logic", 1)
    assign = logic_gen._random_assignment(rng, 3, cats)
    clues = [
        {"kind": "pos", "e": e, "c": c, "v": assign[(e, c)]}
        for e in range(3)
        for c in range(2)
    ]
    assert logic_solver.count_solutions(3, cats, clues, limit=2) == 1


# ── 填字 ──


def test_crossword_runs_and_fills():
    # 段提取
    layout = [
        [1, 1, 0],
        [0, 1, 0],
        [0, 1, 1],
    ]
    across, down = checker.extract_runs(layout)
    assert across == [((0, 0), (0, 1)), ((2, 1), (2, 2))]
    assert down == [((0, 1), (1, 1), (2, 1))]
    # 不可能格型（长度 5 的段，词库无 5 字词）→ 0 种填充
    assert checker.count_fills(
        [[1, 1, 1, 1, 1], [0] * 5, [0] * 5, [0] * 5, [0] * 5], checker.bank_for_level(3), limit=2
    ) == 0


# ── 密码谜题 ──


def test_cryptarithm_send_more_money():
    digits = cryptarithm.solve(["SEND", "MORE"], "MONEY")
    assert digits == {"D": 7, "E": 5, "N": 6, "R": 8, "O": 0, "S": 9, "M": 1, "Y": 2}
    assert cryptarithm.count_solutions(["SEND", "MORE"], "MONEY", limit=2) == 1


def test_substitution_roundtrip():
    t = all_types()["crypto"]
    out = t.generate(make_rng("2026-11-21", "crypto", 1), 1)
    mapping = out["solution"]["mapping"]
    decoded = "".join(mapping.get(ch, ch) for ch in out["puzzle"]["cipher"])
    assert decoded == out["solution"]["pinyin"]
    assert len(out["solution"]["pinyin"].split()) == len(out["solution"]["text"])


# ── 对角线数独 / 猜数字 ──


def test_sudokux_diagonal_constraint():
    t = all_types()["sudokux"]
    out = t.generate(make_rng("2026-11-21", "sudokux", 3), 3)
    sol = _flatten(out["solution"]["grid"])
    # 两条主对角线各自恰好是 1-9
    d0 = [sol[i * 9 + i] for i in range(9)]
    d1 = [sol[i * 9 + (8 - i)] for i in range(9)]
    assert sorted(d0) == list(range(1, 10))
    assert sorted(d1) == list(range(1, 10))
    assert t.verify(out["puzzle"], out["solution"])


def test_guessnum_feedback_and_uniqueness():
    from puzzleforge.types.guessnum import _candidates, _count_solutions, _feedback

    assert _feedback("1234", "1524") == (2, 1)
    # 空线索 → 多解
    assert _count_solutions(_candidates(3), [], limit=2) == 2
    t = all_types()["guessnum"]
    out = t.generate(make_rng("2026-11-21", "guessnum", 4), 4)
    assert t.verify(out["puzzle"], out["solution"])
    assert len(out["puzzle"]["clues"]) >= 1
