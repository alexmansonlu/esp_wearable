# unity/ — Unity 游戏端

> 本目录存放 Unity 相关的一切：项目建立指南、游戏设计文档、谱面生成工具。
> Unity 工程本体建立后位于 `unity/BioRhythmGame/`。

## 目录内容

| 文件/目录 | 内容 |
|---|---|
| [SETUP.md](SETUP.md) | **Unity 项目怎么建**（一次性操作，人做）+ 与 AI 协作写代码的流程 |
| [GAME_DESIGN.md](GAME_DESIGN.md) | 游戏设计文档——导论课与客户讨论用的材料 |
| [tools/](tools/) | 谱面工具：`chartgen.py` 音乐 → 节拍分析 → 谱面 JSON |
| `BioRhythmGame/` | Unity 工程（按 SETUP.md 建立后出现） |

## 分工说明：哪些事必须人在 Unity 里做

| 事项 | 谁做 | 说明 |
|---|---|---|
| 用 Unity Hub 创建工程、装编辑器 | **人** | 一次性，见 SETUP.md |
| 建场景、拖 Prefab、连 Inspector 引用 | **人**（按 AI 给的步骤清单） | AI 会给出精确到点击的操作步骤 |
| 写所有 C# 脚本 | **AI** | 直接写入 `Assets/Scripts/`，Unity 自动编译 |
| 谱面 JSON、配置文件 | **AI** | `tools/chartgen.py` 生成或手写 |
| 按 Play 测试、把报错/截图发回 | **人** | 报错原文贴给 AI 即可 |

> 换句话说：**不需要等 Unity 装好才开始**——设计文档、谱面工具、全部核心脚本都可以先写好，工程建立后一次性放入。
