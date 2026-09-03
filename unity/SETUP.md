# SETUP.md — Unity 项目建立指南

> 一次性操作，约 30 分钟（不含下载时间）。做完后 AI 就能持续往工程里写代码。

## 1. 安装

1. 下载 **Unity Hub**：https://unity.com/download （国内可用 Unity 中国版 Hub）
2. Hub → Installs → Install Editor → 选 **2022.3 LTS**（任一 2022.3.x 均可）
   - 模块勾选：**Windows Build Support** 即可（不需要 Android/iOS/WebGL）
3. 需要 Unity 账号（个人免费版 Personal 即可）

## 2. 创建工程

1. Hub → Projects → New project
2. 模板选 **2D (Core)**（不要选 URP/HDRP，节奏游戏用不上，还会拖慢编译）
3. Project name: `BioRhythmGame`
4. Location: 本仓库的 `unity/` 目录（最终路径应为 `unity/BioRhythmGame/`）
5. Create project，等待首次导入完成

## 3. 必改设置（不做这步串口读不了！）

Edit → Project Settings → Player → Other Settings → Configuration：

- **Api Compatibility Level → `.NET Framework`**（默认是 .NET Standard 2.1，**没有 `System.IO.Ports`**，串口代码会直接编译报错——这是本项目第一大坑）

顺手确认：
- File → Build Settings → Platform 为 Windows（默认即是）
- Edit → Project Settings → Time → 保持默认（判定不依赖 Fixed Timestep）

## 4. 建立文件夹骨架

在 Project 窗口的 `Assets/` 下右键 Create → Folder，建出：

```
Assets/
├── Scenes/          # 00_Boot / 01_Calibration / 02_Gameplay / 03_Result（场景之后按步骤建）
├── Scripts/
│   ├── Data/
│   ├── Transport/
│   ├── Bio/
│   ├── Gameplay/
│   ├── Difficulty/
│   ├── Logging/
│   ├── UI/
│   └── Utils/
├── Charts/          # 谱面 JSON（tools/chartgen.py 的输出放这里）
├── Audio/           # 音乐文件（.ogg 或 .wav；mp3 也支持）
├── Config/          # ScriptableObject 配置
├── Prefabs/
└── Art/
```

> 各文件夹内容规划见 [../ARCHITECTURE.md](../ARCHITECTURE.md) §4.2。

## 5. Git 注意事项

- 仓库根 `.gitignore` 已配置忽略 `unity/*/Library/`、`Temp/` 等生成目录
- 另需开启文本序列化以便 diff（默认已是）：Edit → Project Settings → Editor → Asset Serialization → **Force Text**
- Unity 工程首次提交前确认 `Library/`（几个 GB）没被加进 git

## 6. 与 AI 协作的日常流程

```
AI 写/改 Assets/Scripts/ 下的 .cs 文件
        ↓
你切回 Unity 窗口（自动重新编译，左下角转圈）
        ↓
Console 有红色报错 → 原文复制给 AI
没报错 → 按 Play 测试 → 行为不对就描述现象（或截图）给 AI
        ↓
需要建场景/Prefab/拖引用时 → AI 给出精确步骤清单，你照做一次
```

**提示**：Console 报错要复制**完整一行**（含文件名和行号），AI 定位最快。

## 7. 无硬件开发模式

ESP32 不在手边时，用 `MockBioTransport`（P2 阶段实现）生成假生理数据，游戏逻辑照常开发测试——不要让硬件成为 Unity 进度的阻塞项。
