# PuzzleForge · 每日谜题生成器

程序化生成**数独、网格逻辑题、中文填字、密码谜题**四类每日谜题：每题**自动验证唯一解**、**按难度 1-5 分级**、按日期确定性生成内容库，并带一个可做题的「每日一题」网页。

两条架构第一原则：

1. **内容即接口**：生成器只产出规范 JSON（`content/日期.json`），网页/App/小程序直接消费同一内容库。
2. **题型插件化**：新增题型 = 在 `puzzleforge/types/` 下新建子包 + `@register` 装饰器，核心层零改动；契约测试自动覆盖新题型。

## 快速开始

```bash
# 生成今日内容（难度按日期轮换 1-5）
python -m puzzleforge generate --date 2026-11-21 --days 7

# 复核唯一解与答案一致性
python -m puzzleforge verify

# 本地预览网页（根目录启动，访问 http://localhost:8000/web/）
python -m http.server 8000
```

## CLI

| 命令 | 说明 |
| --- | --- |
| `python -m puzzleforge types` | 列出已注册题型 |
| `python -m puzzleforge generate --date YYYY-MM-DD [--days N] [--types sudoku,crypto] [--difficulty 3]` | 生成内容库 |
| `python -m puzzleforge verify` | 复核全部内容（唯一解 + 答案一致） |
| `python -m puzzleforge stats` | 内容库统计 |

## 各题型唯一解与难度机制

| 题型 | 生成方法 | 唯一解保证 | 难度分级 |
| --- | --- | --- | --- |
| 数独 | 随机满盘 → 控洞挖空 | 每挖一格用解计数器（搜到第 2 解即剪枝）验证 | 解题所需最高技巧：唯一候选(L1)→数对(L2)→三链数/区块(L3)→X-Wing(L4)→回溯(L5) |
| 逻辑推理 | 随机指派 → 派生线索 → 贪心收敛 | 每步用二元 CSP 解计数验证，恰 1 解才接受 | 规模（3×2→5×3）+ 线索类型（高难度禁用直接肯定线索） |
| 中文填字 | 罕见字交叉生长（小词库也能出唯一解的关键） | 槽位 CSP 全枚举：词库范围内恰有 1 种填充 | 词条数 + 网格规模 + 四字词占比 |
| 密码谜题 | 算式谜题（精选经典 + 词池程序化组合）/ 拼音替换密码 | 算式暴力枚举恰 1 解；替换由构造保证 | 字母规模 / 明码提示比例（40%→8%） |

## 新鲜度保障（防重复）

- **内容指纹**：每个条目带 `fingerprint`——程序化题型用谜面哈希，题库型内容（名句/算式）用语义身份（名句本体、算式本身）。
- **生成即避重**：`generate` 默认扫描已有内容库，指纹撞车自动重摇（`--allow-repeat` 可关闭）。实测 30 天 × 4 题型 120 题零重复。
- **储量设计**：算式谜题 = 精选经典 + 词池程序化组合（运行时逐个暴力验证唯一解），候选近乎无限；名言库 60+ 条持续扩充；数独/逻辑/填字为程序化空间，实际不耗尽。
- 空间真正耗尽时 `create()` 接受重复并继续运行——长期新鲜度靠扩充词库/名言/词池维持。

## 新增题型指南

1. 在 `puzzleforge/types/` 下新建子包，如 `types/kenken/`；
2. `__init__.py` 里定义类继承 `PuzzleType`，实现 `generate(rng, difficulty)`（内部必须完成唯一解验证）与 `verify(puzzle, solution)`，并用 `@register` 装饰；
3. 完成——CLI、内容库、契约测试（`tests/test_contract.py`）自动纳入；网页端先用通用卡片展示，随后可在 `web/js/` 注册专用渲染组件。

`puzzleforge/common/csp.py` 提供带前向检查的二元约束求解器（解计数 / 唯一解），可直接复用。

## 目录结构

```
puzzleforge/
├── rng.py            # 日期种子确定性 RNG（新增题型不扰动既有内容）
├── schema.py         # 统一 JSON 信封
├── cli.py            # generate / types / verify / stats
├── common/csp.py     # 二元约束求解器（跨题型复用）
└── types/            # 题型插件：sudoku / logic / crossword / crypto
tests/                # 契约测试（遍历注册表）+ 单元测试
content/              # 生成产出：content/YYYY-MM-DD.json
web/                  # 每日一题页面（纯静态，无构建步骤）
```

## 路线图

每日一读（`type: "reading"` 已预留）→ 模板推理小题 → 词库扩充 → App/小程序壳复用同一 JSON 库。
