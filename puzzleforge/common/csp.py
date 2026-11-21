"""通用二元约束求解器（跨题型复用）。

适用形态：变量 + 值域 + 二元约束（含一元退化）。带 MRV 变量序与前向
检查的回溯搜索，可计数解（limit 截断）或取首个解，是唯一解验证的公共
底座。网格逻辑题等题型直接使用；高性能题型（如数独）可用专化求解器，
但遵循同款语义。
"""

from __future__ import annotations


def _build_neighbors(domains: dict, binary):
    """返回 {变量: [(邻居变量, fn(该变量值, 邻居变量值) -> bool), ...]}。"""
    variables = list(domains.keys())
    neighbors = {v: [] for v in variables}
    for a, b, fn in binary or []:
        if a not in neighbors or b not in neighbors:
            raise KeyError(f"约束涉及未知变量: {a}/{b}")
        if a == b:
            neighbors[a].append((a, fn))
        else:
            neighbors[a].append((b, fn))
            neighbors[b].append((a, lambda x, y, _fn=fn: _fn(y, x)))
    return neighbors


def _search(domains: dict, binary, limit: int, collect: int):
    """回溯搜索。返回 (完整解计数, 最多 collect 个解样本)。"""
    neighbors = _build_neighbors(domains, binary)
    variables = list(domains.keys())
    work = {v: list(domains[v]) for v in variables}
    if any(not d for d in work.values()):
        return 0, []

    count = 0
    found = []

    def consistent(v, val, assignment):
        for u, fn in neighbors[v]:
            if u == v:
                # 一元约束（自环）：fn(val, val) 判自身合法性
                if not fn(val, val):
                    return False
            elif u in assignment and not fn(val, assignment[u]):
                return False
        return True

    def forward_check(v, val, assignment):
        pruned = []
        for u, fn in neighbors[v]:
            if u in assignment or u == v:
                continue
            keep = [x for x in work[u] if fn(val, x)]
            if len(keep) < len(work[u]):
                pruned.append((u, work[u]))
                work[u] = keep
                if not keep:
                    # 失败前先撤销已做的剪枝（逆序），避免污染后续分支
                    for uu, old in reversed(pruned):
                        work[uu] = old
                    return None
        return pruned

    def undo(pruned):
        # 逆序恢复：同一变量可能被多条约束先后剪枝，必须后剪的先还原
        for u, old in reversed(pruned):
            work[u] = old

    def backtrack(assignment):
        nonlocal count
        unassigned = [v for v in variables if v not in assignment]
        if not unassigned:
            count += 1
            if len(found) < collect:
                found.append(dict(assignment))
            return count >= limit
        v = min(unassigned, key=lambda k: len(work[k]))
        for val in work[v]:
            if not consistent(v, val, assignment):
                continue
            pruned = forward_check(v, val, assignment)
            if pruned is None:
                continue
            assignment[v] = val
            if backtrack(assignment):
                undo(pruned)
                del assignment[v]
                return True
            del assignment[v]
            undo(pruned)
        return False

    backtrack({})
    return count, found


def count_solutions(domains: dict, binary=None, limit: int = 2) -> int:
    """统计满足全部约束的解的数量，最多数到 limit 即停。"""
    return _search(domains, binary, limit, 0)[0]


def solve_one(domains: dict, binary=None):
    """返回一个满足约束的完整指派 {var: value}，无解返回 None。"""
    count, found = _search(domains, binary, 1, 1)
    return found[0] if count >= 1 else None


def solve_unique(domains: dict, binary=None):
    """恰有唯一解时返回该指派 {var: value}，否则返回 None。"""
    count, found = _search(domains, binary, 2, 1)
    return found[0] if count == 1 else None
