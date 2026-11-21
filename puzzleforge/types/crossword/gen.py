"""中文填字生成：罕见字交叉生长 + 槽位 CSP 唯一解校验。

策略要点（由词库字频分析得出）：
- 词库中绝大多数汉字只出现在 1-2 个词条里。交叉点落在「罕见字」上时，
  候选词瞬间收敛到 1-2 个，段被基本钉死——这是小词库也能做出唯一解
  填字的关键。
- 双交叉的 2 字词整词确定，优先采用。
- 生长目标只决定网格规模；最终必须通过 checker.count_fills（槽位 CSP，
  词库范围内恰有 1 种填充）才接受，不唯一就换随机路径重试。
"""

import random
from collections import Counter, defaultdict

from . import checker

DIFFICULTY_CONFIG = {
    1: {"size": 8, "target": 9},
    2: {"size": 8, "target": 10},
    3: {"size": 9, "target": 10},
    4: {"size": 9, "target": 11},
    5: {"size": 9, "target": 12},
}


def _build_index():
    bank = [e["word"] for e in checker.load_bank()]
    freq_pos = Counter((ch, i) for w in bank for i, ch in enumerate(w))
    char_pos = defaultdict(list)
    for w in bank:
        for i, ch in enumerate(w):
            char_pos[ch].append((w, i))
    return freq_pos, dict(char_pos)


_FREQ_POS, _CHAR_POS = _build_index()
_FULL_BY_LEN = checker.bank_for_level(3)


def _grow(rng, size, target, rare_max=3):
    """从种子词生长填字网格；返回 (letters, placed)。可能未达目标词数。"""
    letters = {}
    cell_dirs = {}
    placed = []
    seed = rng.choice([w for w in bank4() if len(w) == 4] or list(_CHAR_POS))
    r0 = size // 2
    for i, ch in enumerate(seed):
        cell = (r0, size // 2 - len(seed) // 2 + i)
        letters[cell] = ch
        cell_dirs[cell] = "A"
    placed.append(seed)

    guard = 0
    while guard < 500:
        guard += 1
        if len(placed) >= target:
            break
        anchors = list(letters.keys())
        rng.shuffle(anchors)
        cands = []
        for (ar, ac) in anchors:
            d = cell_dirs.get((ar, ac))
            direction = "D" if d == "A" else ("A" if d == "D" else None)
            if direction is None:
                continue
            ch = letters[(ar, ac)]
            for (w, i) in _CHAR_POS.get(ch, ()):
                if _FREQ_POS[(ch, i)] > rare_max or w in placed:
                    continue
                cells = _fit(rng, letters, cell_dirs, size, w, (ar, ac), i, direction)
                if cells is None:
                    continue
                crossings = sum(1 for c in cells if c in letters)
                score = 100 if (len(w) == 2 and crossings == 2) else (50 if crossings >= 2 else 0)
                score += 3 - _FREQ_POS[(ch, i)]
                cands.append((score, w, cells, direction))
        if not cands:
            break
        cands.sort(key=lambda t: -t[0])
        top = [c for c in cands if c[0] >= cands[0][0] - 2]
        _s, w, cells, direction = rng.choice(top)
        placed.append(w)
        for cell, ch in zip(cells, w):
            letters[cell] = ch
            cell_dirs[cell] = direction
    return letters, placed


def bank4():
    return [w for w in _FULL_BY_LEN.get(4, ())]


def _fit(rng, letters, cell_dirs, size, word, anchor, anchor_idx, direction):
    """尝试以 anchor 为交叉点放置 word（anchor 处字 = word[anchor_idx]）。"""
    L = len(word)
    ar, ac = anchor
    if direction == "D":
        r0 = ar - anchor_idx
        if not (0 <= r0 and r0 + L - 1 < size):
            return None
        if (r0 - 1 >= 0 and (r0 - 1, ac) in letters) or (r0 + L < size and (r0 + L, ac) in letters):
            return None
        cells = [(r0 + j, ac) for j in range(L)]
    else:
        c0 = ac - anchor_idx
        if not (0 <= c0 and c0 + L - 1 < size):
            return None
        if (c0 - 1 >= 0 and (ar, c0 - 1) in letters) or (c0 + L < size and (ar, c0 + L) in letters):
            return None
        cells = [(ar, c0 + j) for j in range(L)]
    for j, cell in enumerate(cells):
        if cell in letters:
            if letters[cell] != word[j] or cell_dirs[cell] == direction:
                return None
        else:
            rr, cc = cell
            if direction == "D":
                if (cc - 1 >= 0 and (rr, cc - 1) in letters) or (cc + 1 < size and (rr, cc + 1) in letters):
                    return None
            else:
                if (rr - 1 >= 0 and (rr - 1, cc) in letters) or (rr + 1 < size and (rr + 1, cc) in letters):
                    return None
    return tuple(cells)


def _payload(letters, size):
    layout = [[1 if (r, c) in letters else 0 for c in range(size)] for r in range(size)]
    across, down = checker.extract_runs(layout)
    starts = {run[0] for run in across} | {run[0] for run in down}
    numbers = {}
    nxt = 1
    for r in range(size):
        for c in range(size):
            if (r, c) in starts:
                numbers[(r, c)] = nxt
                nxt += 1
    lookup = checker.clue_lookup()
    grid = [[letters.get((r, c), "") for c in range(size)] for r in range(size)]
    clues = {"across": [], "down": []}
    answers = []
    for run in across:
        w = "".join(letters[c] for c in run)
        num = numbers[run[0]]
        clues["across"].append({"number": num, "row": run[0][0], "col": run[0][1], "text": lookup[w]})
        answers.append({"number": num, "dir": "across", "answer": w})
    for run in down:
        w = "".join(letters[c] for c in run)
        num = numbers[run[0]]
        clues["down"].append({"number": num, "row": run[0][0], "col": run[0][1], "text": lookup[w]})
        answers.append({"number": num, "dir": "down", "answer": w})
    idiom_ratio = sum(1 for a in answers if len(a["answer"]) == 4) / len(answers)
    return {
        "puzzle": {"size": size, "layout": layout, "clues": clues},
        "solution": {"grid": grid, "answers": answers},
        "hints": [],
        "difficulty_detail": f"{len(answers)} 词条、{size}×{size} 格；四字词占比 {idiom_ratio:.0%}",
    }


def generate(rng: random.Random, difficulty: int) -> dict:
    cfg = DIFFICULTY_CONFIG[difficulty]
    size, target = cfg["size"], cfg["target"]
    phases = ((1200, target - 3), (800, 6))  # 先按目标规模，再放宽词数兜底
    for tries, min_words in phases:
        for _ in range(tries):
            letters, placed = _grow(rng, size, target)
            if len(placed) < min_words:
                continue
            layout = [[1 if (r, c) in letters else 0 for c in range(size)] for r in range(size)]
            if checker.count_fills(layout, _FULL_BY_LEN, limit=2) == 1:
                return _payload(letters, size)
    raise RuntimeError("填字生成失败：未能构造出唯一解网格")


def verify(puzzle: dict, solution: dict) -> bool:
    layout = puzzle["layout"]
    if checker.count_fills(layout, _FULL_BY_LEN, limit=2) != 1:
        return False
    fill = checker.unique_fill(layout, _FULL_BY_LEN)
    if fill is None:
        return False
    grid = solution["grid"]
    size = len(layout)
    for r in range(size):
        for c in range(size):
            if layout[r][c]:
                if fill.get((r, c)) != grid[r][c]:
                    return False
            elif grid[r][c] != "":
                return False
    return True
