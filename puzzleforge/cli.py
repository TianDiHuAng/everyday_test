"""命令行入口：generate / types / verify / stats。

示例：
    python -m puzzleforge types
    python -m puzzleforge generate --date 2026-11-21 --days 7
    python -m puzzleforge generate --date 2026-11-21 --types sudoku,crypto --difficulty 3
    python -m puzzleforge verify --out content
    python -m puzzleforge stats --out content
"""

import argparse
import datetime
import sys

from . import GENERATOR_VERSION
from .history import load_fingerprints
from .rng import default_daily_difficulty, make_rng
from .schema import DailyContent, PuzzleEntry
from .types import all_types


def cmd_generate(args) -> int:
    types = all_types()
    if args.types:
        fixed = [t.strip() for t in args.types.split(",")]
        for name in fixed:
            if name not in types:
                print(f"未知题型: {name}（已注册: {sorted(types)}），先看 `puzzleforge types`")
                return 1
    # 内容感知防重复：扫描已有内容库指纹，生成时自动避开
    avoid = frozenset() if args.allow_repeat else load_fingerprints(args.out)
    start = datetime.date.fromisoformat(args.date)
    for i in range(args.days):
        d = start + datetime.timedelta(days=i)
        date_str = d.isoformat()
        difficulty = args.difficulty or default_daily_difficulty(date_str)
        # 每日题型：指定 --types 用固定列表，否则按日期种子随机抽取
        if args.types:
            selected = args.types.split(",") if "," in args.types else [args.types.strip()]
            selected = [t.strip() for t in selected]
        else:
            pick_rng = make_rng(date_str, "__pick__", 0)
            pool = sorted(types)
            selected = pick_rng.sample(pool, min(max(1, args.count), len(pool)))
        content = DailyContent(date=date_str, generator_version=GENERATOR_VERSION)
        for name in selected:
            t = types[name]
            lo, hi = t.difficulty_range
            diff = max(lo, min(hi, difficulty))
            rng = make_rng(date_str, name, diff)
            out = t.create(rng, diff, avoid)
            avoid = avoid | {out["fingerprint"]}  # 本次批量内也不重复
            content.add(
                PuzzleEntry(
                    type=name,
                    display_name=t.display_name,
                    difficulty=diff,
                    difficulty_detail=out["difficulty_detail"],
                    puzzle=out["puzzle"],
                    solution=out["solution"],
                    hints=out["hints"],
                    fingerprint=out["fingerprint"],
                )
            )
        path = content.save(args.out)
        print(f"{date_str} 难度{difficulty}: {'、'.join(selected)} → {path}")
    return 0


def cmd_types(_args) -> int:
    types = all_types()
    print(f"已注册 {len(types)} 个题型（新增题型会自动出现在这里）：")
    for name in sorted(types):
        t = types[name]
        lo, hi = t.difficulty_range
        print(f"  {name:<12} {t.display_name}  难度 {lo}-{hi}")
    return 0


def cmd_verify(args) -> int:
    import glob

    paths = sorted(glob.glob(f"{args.out}/*.json"))
    if not paths:
        print(f"{args.out}/ 下没有内容文件")
        return 1
    types = all_types()
    bad = 0
    total = 0
    for path in paths:
        content = DailyContent.load(path)
        total += len(content.puzzles)
        for entry in content.puzzles:
            t = types.get(entry.type)
            if t is None:
                print(f"{path}: 未知题型 {entry.type}")
                bad += 1
                continue
            if not t.verify(entry.puzzle, entry.solution):
                print(f"{path}: {entry.type} 验证失败（唯一解破坏或答案不一致）")
                bad += 1
    print(f"验证完成：{total} 题，{bad} 题失败")
    return 1 if bad else 0


def cmd_stats(args) -> int:
    import glob
    from collections import Counter

    paths = sorted(glob.glob(f"{args.out}/*.json"))
    if not paths:
        print(f"{args.out}/ 下没有内容文件")
        return 1
    by_type = Counter()
    by_diff = Counter()
    for path in paths:
        content = DailyContent.load(path)
        for entry in content.puzzles:
            by_type[entry.type] += 1
            by_diff[(entry.type, entry.difficulty)] += 1
    print(f"内容库：{len(paths)} 天，共 {sum(by_type.values())} 题")
    for name in sorted(by_type):
        hist = " ".join(f"D{d}:{by_diff[(name, d)]}" for d in range(1, 6) if by_diff[(name, d)])
        print(f"  {name:<12} {by_type[name]:>3} 题  [{hist}]")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="puzzleforge", description=f"每日谜题生成器 v{GENERATOR_VERSION}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_gen = sub.add_parser("generate", help="按日期生成每日内容")
    p_gen.add_argument("--date", required=True, help="起始日期 YYYY-MM-DD")
    p_gen.add_argument("--days", type=int, default=1, help="连续生成天数")
    p_gen.add_argument("--types", help="逗号分隔的题型列表（固定用这些题型）")
    p_gen.add_argument("--count", type=int, default=4, help="每日随机抽取的题型数量，默认 4")
    p_gen.add_argument("--difficulty", type=int, choices=[1, 2, 3, 4, 5], help="固定难度（默认按日期轮换 1-5）")
    p_gen.add_argument("--out", default="content", help="内容输出目录")
    p_gen.add_argument("--allow-repeat", action="store_true", help="允许与已有内容重复（默认自动避开）")
    p_gen.set_defaults(func=cmd_generate)

    p_types = sub.add_parser("types", help="列出已注册题型")
    p_types.set_defaults(func=cmd_types)

    p_verify = sub.add_parser("verify", help="复核内容库（唯一解 + 答案一致）")
    p_verify.add_argument("--out", default="content")
    p_verify.set_defaults(func=cmd_verify)

    p_stats = sub.add_parser("stats", help="内容库统计")
    p_stats.add_argument("--out", default="content")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
