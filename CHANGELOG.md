# CHANGELOG

本项目版本记录。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/)。

## [0.0.3] - 2026-09-10 — 硬件实物核对、上机工具与 L1 课程材料

### 新增
- `WIRING.md` v1.0：面包板接线与首次上机指南（按厂商资料逐一核对）——micro-USB ESP32 兼容性结论、各模块实物引脚、9 步上机检查（每步有通过标准）、固件核对与编译结论
- `docs/datasheets/`：厂商资料本地副本（芯路城 ESP32-WROOM-32 CH340 版、思知瑞 GSR / PulseSensor / AD8232、ADI AD8232 datasheet）；大压缩包与安装程序不入库（见 `.gitignore`）
- `docs/pdf/`：HARDWARE.md、WIRING.md 的 PDF 版（发学生用）
- `firmware/tools/sensor_check.py`：15 秒上机自检，逐个传感器给出 ✅/❌ 判定（对应 WIRING.md §5）
- `firmware/tools/live_dashboard.py`：实时仪表盘（三路波形 + 心率/HRV/GSR/运动趋势；快捷键 c 校准 / r raw / q 退出；`--snapshot` 无窗口存图）
- `lessons/L1_硬件课.md`：L1 线下课主持脚本（环境安装 → vibe coding 测试 → 六样硬件逐件走读并逐行对应固件源码 → 烧录自检 → 提案反馈 → 作业与评分表）
- `lessons/S2-S5_决策清单.md`：S2–S5 全部待定决策（教师内部 + Nick 对齐用，不直接发学生）
- `AGENTS.md`：给 Codex 等 AI 编程助手的入口说明，指向 CLAUDE.md

### 变更
- `HARDWARE.md` v1.2 → v1.3：皮肤电模块确认为**思知瑞 3 针 GSR 模块**（`GND/VCC/ADC`，无电位器，非 Grove）；ESP32 实物为 micro-USB（CH340）版；新增 0.1 节厂商资料链接与本地副本；AD8232 补充线色与 SDN 上拉说明；面包板/杜邦线标记已购
- `ARCHITECTURE.md`、`firmware/README.md`、`firmware/include/config.h`、`firmware/src/main.cpp` 注释：Grove GSR → 思知瑞 GSR；README 补充 sensor_check / live_dashboard 用法与 macOS 串口名
- `lessons/L0_导论课.md`：改为完整主持脚本——五阶段框架与双轨图、60 分钟议程、D1–D5 决策清单、§5 游戏设计开放问题 G1–G5（只讨论不定案）、AI 助手开箱演示、作业改为纯 AI 助手作业（不写代码不碰 git）
- `lessons/vibe_coding_入门.md`：装机改为 L1 前完成；AI 编程助手定为 **OpenAI Codex VSCode 扩展**（学生用 ChatGPT 账号）；硬件学习模板改为上传 PDF；新增游戏设计提案作业
- `CLAUDE.md`、`.claude/memory/`：登记 WIRING.md、L1/S2-S5 材料、学生用 Codex（教师用 Claude Code）、游戏设计方法论

### 说明
- 固件代码本身无功能变更（仍为 v0.2.0），仅注释；上机验证待 9/11 L1 线下课完成

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
  - 硬件方案历经 v0.1→v0.4 迭代，定稿为 PulseSensor + AD8232 + 思知瑞 GSR + MPU6050 + 裸 MAX30100（选配）
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
