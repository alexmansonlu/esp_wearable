# CHANGELOG

本项目版本记录。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/)。

## [0.0.2] - 2026-09-03 — Unity 端与课程材料

### 新增
- `unity/` 目录
  - `SETUP.md`：Unity 工程建立指南（2022.3 LTS、.NET Framework 设置、与 AI 协作流程）
  - `GAME_DESIGN.md`：游戏设计文档（心流通道/MDA 理论、核心玩法定义、判定与计分、HUD 草图、🗣️ 待客户定案清单、范围控制）
  - `tools/chartgen.py`：音乐 → 节拍分析 → 谱面 JSON 生成器（librosa；tier 三级分档、频谱质心分轨、防同轨连打；已用合成 120 BPM 音轨端到端验证）
- `lessons/` 目录
  - `L0_导论课.md`：首课会议指南（五阶段项目框架 S1–S5、研究/构建双轨并行图、决策清单 D1–D5、60 分钟议程、决策记录表、应急问答）
  - `vibe_coding_入门.md`：学生手册（零编程基础适用：装机、提问基本功、git 基本功、代码答辩四步法、硬件学习提示词模板）
- 本 CHANGELOG

### 变更
- `CLAUDE.md` 与 `.claude/memory/`：登记 unity/、lessons/ 目录与教学模式
- `firmware/tools/*.py`：Windows 控制台 UTF-8 输出修正、图表中文字体修正

### 说明
- 教学模式定案：vibe coding + 每课后人工代码答辩，git commit 为作业交付单位

## [0.0.1] - 2026-09-03 — 架构文档与数据采集固件

### 新增
- `ARCHITECTURE.md` v0.4：六层系统架构、JSON schema、五状态判断规则、动态难度规则、开发排程、风险表
  - 硬件方案历经 v0.1→v0.4 迭代，定稿为 PulseSensor + AD8232 + Grove GSR + MPU6050 + 裸 MAX30100（选配）
- `HARDWARE.md` v1.2：全部元件的原理/接线/数值用途、统一心率融合策略（ECG > PPG > MAX30100）、接线总表、补购清单、上电自检清单
- `TODO.md`：P0–P6 开发任务清单（含 🔑 验收关卡与里程碑）
- `SCHEDULE.md` + 客户版排程（`课程排程_SCHEDULE.docx/.pdf`，简体中文）：22 小时授课日历（技术 18h + 心理学 4h）
- `firmware/` 数据采集固件 v0.2.0（PlatformIO / ESP32）
  - 200Hz 双路波形采样（PPG/ECG）+ `BeatDetector` 自适应阈值心跳检测 → 逐跳 IBI → BPM / RMSSD(HRV)
  - GSR 50Hz 过采样 + 15 秒斜率；MPU6050 运动门控；统一心率融合；30 秒基线校准
  - 10Hz NDJSON 特征流 + beat 事件 + 100Hz raw 波形流；串口指令（calibrate / raw on/off / ping）
  - 配套工具：`tools/serial_logger.py`（数据集记录器）、`tools/plot_session.py`（四联图 + 波形图）
- 项目记忆体系：`CLAUDE.md`（AI 助手自动加载的项目上下文）+ `.claude/memory/`（硬件决策历史、教学安排）
- `.gitignore`
