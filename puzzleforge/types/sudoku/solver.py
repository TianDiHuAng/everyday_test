"""数独求解核心：位运算回溯 + 解计数（唯一解验证底座）。

grid 统一用长度 81 的 list[int]，0 表示空格；JSON 载荷里用 9x9 二维数组。
"""

DIGITS = 0x1FF  # 9 个候选位

ROWS = [[r * 9 + c for c in range(9)] for r in range(9)]
COLS = [[r * 9 + c for r in range(9)] for c in range(9)]
BOXES = []
for _br in range(3):
    for _bc in range(3):
        BOXES.append([(_br * 3 + dr) * 9 + (bc * 3 + dc) for dr in range(3) for dc in range(3) for bc in [_bc]])
CELL_BOX = [0] * 81
for _bi, _cells in enumerate(BOXES):
    for _cell in _cells:
        CELL_BOX[_cell] = _bi

UNITS = ROWS + COLS + BOXES
PEERS = []
for _i in range(81):
    _s = set()
    for _u in (ROWS[_i // 9], COLS[_i % 9], BOXES[CELL_BOX[_i]]):
        _s.update(_u)
    _s.discard(_i)
    PEERS.append(sorted(_s))


def popcount(x: int) -> int:
    return bin(x).count("1")


def _init_masks(grid, diagonals=False):
    """返回 (rows, cols, boxes, diag0, diag1) 位掩码；givens 冲突时返回 None。

    diagonals=True 时两条主对角线（左上-右下、右上-左下）也要求 1-9 互斥，
    用于对角线数独变体。
    """
    rows, cols, boxes = [0] * 9, [0] * 9, [0] * 9
    diag0, diag1 = 0, 0
    for i, v in enumerate(grid):
        if v:
            bit = 1 << (v - 1)
            r, c, b = i // 9, i % 9, CELL_BOX[i]
            if (rows[r] | cols[c] | boxes[b]) & bit:
                return None
            if diagonals:
                if r == c and diag0 & bit:
                    return None
                if r + c == 8 and diag1 & bit:
                    return None
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit
            if diagonals:
                if r == c:
                    diag0 |= bit
                if r + c == 8:
                    diag1 |= bit
    return rows, cols, boxes, diag0, diag1


def _backtrack(grid, rows, cols, boxes, diag0, diag1, diagonals, empties, limit, collect, stop_at_limit=True):
    """MRV 回溯。返回 (解计数, 解样本列表)。"""
    count = 0
    solutions = []
    unfilled = list(empties)

    def backtrack():
        nonlocal count, diag0, diag1
        best_i, best_n, best_mask = -1, 10, 0
        idx = -1
        for k, i in enumerate(unfilled):
            r, c, b = i // 9, i % 9, CELL_BOX[i]
            dm = 0
            if diagonals:
                if r == c:
                    dm |= diag0
                if r + c == 8:
                    dm |= diag1
            mask = DIGITS & ~(rows[r] | cols[c] | boxes[b] | dm)
            n = popcount(mask)
            if n == 0:
                return False
            if n < best_n:
                best_i, best_n, best_mask, idx = i, n, mask, k
                if n == 1:
                    break
        if best_i == -1:
            count += 1
            if collect:
                solutions.append([v for v in current])
            return stop_at_limit and count >= limit

        i = unfilled.pop(idx)
        r, c, b = i // 9, i % 9, CELL_BOX[i]
        for d in range(9):
            bit = 1 << d
            if not (best_mask & bit):
                continue
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit
            if diagonals:
                if r == c:
                    diag0 |= bit
                if r + c == 8:
                    diag1 |= bit
            current[i] = d + 1
            if backtrack():
                if diagonals:
                    if r == c:
                        diag0 &= ~bit
                    if r + c == 8:
                        diag1 &= ~bit
                rows[r] &= ~bit
                cols[c] &= ~bit
                boxes[b] &= ~bit
                current[i] = 0
                unfilled.insert(idx, i)
                return True
            if diagonals:
                if r == c:
                    diag0 &= ~bit
                if r + c == 8:
                    diag1 &= ~bit
            rows[r] &= ~bit
            cols[c] &= ~bit
            boxes[b] &= ~bit
            current[i] = 0
        unfilled.insert(idx, i)
        return False

    # current 为工作棋盘（含 givens），回溯过程中逐步填空格
    current = list(grid)
    backtrack()
    return count, solutions


def count_solutions(grid, limit: int = 2, diagonals: bool = False) -> int:
    """统计解数量，数到 limit 即停。givens 冲突直接返回 0。"""
    masks = _init_masks(grid, diagonals)
    if masks is None:
        return 0
    empties = [i for i, v in enumerate(grid) if v == 0]
    if not empties:
        return 1
    rows, cols, boxes, diag0, diag1 = masks
    return _backtrack(grid, rows, cols, boxes, diag0, diag1, diagonals, empties, limit, 0)[0]


def solve(grid, diagonals: bool = False):
    """返回第一个解（长度 81 list），无解返回 None。"""
    masks = _init_masks(grid, diagonals)
    if masks is None:
        return None
    empties = [i for i, v in enumerate(grid) if v == 0]
    if not empties:
        return list(grid)
    rows, cols, boxes, diag0, diag1 = masks
    _, sols = _backtrack(grid, rows, cols, boxes, diag0, diag1, diagonals, empties, 1, 1)
    return sols[0] if sols else None
