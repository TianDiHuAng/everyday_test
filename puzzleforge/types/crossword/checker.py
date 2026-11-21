"""中文填字唯一解校验：把格型各段视为 CSP 变量做解计数。

格型（layout）固定后，每个长度 ≥2 的横/竖连续白格段必须取词库中的一个
词；交叉格要求两词在共享位置字符相同。这恰好是一个二元 CSP（变量=段，
值=词），直接用 common.csp 计数解：解数 = 该格型在词库范围内的填充数，
恰为 1 才算唯一解。相比逐格枚举，槽位 CSP 借助前向检查剪枝，效率高得
多且数学上等价。
"""

import json
import os
from functools import lru_cache

from ...common import csp

_BANK_PATH = os.path.join(os.path.dirname(__file__), "data", "zh_wordbank.json")


@lru_cache(maxsize=1)
def load_bank():
    """加载并清洗词库：剔除含非汉字的词、线索泄漏词本身的条目。"""
    with open(_BANK_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    entries = []
    for e in data["words"]:
        w = e["word"]
        if any(not ("\u4e00" <= ch <= "\u9fff") for ch in w):
            continue
        if w in e["clue"]:
            continue
        entries.append({"word": w, "clue": e["clue"], "level": int(e.get("level", 2))})
    return tuple(entries)


@lru_cache(maxsize=1)
def bank_for_level(max_level):
    """{词长: [词, ...]}，按难度档过滤。"""
    m = {}
    for e in load_bank():
        if e["level"] > max_level:
            continue
        m.setdefault(len(e["word"]), []).append(e["word"])
    return m


@lru_cache(maxsize=1)
def clue_lookup():
    return {e["word"]: e["clue"] for e in load_bank()}


def extract_runs(layout):
    """返回 (横向段, 纵向段)，每段为有序坐标元组，长度 ≥2。"""
    size = len(layout)
    across, down = [], []
    for r in range(size):
        run = []
        for c in range(size + 1):
            if c < size and layout[r][c]:
                run.append((r, c))
            else:
                if len(run) >= 2:
                    across.append(tuple(run))
                run = []
    for c in range(size):
        run = []
        for r in range(size + 1):
            if r < size and layout[r][c]:
                run.append((r, c))
            else:
                if len(run) >= 2:
                    down.append(tuple(run))
                run = []
    return across, down


def _slot_csp(layout, words_by_len):
    """把格型编译为槽位 CSP：返回 (domains, binary)。无解时 domains 含空值域。"""
    across, down = extract_runs(layout)
    slots = {}
    for i, run in enumerate(across):
        slots[("A", i)] = run
    for i, run in enumerate(down):
        slots[("D", i)] = run
    cell_owner = {}
    for key, run in slots.items():
        for idx, cell in enumerate(run):
            cell_owner.setdefault(cell, []).append((key, idx))
    binary = []
    for owners in cell_owner.values():
        if len(owners) == 2:
            (ka, ia), (kb, ib) = owners
            binary.append((ka, kb, lambda a, b, _ia=ia, _ib=ib: a[_ia] == b[_ib]))
        # len>2 不会出现（一个格至多属一横一纵两段）；len=1 无交叉约束
    domains = {key: list(words_by_len.get(len(run), [])) for key, run in slots.items()}
    return domains, binary


def count_fills(layout, words_by_len, limit: int = 2) -> int:
    """统计格型在词库范围内的合法填充数，最多数到 limit。"""
    domains, binary = _slot_csp(layout, words_by_len)
    if any(not d for d in domains.values()):
        return 0
    return csp.count_solutions(domains, binary, limit=limit)


def unique_fill(layout, words_by_len):
    """唯一填充时返回 {cell: char}，否则 None。"""
    domains, binary = _slot_csp(layout, words_by_len)
    if any(not d for d in domains.values()):
        return None
    sol = csp.solve_unique(domains, binary)
    if sol is None:
        return None
    across, down = extract_runs(layout)
    letters = {}
    for key, run in zip([("A", i) for i in range(len(across))] + [("D", i) for i in range(len(down))],
                        list(across) + list(down)):
        w = sol[key]
        for idx, cell in enumerate(run):
            letters[cell] = w[idx]
    return letters
