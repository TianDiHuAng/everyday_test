"""替换密码：名言警句转无声调拼音后做单表替换。

唯一解由构造保证（映射固定，解码唯一）；难度体现在明码提示字母的
比例上——提示越少越难。玩家需结合拼音规律与名句知识破译。
"""

import json
import os
import random
from functools import lru_cache

_QUOTES_PATH = os.path.join(os.path.dirname(__file__), "data", "quotes.json")

# 难度 → 明码提示比例（对密文中出现的不同字母）
HINT_RATIO = {1: 0.40, 2: 0.30, 3: 0.20, 4: 0.12, 5: 0.08}


@lru_cache(maxsize=1)
def load_quotes():
    with open(_QUOTES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return tuple(data["quotes"])


def _encode(pinyin, mapping):
    return "".join(mapping.get(ch, ch) for ch in pinyin)


def _make_mapping(rng):
    """无不动点的字母替换表。"""
    letters = [chr(ord("a") + i) for i in range(26)]
    while True:
        shuffled = letters[:]
        rng.shuffle(shuffled)
        mapping = dict(zip(letters, shuffled))
        if all(mapping[k] != k for k in letters):
            return mapping


def generate(rng: random.Random, difficulty: int) -> dict:
    quotes = load_quotes()
    quote = rng.choice(list(quotes))
    pinyin = quote["pinyin"]
    enc = _make_mapping(rng)  # 明文 → 密文
    cipher = _encode(pinyin, enc)
    decode_map = {v: k for k, v in enc.items()}  # 密文 → 明文（对玩家暴露的方向）

    cipher_letters = sorted(set(ch for ch in cipher if ch.isalpha()))
    n_hint = max(2, round(len(cipher_letters) * HINT_RATIO[difficulty]))
    hint_letters = rng.sample(cipher_letters, min(n_hint, len(cipher_letters)))
    hints = {ch: decode_map[ch] for ch in hint_letters}

    detail = f"拼音单表替换密码；已给出 {len(hints)}/{len(cipher_letters)} 个明码"
    if difficulty <= 2:
        detail += f"；出处提示：{quote['source']}"

    return {
        "puzzle": {
            "subtype": "substitution",
            "cipher": cipher,
            "hints": hints,
            "note": "下面是某句名言的无声调拼音（单表替换加密，空格保持不变）。破译它。",
        },
        "solution": {
            "mapping": {k: decode_map[k] for k in sorted(decode_map)},
            "pinyin": pinyin,
            "text": quote["text"],
            "source": quote["source"],
        },
        "hints": [f"{k} → {v}" for k, v in sorted(hints.items())],
        "difficulty_detail": detail,
    }


def verify(puzzle, solution) -> bool:
    mapping = solution["mapping"]
    # 双射性
    values = list(mapping.values())
    if len(set(values)) != len(values):
        return False
    if set(mapping.keys()) != set(chr(ord("a") + i) for i in range(26)):
        return False
    # 提示与映射一致
    for k, v in puzzle["hints"].items():
        if mapping.get(k) != v:
            return False
    # 解码还原（mapping 为 密文→明文）
    decoded = "".join(mapping.get(ch, ch) for ch in puzzle["cipher"])
    if decoded != solution["pinyin"]:
        return False
    # 拼音与原文对应（按音节数）
    if len(solution["pinyin"].split()) != len(solution["text"]):
        return False
    return True
