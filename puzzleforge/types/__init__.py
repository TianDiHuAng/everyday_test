"""题型注册表 + 自动发现。

import puzzleforge.types 后调用 load_all() 即扫描 types/ 下全部子包并导入，
各子包在导入时经 @register 自注册。新增题型无需改动本文件。
"""

from __future__ import annotations

import importlib
import pkgutil

from .base import PuzzleType

REGISTRY: dict = {}


def register(cls):
    """类装饰器：实例化并注册题型。"""
    inst = cls()
    if not inst.name:
        raise ValueError(f"{cls.__name__} 未设置 name")
    if inst.name in REGISTRY:
        raise ValueError(f"题型 {inst.name} 重复注册")
    REGISTRY[inst.name] = inst
    return cls


_loaded = False


def load_all() -> None:
    """自动扫描 types/ 下所有子模块，触发注册。"""
    global _loaded
    if _loaded:
        return
    pkg = importlib.import_module(__name__)
    for mod in pkgutil.iter_modules(pkg.__path__):
        if mod.name in ("base",):
            continue
        importlib.import_module(f"{__name__}.{mod.name}")
    _loaded = True


def get_type(name: str) -> PuzzleType:
    load_all()
    if name not in REGISTRY:
        raise KeyError(f"未知题型: {name}（已注册: {sorted(REGISTRY)}）")
    return REGISTRY[name]


def all_types() -> dict:
    load_all()
    return dict(REGISTRY)
