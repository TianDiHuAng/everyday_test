"""网格逻辑题约束求解：把线索编译为二元 CSP，用公共求解器计数解。

变量 = (实体下标, 属性下标)，值 = 该属性的取值下标。
线索形态（全部可化为 一元/二元 约束）：
  pos     实体 e 的属性 c 是 v            → 一元
  neg     实体 e 的属性 c 不是 v          → 一元
  either  实体 e 的属性 c 是 v1 或 v2     → 一元
  link    「c1 是 v1」的人「c2 是/不是 v2」 → 对每个实体一条二元约束
"""

from ...common import csp


def _category_values(categories, c_idx):
    return categories[c_idx]["values"]


def build_constraints(n, categories, clues):
    """返回 (domains, binary) 供 common.csp 使用。"""
    variables = [(e, c) for e in range(n) for c in range(len(categories))]
    domains = {(e, c): list(range(len(categories[c]["values"]))) for (e, c) in variables}
    binary = []

    # 同一属性内互不相同（每属性是 1..n 的一个排列）
    for c in range(len(categories)):
        for e1 in range(n):
            for e2 in range(e1 + 1, n):
                binary.append(((e1, c), (e2, c), lambda a, b: a != b))

    for clue in clues:
        kind = clue["kind"]
        if kind == "pos":
            e, c, v = clue["e"], clue["c"], clue["v"]
            binary.append(((e, c), (e, c), lambda a, b, _v=v: a == _v))
        elif kind == "neg":
            e, c, v = clue["e"], clue["c"], clue["v"]
            binary.append(((e, c), (e, c), lambda a, b, _v=v: a != _v))
        elif kind == "either":
            e, c, v1, v2 = clue["e"], clue["c"], clue["v1"], clue["v2"]
            binary.append(((e, c), (e, c), lambda a, b, _a=v1, _b=v2: a in (_a, _b)))
        elif kind == "link":
            c1, v1, c2, v2, polarity = clue["c1"], clue["v1"], clue["c2"], clue["v2"], clue["polarity"]
            if c1 == c2:
                raise ValueError("link 线索两侧属性必须不同")
            for e in range(n):
                if polarity == "pos":
                    fn = lambda a, b, _v1=v1, _v2=v2: (a != _v1) or (b == _v2)
                else:
                    fn = lambda a, b, _v1=v1, _v2=v2: (a != _v1) or (b != _v2)
                binary.append(((e, c1), (e, c2), fn))
        else:
            raise ValueError(f"未知线索类型: {kind}")
    return domains, binary


def count_solutions(n, categories, clues, limit: int = 2) -> int:
    domains, binary = build_constraints(n, categories, clues)
    return csp.count_solutions(domains, binary, limit=limit)


def solve(n, categories, clues):
    """返回唯一解的指派 {(e, c): v}（无解/多解返回 None）。"""
    domains, binary = build_constraints(n, categories, clues)
    return csp.solve_unique(domains, binary)
