# CLAUDE.md — 项目上下文（AI 助手必读）

> 本文件是给 Claude（或其他 AI 助手）的项目记忆，换电脑后从这里恢复全部上下文。
> 详细决策历史与教学安排见 [.claude/memory/](.claude/memory/) 下的文件。

## 项目是什么

**生理信号自适应音乐节奏游戏**（教学项目，授课对象为一名学生客户）：
ESP32 读取玩家心率/HRV + 皮肤电（GSR），实时传给 Unity 4 轨节奏游戏，按玩家生理状态（calm / focused / nervous / frustrated / overloaded）动态调整音符速度/密度/复杂度，Python 做赛后分析。总授课 22 小时（技术 18h + 心理学教师 Nick 4h）。

## 核心文档地图（按此顺序读）

| 文件 | 内容 |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 六层系统架构 v0.4：数据流、JSON schema、状态判断规则、难度调整规则、风险表 |
| [HARDWARE.md](HARDWARE.md) | 硬件 v1.3：每个元件原理/接线/数值用途、接线总表、自检清单、0.1 节厂商资料链接与本地副本 |
| [WIRING.md](WIRING.md) | 面包板接线与首次上机指南（2026-09-07，按厂商资料核对）：micro-USB ESP32 兼容性、各模块实物引脚、9 步上机检查（每步有通过标准）、固件核对与编译结论。差异已回填 HARDWARE.md v1.3。厂商资料已下载到 docs/datasheets/ |
| [TODO.md](TODO.md) | P0–P6 开发任务清单（含验收关卡 🔑） |
| [SCHEDULE.md](SCHEDULE.md) | 授课日历（注意：仍是繁体+旧版硬件描述，客户版 PDF 已发） |
| [firmware/](firmware/) | **已实现的数据采集固件 v0.2.0**（PlatformIO），含 README 和串口协议 |
| [unity/](unity/) | Unity 端：SETUP.md（建工程步骤+协作流程）、GAME_DESIGN.md（游戏设计基准，🗣️标记待客户定案项）、tools/chartgen.py（音乐→节拍→谱面JSON，已验证可用） |
| [lessons/](lessons/) | 每堂课的材料。L0_导论课.md = 首课会议指南：五阶段项目框架（目标→硬件管线→实验→模型验证→游戏整合，研究轨与构建轨并行）、决策清单 D1–D5（当场定）、§5 游戏设计开放问题 G1–G5（参考游戏/最小机制/按键数/情绪→难度杠杆/奖励与正向反馈，**只讨论不定案**，学生带提案到 L1）与决策记录表。S2-S5_决策清单.md = S2–S5 全部待定决策（教师内部 + Nick 对齐用，每项标"先由谁谈"，**不直接发学生**；§0 是发 Nick 的对齐摘要）。L1_硬件课.md = L1 线下课主持脚本：环境安装 → vibe coding 测试（clone + 三个探索任务 + 首次 commit）→ 六样硬件逐件走读（机制 / 信号到 ESP32 / 固件读取与预处理 / 用处 / AI 看代码，逐行对应 firmware 源码）→ 烧录自检 → 提案反馈。**开完会要把决策记录回填进相关文档** |

## 硬件定稿（v0.4，2026-09 确定，勿再用旧方案）

- **PulseSensor**（GPIO35，PPG 波形）= 游戏实时心率主力
- **AD8232 心电**（GPIO32 + LO± 27/14）= HRV 金标准，校准段/实验段用
- **思知瑞 GSR 皮肤电模块**（GPIO34，⚠️必须 3.3V 供电；3 针 GND/VCC/ADC，无电位器，**不是 Grove**）= 快速情绪通道，主力实时信号
- **MPU6050**（I2C 0x68，GPIO21/22）= 运动门控（关键防线）
- **裸 MAX30100**（I2C 0x57，同总线）= 选配，默认停用（多数板需改上拉电阻）
- 历史：曾计划 Gravity MAX30102(SEN0518) 与 LIS2DH，**已移除**——SEN0518 心率 4 秒才更新且无 HRV

固件统一心率 `hr` 按 **ECG > PPG > MAX30100** 优先级融合；HR 逐跳更新，RMSSD（HRV）在主线数据流中。

## 关键设计决策（不要重新讨论，已定案）

1. **传输**：USB Serial 115200 NDJSON 为主线（P2 课堂会正式比较三方案，但 Serial 是默认答案）；`ITransport` 抽象保留 UDP/BLE 切换空间
2. **双时间尺度**：GSR 负责秒级快速反应，HR 在 30 秒窗口评估慢速趋势；RMSSD 初版只记录不进状态规则
3. **状态判断**：规则式 first-match（见 ARCHITECTURE §5.2）+ 防抖动（8 秒最短停留、连续 3 次确认、迟滞 0.85、质量/运动闸门）
4. **难度调整**：focused 状态不动难度（心流保护）；EMA 平滑 + 10 秒冷却 + 小节边界应用 + 硬边界 clamp
5. **实验必须有对照组**：adaptive / fixed / sham 三模式 + 每场后主观量表（没有标签无法做监督分类）
6. **一切生理特征用相对基线变化量**（30 秒静息校准），绝不用绝对值
7. Unity 判定用 `AudioSettings.dspTime`，不用 `Time.time`；串口接收在后台线程 + ConcurrentQueue，线程内禁碰 Unity API

## 教学模式（重要，影响所有课程材料的写法）

- **学生零编程基础**，全项目用 vibe coding：她指挥 AI 写代码，自己负责需求、验收、决策
- **学生用的 AI 编程助手是 OpenAI Codex 的 VSCode 扩展**（`openai.chatgpt`，ChatGPT 账号登录），教师用 Claude Code。Codex 自动读的是 `AGENTS.md`，因此仓库根目录放了 AGENTS.md 指向本文件；给学生的材料里工具名一律写 Codex，提示词两边通用
- **代码答辩制度**：每课后作业以 git commit 交付 → 技术教师人工 code review + 当面提问 → 答不出"这段在干嘛"就回炉。学生靠与 AI 紧密沟通准备答辩（逐段讲解→AI出预测考题→自答→AI批改）
- 学生手册：[lessons/vibe_coding_入门.md](lessons/vibe_coding_入门.md)（装机、提问基本功、git、答辩四步法、硬件学习提示词模板）
- L0 作业核心（**纯 AI 助手作业，不写代码不碰 git**，交付发文件）：用 AI 学懂 HARDWARE.md 全部 6 样硬件并写自己话笔记 + G1–G5 游戏设计提案；L1 开场快问快答 + 收尾提案反馈
- L1 线下才开始 vibe coding 本体：她 git clone 本仓库，**只给 README/md 文档不讲课**，用 AI 读懂仓库、跑 firmware/tools/serial_logger.py、做第一次 commit；L1 作业 = 第一个测试脚本（串口读 10 秒/画曲线/深呼吸检测三选一），L2 开头第一次代码答辩
- **给学生写材料时**：假设零基础、多用比喻、给可直接复制的提示词模板

## 语言与沟通约定

- 用户（技术教师）中英混用，**文档一律简体中文**（SCHEDULE.md 尚未转换）
- 给客户的交付物走 Word/PDF（本机有 MS Word COM 可自动转换）
- 用户邮箱 alexmansonlu@gmail.com；心理学教师 Nick（负责 4h 线下课 + 实验督导）

## 当前状态与下一步

- ✅ 架构/硬件/排程文档齐全；固件 v0.2.0 已写完（**未上机验证**）
- ✅ unity/ 目录就绪：建工程指南、游戏设计文档（导论课用）、谱面生成器 chartgen.py（已端到端验证）
- ⏭️ 下一步：① 硬件到手后跑 HARDWARE.md 第 10 节自检清单（重点第 8 项心率融合切换、第 9 项双路 RMSSD 一致性）；② 用户按 unity/SETUP.md 建 Unity 工程后即可开始写 C# 脚本（Unity 工程未建立不阻塞脚本编写）；③ 导论课用 GAME_DESIGN.md 第 6 节讨论清单与客户定案
- 待确认事项见 ARCHITECTURE.md §7.3（传输选型正式定案、阈值 pilot 校正、佩戴位置等）

## 常见坑（已踩过/已预防，别再犯）

- GSR 接 5V 会超 ESP32 ADC 量程（可能损伤引脚）→ 必须 3V3
- 模拟传感器必须接 ADC1（GPIO32-39），ADC2 与 Wi-Fi 冲突
- MPU6050 上电默认睡眠模式，必须写 PWR_MGMT_1=0 唤醒（固件已处理）
- Unity `System.IO.Ports` 需 Api Compatibility Level = .NET Framework
- 游玩按键的肌电会干扰 ECG → `hr` 自动降级到 PPG 属正常现象
- AD8232 贴片电极是耗材，采集前要补购
