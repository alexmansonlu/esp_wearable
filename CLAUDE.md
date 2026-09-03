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
| [HARDWARE.md](HARDWARE.md) | 硬件 v1.2：每个元件原理/接线/数值用途、接线总表、自检清单 |
| [TODO.md](TODO.md) | P0–P6 开发任务清单（含验收关卡 🔑） |
| [SCHEDULE.md](SCHEDULE.md) | 授课日历（注意：仍是繁体+旧版硬件描述，客户版 PDF 已发） |
| [firmware/](firmware/) | **已实现的数据采集固件 v0.2.0**（PlatformIO），含 README 和串口协议 |

## 硬件定稿（v0.4，2026-09 确定，勿再用旧方案）

- **PulseSensor**（GPIO35，PPG 波形）= 游戏实时心率主力
- **AD8232 心电**（GPIO32 + LO± 27/14）= HRV 金标准，校准段/实验段用
- **Grove GSR**（GPIO34，⚠️必须 3.3V 供电）= 快速情绪通道，主力实时信号
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

## 语言与沟通约定

- 用户（技术教师）中英混用，**文档一律简体中文**（SCHEDULE.md 尚未转换）
- 给客户的交付物走 Word/PDF（本机有 MS Word COM 可自动转换）
- 用户邮箱 alexmansonlu@gmail.com；心理学教师 Nick（负责 4h 线下课 + 实验督导）

## 当前状态与下一步

- ✅ 架构/硬件/排程文档齐全；固件 v0.2.0 已写完（**未上机验证**）
- ⏭️ 下一步：硬件到手后跑 HARDWARE.md 第 10 节自检清单（重点第 8 项心率融合切换、第 9 项双路 RMSSD 一致性）；然后按 TODO.md P2 开始 Unity 端
- 待确认事项见 ARCHITECTURE.md §7.3（传输选型正式定案、阈值 pilot 校正、佩戴位置等）

## 常见坑（已踩过/已预防，别再犯）

- GSR 接 5V 会超 ESP32 ADC 量程（可能损伤引脚）→ 必须 3V3
- 模拟传感器必须接 ADC1（GPIO32-39），ADC2 与 Wi-Fi 冲突
- MPU6050 上电默认睡眠模式，必须写 PWR_MGMT_1=0 唤醒（固件已处理）
- Unity `System.IO.Ports` 需 Api Compatibility Level = .NET Framework
- 游玩按键的肌电会干扰 ECG → `hr` 自动降级到 PPG 属正常现象
- AD8232 贴片电极是耗材，采集前要补购
