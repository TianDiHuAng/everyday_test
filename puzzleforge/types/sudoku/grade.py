"""数独难度分级：模拟人类解题技巧逐级推进。

级别（grade = 全程所需最高技巧级别）:
  1  唯一候选数(naked single) / 隐性唯一(hidden single)
  2  显性/隐性数对
  3  三链数 + 区块排除(pointing/claiming)
  4  X-Wing
  5  以上技巧穷尽仍无法推进（需链式推理/猜测回溯）

实现要点：候选数盘跨迭代持久化——排除类技巧的删除效果必须保留，
否则同一技巧会反复触发造成死循环。矛盾视为超出技巧范围 → 5 级。
"""

import itertools

from .solver import BOXES, CELL_BOX, COLS, DIGITS, PEERS, ROWS, UNITS, popcount

LEVEL_NAMES = {
    1: "唯一候选数 / 隐性唯一",
    2: "显性/隐性数对",
    3: "三链数 / 区块排除",
    4: "X-Wing",
    5: "链式推理或回溯（超出技巧求解范围）",
}


class _Contradiction(Exception):
    pass


def _candidates(g):
    cand = {}
    for i in range(81):
        if g[i] == 0:
            used = 0
            for p in PEERS[i]:
                if g[p]:
                    used |= 1 << (g[p] - 1)
            m = DIGITS & ~used
            if m == 0:
                raise _Contradiction
            cand[i] = m
    return cand


def _eliminate_peer(cand, i, d):
    bit = 1 << (d - 1)
    for p in PEERS[i]:
        if p in cand:
            cand[p] &= ~bit
            if cand[p] == 0:
                raise _Contradiction


def _naked_single(g, cand):
    for i, m in cand.items():
        if popcount(m) == 1:
            d = m.bit_length()
            g[i] = d
            del cand[i]
            _eliminate_peer(cand, i, d)
            return True
    return False


def _hidden_single(g, cand):
    for unit in UNITS:
        placed = 0
        for i in unit:
            if g[i]:
                placed |= 1 << (g[i] - 1)
        for d in range(1, 10):
            bit = 1 << (d - 1)
            if placed & bit:
                continue
            spots = [i for i in unit if i in cand and cand[i] & bit]
            if len(spots) == 1:
                i = spots[0]
                g[i] = d
                del cand[i]
                _eliminate_peer(cand, i, d)
                return True
    return False


def _naked_subset(cand, n):
    for unit in UNITS:
        empties = [i for i in unit if i in cand]
        if len(empties) <= n:
            continue
        for combo in itertools.combinations(empties, n):
            union = 0
            for i in combo:
                union |= cand[i]
            if popcount(union) != n:
                continue
            changed = False
            for i in empties:
                if i in combo:
                    continue
                new = cand[i] & ~union
                if new != cand[i]:
                    if new == 0:
                        raise _Contradiction
                    cand[i] = new
                    changed = True
            if changed:
                return True
    return False


def _hidden_subset(g, cand, n):
    for unit in UNITS:
        placed = 0
        for i in unit:
            if g[i]:
                placed |= 1 << (g[i] - 1)
        avail = [d for d in range(1, 10) if not (placed >> (d - 1)) & 1]
        if len(avail) <= n:
            continue
        for combo in itertools.combinations(avail, n):
            keep = 0
            cells = set()
            ok = True
            for d in combo:
                bit = 1 << (d - 1)
                keep |= bit
                spots = [i for i in unit if i in cand and cand[i] & bit]
                if not spots:
                    ok = False
                    break
                cells.update(spots)
            if not ok or len(cells) != n:
                continue
            changed = False
            for i in cells:
                new = cand[i] & keep
                if new != cand[i]:
                    if new == 0:
                        raise _Contradiction
                    cand[i] = new
                    changed = True
            if changed:
                return True
    return False


def _digit_spots(cells, cand, d):
    bit = 1 << (d - 1)
    return [i for i in cells if i in cand and cand[i] & bit]


def _locked_pointing(cand):
    for box in BOXES:
        for d in range(1, 10):
            spots = _digit_spots(box, cand, d)
            if len(spots) < 2:
                continue
            rows_of = {i // 9 for i in spots}
            if len(rows_of) != 1:
                continue
            r = rows_of.pop()
            bit = 1 << (d - 1)
            changed = False
            for i in ROWS[r]:
                if i in box or i not in cand or not (cand[i] & bit):
                    continue
                cand[i] &= ~bit
                if cand[i] == 0:
                    raise _Contradiction
                changed = True
            if changed:
                return True
    return False


def _locked_claiming(cand):
    for r in range(9):
        for d in range(1, 10):
            spots = _digit_spots(ROWS[r], cand, d)
            if len(spots) < 2:
                continue
            boxes_of = {CELL_BOX[i] for i in spots}
            if len(boxes_of) != 1:
                continue
            box = BOXES[boxes_of.pop()]
            bit = 1 << (d - 1)
            changed = False
            for i in box:
                if i in ROWS[r] or i not in cand or not (cand[i] & bit):
                    continue
                cand[i] &= ~bit
                if cand[i] == 0:
                    raise _Contradiction
                changed = True
            if changed:
                return True
    return False


def _xwing(cand):
    for d in range(1, 10):
        bit = 1 << (d - 1)
        # 行基：两行中该数字候选位完全相同
        row_spots = {}
        for r in range(9):
            spots = sorted(i % 9 for i in _digit_spots(ROWS[r], cand, d))
            if len(spots) == 2:
                row_spots[r] = spots
        for r1, r2 in itertools.combinations(sorted(row_spots), 2):
            if row_spots[r1] != row_spots[r2]:
                continue
            changed = False
            for c in row_spots[r1]:
                for r in range(9):
                    if r in (r1, r2):
                        continue
                    i = r * 9 + c
                    if i in cand and cand[i] & bit:
                        cand[i] &= ~bit
                        if cand[i] == 0:
                            raise _Contradiction
                        changed = True
            if changed:
                return True
        # 列基
        col_spots = {}
        for c in range(9):
            spots = sorted(i // 9 for i in _digit_spots(COLS[c], cand, d))
            if len(spots) == 2:
                col_spots[c] = spots
        for c1, c2 in itertools.combinations(sorted(col_spots), 2):
            if col_spots[c1] != col_spots[c2]:
                continue
            changed = False
            for r in col_spots[c1]:
                for c in range(9):
                    if c in (c1, c2):
                        continue
                    i = r * 9 + c
                    if i in cand and cand[i] & bit:
                        cand[i] &= ~bit
                        if cand[i] == 0:
                            raise _Contradiction
                        changed = True
            if changed:
                return True
    return False


def grade_puzzle(grid) -> int:
    """返回 1..5 的难度级别。"""
    g = list(grid)
    try:
        cand = _candidates(g)
        level = 1
        while cand:
            if _naked_single(g, cand):
                continue
            if _hidden_single(g, cand):
                continue
            if _naked_subset(cand, 2) or _hidden_subset(g, cand, 2):
                level = max(level, 2)
                continue
            if (
                _naked_subset(cand, 3)
                or _hidden_subset(g, cand, 3)
                or _locked_pointing(cand)
                or _locked_claiming(cand)
            ):
                level = max(level, 3)
                continue
            if _xwing(cand):
                level = max(level, 4)
                continue
            return 5
        if any(v == 0 for v in g):
            return 5
        return level
    except _Contradiction:
        return 5
