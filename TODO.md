# TODO.md — 开发任务清单

> 依照 [ARCHITECTURE.md](ARCHITECTURE.md)（v0.4，硬件定稿：PulseSensor + AD8232 + GSR + MPU6050）的阶段顺序拆解。硬件详情见 [HARDWARE.md](HARDWARE.md)。
> **注**：Phase 0–1 的固件代码已有可用实现（[firmware/](firmware/) v0.2.0），对应任务改为「讲解 + 调参 + 实测验证」。
> 标记说明：`[ ]` 未开始 / `[x]` 完成 / `(0.5h)` 预估工时 / 🔑 = 该阶段的验收关卡（过不了就不要进下一阶段）
> 硬件不在手边时：P2 之后所有 Unity 任务都可用 `MockBioTransport` / `fake_device.py` 继续开发。

---

## Phase 0 — 环境搭建与硬件验收（2 h）

### 0.1 开发环境
- [ ] T0-01 (0.2h) 安装 VSCode + PlatformIO 扩展；建立 `firmware/` 项目（board: `esp32dev`, framework: `arduino`）
- [ ] T0-02 (0.1h) 安装 USB 驱动（CH340 或 CP210x，视板子而定），确认设备管理器出现 COM 口
- [ ] T0-03 (0.2h) 建立 Unity 项目 `unity/BioRhythmGame`（建议 2022 LTS），Player Settings → Api Compatibility Level 改为 **.NET Framework**
- [ ] T0-04 (0.2h) 建立 `analysis/` Python 环境：`python -m venv .venv`、`requirements.txt`（pandas, numpy, matplotlib, scikit-learn, jupyter, pyserial）
- [ ] T0-05 (0.2h) 项目根目录 `git init`、编写 `.gitignore`（Unity Library/、Recordings/、.venv/、.pio/）

### 0.2 硬件验收
- [ ] T0-06 (0.2h) ESP32 烧录 Blink，确认烧录流程与 COM 口正常
- [ ] T0-07 (0.3h) 按 HARDWARE.md 第 7 节接线：GSR（**3.3V 供电**，SIG → GPIO34）、PulseSensor（GPIO35）、AD8232（GPIO32 + LO± → 27/14）、MPU6050（I2C GPIO21/22）
- [ ] T0-08 (0.2h) 烧录 I2C scanner，确认扫到 `0x68`（MPU6050；启用 MAX30100 后另见 `0x57`）
- [ ] T0-09 (0.2h) 最小 sketch：`analogRead(34)` 每 100ms 打印一次，戴上 GSR 指环电极确认数值有反应
- [ ] T0-10 (0.2h) 🔑 **验收**：跑通 HARDWARE.md 第 10 节「上电自检清单」全部 10 项

---

## Phase 1 — 固件读取 + 串口输出验证（4 h）

### 1.1 项目骨架
- [ ] T1-01 (0.3h) 建立 ARCHITECTURE.md §4.1 的文件夹结构；写 `config.h`（引脚、GSR_SAMPLE_HZ、PACKET_HZ、TRANSPORT_MODE）与 `types.h`（`BioSample` / `BioFeature` struct）
- [ ] T1-02 (0.3h) 理解任务调度：以 `millis()` 为基底的非阻塞多任务（200Hz 波形采样、50Hz GSR、25Hz 加速度、10Hz 发包），main loop 禁用 `delay()`

### 1.2 传感器驱动
- [ ] T1-03 (0.5h) `BeatDetector` 调参与验证：PulseSensor 与 AD8232 双路波形 → 去基线 → 自适应阈值 → 逐跳 IBI → BPM / RMSSD；对照 Serial Plotter 波形理解每个参数
- [ ] T1-04 (0.3h) GSR 采样：ADC 过采样（50Hz 读、每次 8 样本平均）+ 1 秒滑动平均
- [ ] T1-05 (0.4h) `Mpu6050` 最小寄存器驱动讲解（唤醒/量程/DLPF），计算去重力后的 motion magnitude（g）

### 1.3 滤波与特征
- [ ] T1-06 (0.5h) `MovingAverage`（环形缓冲）与 `MedianFilter`（3 点中值）：纯 C++、不依赖 Arduino API
- [ ] T1-07 (0.4h) 在 `[env:native]` 写滤波器单元测试（喂已知序列、验证输出），`pio test -e native` 通过
- [ ] T1-08 (0.5h) `BaselineTracker`：收到 `calibrate` 指令后累积 60 秒、取后 30 秒平均为基线；之后以 EMA（alpha=0.001）慢速漂移补偿
- [ ] T1-09 (0.5h) 特征计算：统一心率融合（ECG > PPG > MAX30100）、`hr_delta`、`gsr_delta`、`gsr_slope`（15 秒线性斜率）、`quality` bitmask（bit0 心搏新鲜度 / bit1 GSR / bit2 基线就绪）

### 1.4 封装与输出
- [ ] T1-10 (0.3h) `PacketBuilder`：用 ArduinoJson 产生 §3.1 schema 的单行 JSON（含 `seq` 递增）；`ITransport` 接口 + `TransportSerial` 实现
- [ ] T1-11 (0.3h) 使用 `tools/serial_logger.py` 记录一段数据、`plot_session.py` 出图，理解 bio/beat/raw 三种流
- [ ] T1-12 (0.4h) 🔑 **验收**：佩戴设备静坐，10Hz 数据包稳定、`hr` 在合理范围（55–100）且与 `hr_e`/`hr_p` 一致、`rmssd` 输出正值、心算/憋气能看到 GSR 上升、甩手能看到 acc 飙升且质量位变化

---

## Phase 2 — ESP32 → Unity 数据通路打通（3 h）

- [ ] T2-01 (0.5h) 课堂讨论：Serial vs UDP vs BLE 比较表（ARCHITECTURE.md §2 第 3 层），**当堂定案并记录于 ARCHITECTURE.md 待确认清单**
- [ ] T2-02 (0.3h) Unity 端建立 `Scripts/Data/BioPacket.cs`（对应 JSON schema，含 hr/hr_delta/rmssd_p/rmssd_e/lead_off/gsr/gsr_slope/acc/quality）与 `Scripts/Transport/IBioTransport.cs` 接口（`Start/Stop/TryDequeue`）
- [ ] T2-03 (0.7h) `SerialBioTransport.cs`：后台线程 + `SerialPort.ReadLine()` + `ConcurrentQueue<string>`；超时、断线重连、Dispose 安全关闭（**线程内不得调用任何 Unity API**）
- [ ] T2-04 (0.3h) `DataReceiver.cs`（MonoBehaviour）：`Update()` 中 drain queue、`JsonUtility` 解析、保存 `LatestPacket`、发 C# event `OnPacket`
- [ ] T2-05 (0.4h) `MockBioTransport.cs`：不接硬件时产生拟真假数据（逐跳 HR 随机游走、GSR 慢波动、可用键盘触发「压力事件」）；同时写 `firmware/tools/fake_device.py`
- [ ] T2-06 (0.3h) `DebugPanel.cs` v1：画面显示 HR / RMSSD / GSR / seq / 包率 / 丢包率 / 最后数据包时间
- [ ] T2-07 (0.3h) 下行指令：Unity 发 `{"cmd":"calibrate"}`，固件收到后开始基线校准并在完成时置 quality bit2
- [ ] T2-08 (0.2h) 🔑 **验收**：Unity Play 模式连续跑 5 分钟，画面数值实时跳动、丢包率 < 1%、按 Stop 不会让 Unity 卡死（串口正确释放）

---

## Phase 3 — Unity 基础节奏游戏雏形（4 h）

### 3.1 时间轴与谱面
- [ ] T3-01 (0.5h) `AudioConductor.cs`：以 `AudioSettings.dspTime` 为权威时间、`PlayScheduled` 起播、提供 `SongTimeMs` 属性
- [ ] T3-02 (0.5h) 定义 §3.6 谱面格式；`ChartLoader.cs` 读取 `Assets/Charts/*.json`；手写一份 120bpm 测试谱面 `chart_demo_lv3.json`（60–90 秒、含 tier 1–3 音符）

### 3.2 音符系统
- [ ] T3-03 (0.5h) `NotePool.cs` 对象池 + `NoteObject.cs`：依 `note_speed` 与剩余时间计算 Y 位置（位置由时间推导，不用累加位移，避免漂移）
- [ ] T3-04 (0.5h) `NoteSpawner.cs`：lookahead 2 秒生成、按 lane 分 4 轨、依 `tier <= densityThreshold` 过滤
- [ ] T3-05 (0.5h) `InputHandler.cs`：D/F/J/K 对应 4 轨，记录按键的精确 dsp 时间戳
- [ ] T3-06 (0.7h) `JudgeSystem.cs`：判定窗口 Perfect ±40ms / Great ±80ms / Good ±120ms / Miss；找该轨最近未判定音符比对；音符超过 +120ms 未按自动 Miss
- [ ] T3-07 (0.4h) `ScoreManager.cs`：分数、combo、combo break 检测、30 秒滑动窗口 accuracy / miss rate / offset 标准差（供 P4 使用）
- [ ] T3-08 (0.4h) 基础 UI：判定文字弹出、combo 显示、分数、进度条；`03_Result.unity` 结算画面
- [ ] T3-09 (0.0h) 🔑 **验收**：完整游玩一首测试谱面，判定手感正确（刻意早按/晚按能得到对应判定），连续游玩无 GC 卡顿

---

## Phase 4 — 生理数据处理与状态判断（3 h）

- [ ] T4-01 (0.5h) `BioSignalBuffer.cs`：环形缓冲保存最近 60 秒数据包；提供 `HrDelta30sMean`（HR 慢通道平滑）、`GsrSlope15s`、与 ScoreManager 的表现指标汇整成 `BioSnapshot`
- [ ] T4-02 (0.3h) `BioState.cs` enum（Calm/Focused/Nervous/Frustrated/Overloaded）+ `StateRules.asset`（ScriptableObject 存放 §5.2 所有阈值，可在 Inspector 调整）
- [ ] T4-03 (0.7h) `BioStateEstimator.cs`：1Hz 评估、first-match 规则链（含双时间尺度：HR 用 30 秒窗口、GSR 用即时值 + 斜率）、输出 state + confidence；fallback 沿用前一状态
- [ ] T4-04 (0.7h) 防抖动：最短停留 8s、连续 3 次确认、离开阈值 x0.85 迟滞、quality 闸门冻结、`acc > 0.8g` 运动闸门
- [ ] T4-05 (0.4h) EditMode 单元测试：喂合成的 `BioSnapshot` 序列（渐增压力、瞬时噪声、信号中断）验证状态转移与防抖动行为
- [ ] T4-06 (0.4h) `BioHUD.cs`：HR 数字 + 迷你趋势线、GSR 条、状态徽章（五色）、confidence；`DebugPanel` 加入手动覆写状态按钮
- [ ] T4-07 (0.0h) 🔑 **验收**：佩戴游玩，静止时显示 calm；游玩中转为 focused/nervous；深呼吸 30 秒能回落；状态切换平顺不闪烁

---

## Phase 5 — 动态难度串接（2 h）

- [ ] T5-01 (0.4h) `DifficultyParams.cs` + `DifficultyMapping.asset`：§5.4 状态→动作表与 bounds，全部 Inspector 可调
- [ ] T5-02 (0.5h) `DifficultySmoother.cs`：EMA（a=0.3）+ clamp + 10 秒冷却 + 单次变化上限；`DifficultyController.cs` 只在小节边界（每 4 拍）应用
- [ ] T5-03 (0.4h) 接上游戏：`note_speed` 只影响新生成音符；`note_density` 改 tier 阈值；`pattern_complexity` 控制同时按/交错 pattern 开关
- [ ] T5-04 (0.3h) `difficulty_change` 事件写入 events.csv 流；HUD 显示当前三参数与综合档位
- [ ] T5-05 (0.4h) 实验模式开关（`SessionManager`）：`adaptive` / `fixed`（锁定初始难度）/ `sham`（随机时间点随机小幅调整），写入 meta.json
- [ ] T5-06 (0.0h) 🔑 **验收**：用 DebugPanel 手动切换状态，观察难度在 1–2 个小节内平滑到位、不振荡、不越界；画面上既有音符不跳位

---

## Phase 6 — 数据采集与 Python 分析（2 h）

### 6.1 Unity 记录
- [ ] T6-01 (0.5h) `CsvWriter.cs`（缓冲 + 定期 flush）与 `GameplayLogger.cs`：10Hz 写 bio.csv、事件写 events.csv、结束写 meta.json（格式照 §3.3–3.5）；`SessionManager` 产生 session 文件夹
- [ ] T6-02 (0.2h) 校准流程整合：`01_Calibration` 场景 60 秒引导 → 发 calibrate 指令 → 等 quality bit2 → 进入游戏

### 6.2 Python 分析
- [ ] T6-03 (0.3h) `load_session.py` + `preprocess.py`：读 session 文件夹、以 `game_time_ms` 对齐、重采样 1Hz、outlier 处理（IBI 伪影剔除；HR 跳变 > 20bpm/s 标记为 artifact）
- [ ] T6-04 (0.4h) `visualize.py` 标准四联图：(1) HR 曲线 + 状态色带 (2) GSR 曲线 + 斜率 (3) 难度三参数阶梯图 (4) accuracy/miss 滑动曲线 + 判定散点；输出 PNG 到 `outputs/figures/`
- [ ] T6-05 (0.2h) `batch_process.py`：CLI 一键处理 `data/raw/` 下所有 session
- [ ] T6-06 (0.4h) （可选）`classify.py`：以主观标签为 y、生理+表现滑动特征为 X，比较 KNN / RandomForest / LogisticRegression，**GroupKFold（按受试者分组）** 交叉验证，输出混淆矩阵
- [ ] T6-07 (0.0h) 🔑 **验收**：完整跑一场 → 复制 session 文件夹到 `analysis/data/raw/` → 一个指令产出四联图

---

## 课外 — 正式数据采集（4–6 h，非 coding）

- [ ] X-01 设计采集流程 SOP：知情同意 → 佩戴与信号检查（清洁电极）→ 校准 1 分钟 → 3 场 x 3 分钟（adaptive/fixed/sham，顺序 counterbalance）→ 每场后主观量表
- [ ] X-02 制作主观量表（问卷或纸本）：难度、挫折、紧张、心流各 1–5 分，记录 participant_id 与场次对应
- [ ] X-03 招募 6–10 位受试者并排程
- [ ] X-04 执行采集，每场结束当场检查数据完整性（bio.csv 行数约 = 180s x 10Hz）
- [ ] X-05 数据去识别化与备份，合并主观标签到 `data/processed/`
- [ ] X-06 产出最终分析报告：三模式表现比较、状态分布、（可选）分类器结果

---

## 里程碑总览

| 里程碑 | 对应验收 | 累计时数 |
|---|---|---|
| M0 硬件会动 | T0-10 | 2 h |
| M1 生理数据可信 | T1-12 | 6 h |
| M2 数据进入 Unity | T2-08 | 9 h |
| M3 游戏可玩 | T3-09 | 13 h |
| M4 状态看得见 | T4-07 | 16 h |
| M5 难度会自适应 | T5-06 | 18 h |
| M6 分析跑得通 | T6-07 | 20 h |
| M7 数据集完成 | X-06 | +4–6 h |
