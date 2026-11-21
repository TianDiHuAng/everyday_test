"""防重复机制测试：内容指纹 + 撞车重摇。"""

from puzzleforge.rng import make_rng
from puzzleforge.types import all_types


def test_create_returns_fingerprint():
    t = all_types()["crypto"]
    out = t.create(make_rng("2026-11-21", "crypto", 3), 3, ())
    assert out["fingerprint"]
    assert out["fingerprint"].startswith(("cry:", "sub:"))


def test_create_avoids_used_fingerprint():
    t = all_types()["crypto"]
    rng = make_rng("2026-11-21", "crypto", 2)
    first = t.create(rng, 2, ())
    second = t.create(rng, 2, {first["fingerprint"]})
    assert second["fingerprint"] != first["fingerprint"]
    assert t.verify(second["puzzle"], second["solution"])


def test_create_deterministic_with_same_avoid():
    t = all_types()["crypto"]
    avoid = frozenset({"cry: SEND + MORE = MONEY".strip()})
    a = t.create(make_rng("2026-11-21", "crypto", 4), 4, avoid)
    b = t.create(make_rng("2026-11-21", "crypto", 4), 4, avoid)
    assert a["fingerprint"] == b["fingerprint"]
    assert a["puzzle"] == b["puzzle"]


def test_default_fingerprint_hash_for_procedural_types():
    t = all_types()["sudoku"]
    out = t.create(make_rng("2026-11-21", "sudoku", 2), 2, ())
    assert out["fingerprint"].startswith("sudoku:")
