"""算式谜题（cryptarithm）：字母代表数字的竖式加法。

候选算式来自精选词表，运行时用「列进位回溯」逐个验证：
- 解数恰为 1 的才算合格（唯一解由暴力枚举保证）；
- 不同字母必须对应不同数字，首位不为 0。

实现要点：列和必须包含「已在更前列赋值的字母」的贡献（如 MONEY 的 E
同时出现在 SEND 与 MONEY 的不同列）；每个赋值/撤销严格配对。
"""

from functools import lru_cache

# 候选算式（operands..., result），运行时验证唯一解后才可用
_CANDIDATES = [
    ("ANT", "BEE", "BUGS"),
    ("ONE", "TWO", "SIX"),
    ("BLUE", "RED", "GREEN"),
    ("SUN", "MOON", "STARS"),
    ("NIGHT", "DAY", "DREAM"),
    ("CAT", "DOG", "PETS"),
    ("SEND", "MORE", "MONEY"),
    ("CROSS", "ROADS", "DANGER"),
    ("HARD", "WORK", "PAYS"),
    ("FIFTY", "STATES", "AMERICA"),
    ("DONALD", "GERALD", "ROBERT"),
    ("WHO", "IS", "THIS"),
    ("MADE", "USA", "PRIDE"),
    ("COOL", "NEWS", "DAILY"),
]


def _word_value(word, digits):
    return int("".join(str(digits[ch]) for ch in word))


def _build_cols(operands, result):
    ncols = max(len(w) for w in operands)
    rlen = len(result)
    cols = []
    for i in range(ncols):
        col_letters = [w[len(w) - 1 - i] for w in operands if len(w) - 1 - i >= 0]
        res_ch = result[rlen - 1 - i] if rlen - 1 - i >= 0 else None
        cols.append((col_letters, res_ch))
    return cols


def count_solutions(operands, result, limit: int = 2) -> int:
    """列进位回溯计数。解 = 全部字母→数字的合法指派。"""
    firsts = {w[0] for w in operands} | {result[0]}
    ncols = max(len(w) for w in operands)
    rlen = len(result)
    if rlen < ncols or rlen > ncols + 1:
        return 0
    cols = _build_cols(operands, result)
    assignment = {}
    used = set()
    state = {"count": 0}

    def bt(ci, carry):
        if state["count"] >= limit:
            return
        if ci == ncols:
            if rlen == ncols:
                if carry == 0:
                    state["count"] += 1
            else:
                lead = result[0]
                if lead in assignment:
                    if assignment[lead] == carry and carry != 0:
                        state["count"] += 1
                elif carry != 0 and carry not in used:
                    state["count"] += 1
            return
        col_letters, res_ch = cols[ci]
        # 同列重复字母去重；列和按出现次数累加
        occ = {}
        need = []
        for ch in col_letters:
            if ch not in assignment:
                if ch not in occ:
                    need.append(ch)
                occ[ch] = occ.get(ch, 0) + 1
        # 已在前序列赋值的字母，其数字必须计入本列和
        base = sum(assignment[ch] for ch in col_letters if ch in assignment)

        def assign(k, ssum):
            if state["count"] >= limit:
                return
            if k == len(need):
                total = ssum + base + carry
                digit = total % 10
                new_carry = total // 10
                if res_ch is None:
                    bt(ci + 1, new_carry)
                    return
                if res_ch in assignment:
                    if assignment[res_ch] == digit:
                        bt(ci + 1, new_carry)
                    return
                if digit in used or (digit == 0 and res_ch in firsts):
                    return
                assignment[res_ch] = digit
                used.add(digit)
                bt(ci + 1, new_carry)
                del assignment[res_ch]
                used.discard(digit)
                return
            ch = need[k]
            mult = occ[ch]
            for d in range(10):
                if d in used:
                    continue
                if d == 0 and ch in firsts:
                    continue
                assignment[ch] = d
                used.add(d)
                assign(k + 1, ssum + d * mult)
                del assignment[ch]
                used.discard(d)

        assign(0, 0)

    bt(0, 0)
    return state["count"]


def solve(operands, result):
    """返回唯一解的 digits 映射；非唯一/无解返回 None。"""
    if count_solutions(operands, result, limit=2) != 1:
        return None
    return _search_one(tuple(operands), result)


def _search_one(operands, result):
    """列进位回溯取第一个解（已验证唯一时即唯一解）。"""
    firsts = {w[0] for w in operands} | {result[0]}
    ncols = max(len(w) for w in operands)
    rlen = len(result)
    cols = _build_cols(operands, result)
    assignment = {}
    used = set()

    def bt(ci, carry):
        if ci == ncols:
            if rlen == ncols:
                return carry == 0
            lead = result[0]
            if lead in assignment:
                return assignment[lead] == carry and carry != 0
            if carry != 0 and carry not in used:
                # 结果多出的最高位：进位即其数字，补进解映射
                assignment[lead] = carry
                return True
            return False
        col_letters, res_ch = cols[ci]
        occ = {}
        need = []
        for ch in col_letters:
            if ch not in assignment:
                if ch not in occ:
                    need.append(ch)
                occ[ch] = occ.get(ch, 0) + 1
        base = sum(assignment[ch] for ch in col_letters if ch in assignment)

        def assign(k, ssum):
            if k == len(need):
                total = ssum + base + carry
                digit = total % 10
                new_carry = total // 10
                if res_ch is None:
                    return bt(ci + 1, new_carry)
                if res_ch in assignment:
                    if assignment[res_ch] == digit:
                        return bt(ci + 1, new_carry)
                    return False
                if digit in used or (digit == 0 and res_ch in firsts):
                    return False
                assignment[res_ch] = digit
                used.add(digit)
                ok = bt(ci + 1, new_carry)
                if ok:
                    return True
                del assignment[res_ch]
                used.discard(digit)
                return False
            ch = need[k]
            mult = occ[ch]
            for d in range(10):
                if d in used:
                    continue
                if d == 0 and ch in firsts:
                    continue
                assignment[ch] = d
                used.add(d)
                ok = assign(k + 1, ssum + d * mult)
                if ok:
                    return True
                del assignment[ch]
                used.discard(d)
            return False

        return assign(0, 0)

    if bt(0, 0):
        return dict(assignment)
    return None


@lru_cache(maxsize=None)
def _qualified(difficulty_band):
    """返回该难度档内（运行时验证过唯一解的）精选候选算式列表。"""
    bands = {
        1: lambda n, maxlen: n <= 7 and maxlen <= 4,
        2: lambda n, maxlen: n <= 8 and maxlen <= 5,
        3: lambda n, maxlen: 7 <= n <= 9,
        4: lambda n, maxlen: 8 <= n <= 10,
        5: lambda n, maxlen: n >= 9,
    }
    check = bands[difficulty_band]
    out = []
    for cand in _CANDIDATES:
        operands, result = cand[:-1], cand[-1]
        letters = set("".join(cand))
        maxlen = max(len(w) for w in cand)
        if not check(len(letters), maxlen):
            continue
        if count_solutions(list(operands), result, limit=2) == 1:
            out.append(cand)
    return tuple(out)


# ── 程序化候选池：从词池随机组合 a+b=c，运行时验证唯一解 ──
# 候选数量近乎无限，是「每日新算式」的主要来源；精选经典算式作为点缀。

_WORD_POOL = [
    # 3 字母
    "CAT", "DOG", "SUN", "SKY", "CAR", "BUS", "MAP", "KEY", "BOX", "CUP",
    "PEN", "HAT", "EGG", "PIE", "JAM", "OWL", "FOX", "BEE", "ANT", "COW",
    "PIG", "HEN", "BAT", "RAT", "LOG", "ARM", "TOY", "BAG", "NET", "GEM",
    # 4 字母
    "STAR", "MOON", "WIND", "RAIN", "SNOW", "FIRE", "LAKE", "HILL", "CAVE",
    "WAVE", "SAND", "ROCK", "TREE", "LEAF", "BIRD", "FISH", "BEAR", "LION",
    "WOLF", "DEER", "DOVE", "SWAN", "DUCK", "FROG", "GOAT", "KING", "GOLD",
    "BLUE", "GREEN", "DARK", "LIME", "ROSE", "TULIP", "IRON", "WOOD", "DOOR",
    "BELL", "RING", "BOOK", "DESK", "LAMP", "SOFA", "MOSS", "PALM", "POND",
    # 5 字母
    "WATER", "TIGER", "MOUSE", "HORSE", "EAGLE", "SHARK", "WHALE", "CLOUD",
    "STORM", "TRAIN", "PLANE", "PHONE", "MUSIC", "PIANO", "SUGAR", "APPLE",
    "MANGO", "LEMON", "PEACH", "GRAPE", "BREAD", "HONEY", "OLIVE", "PANDA",
    "ZEBRA", "KOALA", "RIVER", "BEACH", "CANDY", "GHOST", "LIGHT", "NIGHT",
    # 6 字母
    "FOREST", "GARDEN", "BRIDGE", "CASTLE", "TURTLE", "MONKEY", "SILVER",
    "BUTTER", "FLOWER", "SPRING", "SUMMER", "PLANET", "ROCKET", "CANDLE",
]

# 难度档 → 允许的操作数长度组合与字母上限
_GEN_BANDS = {
    2: {"pairs": [(3, 3), (3, 4), (4, 4)], "letters": 9},
    3: {"pairs": [(3, 4), (3, 5), (4, 4), (4, 5)], "letters": 10},
    4: {"pairs": [(4, 4), (4, 5), (4, 6), (5, 5)], "letters": 10},
    5: {"pairs": [(4, 5), (4, 6), (5, 5), (5, 6)], "letters": 10},
}


@lru_cache(maxsize=1)
def _pool_by_len():
    m = {}
    for w in _WORD_POOL:
        m.setdefault(len(w), []).append(w)
    return m


def _generated_pool(rng, difficulty, limit=14, max_tries=3000):
    """随机组合词池生成候选算式，逐个暴力验证唯一解。

    这是算式谜题的「无限储量」来源：验证不过就换下一组，直到凑够
    limit 个或尝试耗尽。与精选经典算式合并使用。
    """
    band = _GEN_BANDS.get(difficulty)
    if band is None:
        return ()
    by_len = _pool_by_len()
    out, seen = [], set()
    for _ in range(max_tries):
        if len(out) >= limit:
            break
        la, lb = rng.choice(band["pairs"])
        len_a, len_b = by_len.get(la), by_len.get(lb)
        if not len_a or not len_b:
            continue
        wa = rng.choice(len_a)
        wb = rng.choice(len_b)
        result_len = max(la, lb) + rng.choice([0, 1])
        len_c = by_len.get(result_len)
        if not len_c:
            continue
        wc = rng.choice(len_c)
        if wc in (wa, wb):
            continue
        cand = (wa, wb, wc)
        if cand in seen:
            continue
        seen.add(cand)
        letters = set("".join(cand))
        if len(letters) > band["letters"]:
            continue
        operands, result = cand[:-1], cand[-1]
        if count_solutions(list(operands), result, limit=2) == 1:
            out.append(cand)
    return tuple(out)


def generate(rng, difficulty):
    pool = list(_qualified(difficulty)) + list(_generated_pool(rng, difficulty))
    if not pool:
        raise RuntimeError(f"算式谜题无难度 {difficulty} 的合格候选")
    cand = rng.choice(pool)
    operands, result = cand[:-1], cand[-1]
    digits = solve(list(operands), result)
    if digits is None:  # 理论上不会发生（已验证）
        raise RuntimeError("算式谜题解缺失")
    expr = " + ".join(operands) + " = " + result
    numbers = " + ".join(str(_word_value(w, digits)) for w in operands) + " = " + str(_word_value(result, digits))
    n_letters = len(set("".join(cand)))
    return {
        "puzzle": {
            "subtype": "cryptarithm",
            "equation": expr,
            "note": "不同字母代表不同数字，首位不为 0；求出每个字母对应的数字。",
        },
        "solution": {"digits": digits, "equation_numbers": numbers},
        "hints": [f"共 {n_letters} 个不同字母"],
        "difficulty_detail": f"{n_letters} 个字母的字母算式",
    }


def verify(puzzle, solution) -> bool:
    parts = puzzle["equation"].split("=")
    lhs = [w.strip() for w in parts[0].split("+")]
    rhs = parts[1].strip()
    digits = solution["digits"]
    if count_solutions(lhs, rhs, limit=2) != 1:
        return False
    ref = _search_one(tuple(lhs), rhs)
    if ref != digits:
        return False
    # 数字映射一致性
    all_words = lhs + [rhs]
    if sorted(set("".join(all_words))) != sorted(digits.keys()):
        return False
    if len(set(digits.values())) != len(digits):
        return False
    return sum(_word_value(w, digits) for w in lhs) == _word_value(rhs, digits)
