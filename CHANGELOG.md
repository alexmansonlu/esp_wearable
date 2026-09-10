# CHANGELOG

本项目版本记录。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/)。

## [0.0.5] - 2026-09-10 — 上机实测修正

### 修正
- `firmware/src/main.cpp`：`rmssd_p` / `rmssd_e` 在对应心率来源不新鲜（-1）时也输出 -1，不再残留旧值（实测见 `hr_e:-1` 却 `rmssd_e:437`）；已编译通过，需重新烧录
- `firmware/tools/sensor_check.py`：上机实测发现偶有缺字段的 bio 行（传输坏行但仍是合法 JSON），汇总时 KeyError 崩溃 → 缺字段的包跳过并计数提示；连接后用 DTR/RTS 主动复位一次以稳定收到 boot 行（`--no-reset` 可保留校准基线）；MPU6050 判定文案补充
- 三个工具（sensor_check / live_dashboard / serial_logger）改为从行内第一个 `{` 开始解析：ESP32 复位后 `Serial.begin` 常在 boot 行前吐一个乱码字节，原来 `startswith("{")` 会把 boot 行整行丢掉，表现为"按 EN 也未见 boot 行"；sensor_check 加 `--debug` 原样打印非 bio 行、识别 ROM 复位信息
- `firmware/tools/live_dashboard.py`：同样丢弃缺字段的包
- L1 §5.0 判定表、firmware/README 排查表补充坏包与 boot 行说明

### 变更
- `.gitignore`：`experiment/data_gathering/sessions/` 原始数据整体不入库（本地保留）；README 与 L1 交付说明同步

## [0.0.4] - 2026-09-10 — L1 改版（提案定案 + 采集分析闭环）与 experiment/ 目录

### 新增
- `experiment/`：数据采集与分析的固定结构（`README.md` 定义结构、流程、命名规范；三条规矩：data_gathering 只增不改 / analysis 只写 results / results 可删可重跑）
  - `data_gathering/record.py`：采一场 = 调 serial_logger 记录到 `sessions/` → 自动校准 → Ctrl+C → 终端问标签写入 `sessions.csv`（游戏 / 关卡难度 / BPM / 最终分数 / 明显失误 / 漏拍 / 主观紧张 / 备注）；空场自动清理
  - `analysis/common.py`：读取 / 路径 / 画图设置（跨平台中文字体、固定系列颜色）；`01_session_summary.py`：每场一行特征 + 三联总览图；`02_tag_correlation.py`：特征 × 标签 Spearman 相关（热图 + 最强 4 对散点，N<8 提示只当线索）
  - `analysis/prompts.md`：学生让 AI 分析用的提示词 P0–P5（读懂数据 → 单场看图 → 相关性 → 按规范写新脚本 → 质疑替代解释 → 出题自测）与报告格式
  - `results/{summary,plots,correlation,reports}/`；`sessions/*/raw.csv` 不入库
- 根目录 `requirements.txt`（pyserial / numpy / pandas / matplotlib，覆盖 firmware/tools 与 experiment/）；experiment/README.md 增加 Mac / Windows 建 `venv` 的完整命令；`venv/` 入 .gitignore
- 两个脚本已用 5 场合成数据端到端验证

### 变更
- `lessons/L1_硬件课.md` 改版为新时间表：0:00–0:20 游戏提案定案（G1–G5 空表现场填结论）+ Demo A–E 开发时程空表（现场填，L2 9/17、L3 9/19）→ 休息 → 0:30–0:40 vibe coding 自行探索（clone、T1/T2、首次 commit）→ 0:40–1:20 硬件走读 40 分钟，她开着 WIRING.md 当参照**自己接线**（固件教师预烧，PlatformIO 改作业）→ 1:20–1:30 sensor_check 自检每样接没接好 → 讲清 calibrate 做什么（30 秒基线、gsr_delta/hr_delta 公式、quality bit2、规矩与"偷偷心算"追问）→ live_dashboard → record.py 采一场 → 休息 → 1:40–2:00 收尾：下次课 Unity（课前装好）+ 作业（玩情绪起伏大的游戏采 ≥6 场 + rest 对照、打标签、让 AI 找相关性、写报告、git 交付）
- `CLAUDE.md`、`.claude/memory/teaching-plan.md`：登记 experiment/ 与新 L1 结构；`firmware/README.md` 指向 experiment/；`TODO.md` 分析目录路径改为 experiment/analysis

### 说明
- L2–L8 主题将按 L1 定下的开发时程改版 SCHEDULE.md（待 0.0.5）

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
