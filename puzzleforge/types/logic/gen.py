"""网格逻辑题生成：随机指派 → 派生候选线索 → 贪心收敛到唯一解 → 删减最小化。

难度配置决定规模（N 人 × M 属性）与可用线索类型；高难度禁用直接肯定
线索，逼迫链式推理。每条候选线索加入时都用求解器验证解数变化，最终
线索集满足：解数恰为 1（唯一解由构造保证）。
"""

import random

from . import solver

ENTITY_NAMES = ["小明", "小红", "小刚", "小丽", "小华"]

CATEGORY_POOL = [
    ("颜色", ["红色", "蓝色", "绿色", "黄色", "紫色"]),
    ("宠物", ["猫", "狗", "鸟", "鱼", "兔子"]),
    ("饮料", ["茶", "咖啡", "牛奶", "果汁", "汽水"]),
    ("运动", ["跑步", "游泳", "篮球", "羽毛球", "骑行"]),
    ("乐器", ["钢琴", "小提琴", "吉他", "笛子", "架子鼓"]),
    ("名次", ["第1名", "第2名", "第3名", "第4名", "第5名"]),
]

# n=实体数, cats=属性数, kinds=允许的线索类型
DIFFICULTY_CONFIG = {
    1: {"n": 3, "cats": 2, "kinds": ("pos", "neg", "link")},
    2: {"n": 4, "cats": 2, "kinds": ("pos", "neg", "link", "either")},
    3: {"n": 4, "cats": 3, "kinds": ("pos", "neg", "link", "either")},
    4: {"n": 5, "cats": 3, "kinds": ("pos", "neg", "link", "either")},
    5: {"n": 5, "cats": 3, "kinds": ("neg", "link", "either")},  # 无直接肯定线索
}

KIND_LABEL = {"pos": "直接肯定", "neg": "直接否定", "link": "关联推理", "either": "二选一"}


def _random_assignment(rng, n, cats):
    assign = {}
    for c in range(len(cats)):
        perm = list(range(n))
        rng.shuffle(perm)
        for e in range(n):
            assign[(e, c)] = perm[e]
    return assign


def _holders(assign, n, c):
    """属性 c 中 值下标 → 实体下标。"""
    return {assign[(e, c)]: e for e in range(n)}


def _candidate_clues(rng, n, cats, assign, kinds):
    """派生候选线索，按信息量分组排序：pos > link > either > neg。

    组内随机洗牌。pos 线索直接钉死单元格，保证加入阶段必然收敛。
    """
    groups = {"pos": [], "link": [], "either": [], "neg": []}
    nvals = [len(cat["values"]) for cat in cats]
    for e in range(n):
        for c in range(len(cats)):
            true_v = assign[(e, c)]
            if "pos" in kinds:
                groups["pos"].append({"kind": "pos", "e": e, "c": c, "v": true_v})
            if "neg" in kinds:
                for v in range(nvals[c]):
                    if v != true_v:
                        groups["neg"].append({"kind": "neg", "e": e, "c": c, "v": v})
            if "either" in kinds:
                for v in range(nvals[c]):
                    if v != true_v:
                        groups["either"].append({"kind": "either", "e": e, "c": c, "v1": true_v, "v2": v})
    for c1 in range(len(cats)):
        for c2 in range(len(cats)):
            if c1 == c2:
                continue
            h1 = _holders(assign, n, c1)
            h2 = _holders(assign, n, c2)
            for v1 in range(nvals[c1]):
                for v2 in range(nvals[c2]):
                    polarity = "pos" if h1[v1] == h2[v2] else "neg"
                    groups["link"].append(
                        {"kind": "link", "c1": c1, "v1": v1, "c2": c2, "v2": v2, "polarity": polarity}
                    )
    cands = []
    # 添加阶段：关联肯定 > 二选一 > 直接肯定 > 关联否定 > 直接否定
    # （强线索先收敛，弱线索兜底，pos 只在必要时登场）
    link_pos = [c for c in groups["link"] if c["polarity"] == "pos"]
    link_neg = [c for c in groups["link"] if c["polarity"] == "neg"]
    for group in (link_pos, groups["either"], groups["pos"], link_neg, groups["neg"]):
        rng.shuffle(group)
        cands.extend(group)
    return cands


def _select_clues(rng, n, cats, kinds, assign):
    """加入线索直到解数恰为 1（候选按信息量排序，收敛有保证）。

    注意不能用「解数下降才保留」的贪心：limit 截断后大解数区间无法
    比较大小；改为先加满到唯一，再由 _minimize 删冗余。
    """
    chosen = []
    for cand in _candidate_clues(rng, n, cats, assign, kinds):
        chosen.append(cand)
        if solver.count_solutions(n, cats, chosen, limit=2) == 1:
            return chosen
    return None


_REMOVAL_ORDER = {"pos": 0, "neg": 1, "either": 2, "link": 3}


def _minimize(rng, n, cats, chosen):
    """按线索对象逐个尝试删除（仍唯一才删），优先移除直白线索。

    注意必须按对象迭代而非索引——kept 在循环中收缩，索引会移位。
    """
    kept = list(chosen)
    clue_objs = list(kept)
    rng.shuffle(clue_objs)
    clue_objs.sort(key=lambda c: _REMOVAL_ORDER.get(c["kind"], 9))
    for clue in clue_objs:
        if not any(c is clue for c in kept):
            continue
        trial = [c for c in kept if c is not clue]
        if solver.count_solutions(n, cats, trial, limit=2) == 1:
            kept = trial
    return kept


def _clue_text(clue, entities, cats):
    if clue["kind"] == "pos":
        return f"{entities[clue['e']]}的{cats[clue['c']]['name']}是{cats[clue['c']]['values'][clue['v']]}。"
    if clue["kind"] == "neg":
        return f"{entities[clue['e']]}的{cats[clue['c']]['name']}不是{cats[clue['c']]['values'][clue['v']]}。"
    if clue["kind"] == "either":
        vals = cats[clue["c"]]["values"]
        return f"{entities[clue['e']]}的{cats[clue['c']]['name']}是{vals[clue['v1']]}或{vals[clue['v2']]}。"
    if clue["kind"] == "link":
        v1 = cats[clue["c1"]]["values"][clue["v1"]]
        v2 = cats[clue["c2"]]["values"][clue["v2"]]
        if clue["polarity"] == "pos":
            return f"{cats[clue['c1']]['name']}是{v1}的人，{cats[clue['c2']]['name']}是{v2}。"
        return f"{cats[clue['c1']]['name']}是{v1}的人，{cats[clue['c2']]['name']}不是{v2}。"
    raise ValueError(clue["kind"])


def generate(rng: random.Random, difficulty: int) -> dict:
    cfg = DIFFICULTY_CONFIG[difficulty]
    n, cats_n = cfg["n"], cfg["cats"]
    kinds = tuple(cfg["kinds"])
    entities = ENTITY_NAMES[:n]

    last_err = None
    for _attempt in range(8):
        cats = []
        for name, values in rng.sample(CATEGORY_POOL, cats_n):
            vals = list(values)
            rng.shuffle(vals)
            cats.append({"name": name, "values": vals[:n]})

        assign = _random_assignment(rng, n, cats)
        chosen = _select_clues(rng, n, cats, kinds, assign)
        if chosen is None and "pos" not in kinds:
            # 高难度兜底：链式线索凑不出唯一解时放回直接肯定
            kinds = kinds + ("pos",)
            chosen = _select_clues(rng, n, cats, kinds, assign)
        if chosen is None:
            last_err = "候选线索不足"
            continue
        kept = _minimize(rng, n, cats, chosen)
        if solver.count_solutions(n, cats, kept, limit=2) != 1:
            last_err = "最小化后失去唯一解"
            continue

        clues = []
        for i, clue in enumerate(kept):
            entry = {"id": i + 1, "kind": clue["kind"], "text": _clue_text(clue, entities, cats)}
            entry.update({k: v for k, v in clue.items() if k != "kind"})
            clues.append(entry)

        assignment = {}
        for e, name in enumerate(entities):
            assignment[name] = {cat["name"]: cat["values"][assign[(e, c)]] for c, cat in enumerate(cats)}

        labels = [KIND_LABEL[k] for k in dict.fromkeys(c["kind"] for c in kept)]
        return {
            "puzzle": {"n": n, "entities": entities, "categories": cats, "clues": clues},
            "solution": {"assignment": assignment},
            "hints": [],
            "difficulty_detail": f"{n} 人 × {cats_n} 属性；线索类型：{'、'.join(labels)}",
        }
    raise RuntimeError(f"逻辑题生成失败: {last_err}")


def verify(puzzle: dict, solution: dict) -> bool:
    n = puzzle["n"]
    sol = solver.solve(n, puzzle["categories"], puzzle["clues"])
    if sol is None:
        return False
    expected = {}
    for e, name in enumerate(puzzle["entities"]):
        expected[name] = {
            cat["name"]: cat["values"][sol[(e, c)]] for c, cat in enumerate(puzzle["categories"])
        }
    return solution["assignment"] == expected
