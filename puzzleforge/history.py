"""内容库历史指纹：让生成器感知已发布的内容，避免题库型题目短期内重复。"""

import glob
import json
import os


def load_fingerprints(out_dir: str) -> frozenset:
    """扫描内容库中所有条目的指纹。"""
    fps = set()
    for path in glob.glob(os.path.join(out_dir, "*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        for p in data.get("puzzles", []):
            fp = p.get("fingerprint")
            if fp:
                fps.add(fp)
    return frozenset(fps)
