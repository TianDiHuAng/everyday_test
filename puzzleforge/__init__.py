"""PuzzleForge — 每日谜题生成器。

架构原则：
1. 内容即接口：生成器产出规范 JSON，前端/App 直接消费。
2. 题型插件化：新增题型 = 在 types/ 下新建子包 + @register，核心层零改动。
"""

GENERATOR_VERSION = "0.1.0"
