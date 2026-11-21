"""统一 JSON 信封：内容库的最小契约，前端/App 按此解析。

信封固定字段 + 每题条目固定字段；puzzle/solution 的内部结构由各题型自定
义（App 可按 type 分发给对应渲染器）。type 字段预留 "reading" 位给将来的
每日一读。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


@dataclass
class PuzzleEntry:
    """单个谜题条目。"""

    type: str
    display_name: str
    difficulty: int
    difficulty_detail: str
    puzzle: dict
    solution: dict
    hints: list = field(default_factory=list)
    fingerprint: str = ""  # 内容指纹，用于跨天防重复

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "display_name": self.display_name,
            "difficulty": self.difficulty,
            "difficulty_detail": self.difficulty_detail,
            "puzzle": self.puzzle,
            "solution": self.solution,
            "hints": self.hints,
            "fingerprint": self.fingerprint,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PuzzleEntry":
        return cls(
            type=d["type"],
            display_name=d.get("display_name", d["type"]),
            difficulty=d["difficulty"],
            difficulty_detail=d.get("difficulty_detail", ""),
            puzzle=d["puzzle"],
            solution=d["solution"],
            hints=d.get("hints", []),
            fingerprint=d.get("fingerprint", ""),
        )


@dataclass
class DailyContent:
    """某一天的完整内容（可含多题型，未来也可含 reading 条目）。"""

    date: str
    generator_version: str
    puzzles: list = field(default_factory=list)

    def add(self, entry: PuzzleEntry) -> None:
        self.puzzles.append(entry)

    def to_json(self) -> str:
        return json.dumps(
            {
                "date": self.date,
                "generator_version": self.generator_version,
                "puzzles": [p.to_dict() for p in self.puzzles],
            },
            ensure_ascii=False,
            indent=2,
        )

    @classmethod
    def from_json(cls, raw: str) -> "DailyContent":
        d = json.loads(raw)
        return cls(
            date=d["date"],
            generator_version=d.get("generator_version", "?"),
            puzzles=[PuzzleEntry.from_dict(p) for p in d.get("puzzles", [])],
        )

    def save(self, out_dir: str) -> str:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"{self.date}.json")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(self.to_json() + "\n")
        return path

    @classmethod
    def load(cls, path: str) -> "DailyContent":
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_json(f.read())
