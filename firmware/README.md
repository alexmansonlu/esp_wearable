# firmware — 生理信号数据采集固件

> Phase 1（数据集采集 / 硬件验证）阶段的 ESP32 固件与配套电脑端工具。
> 硬件接线见 [../HARDWARE.md](../HARDWARE.md)，架构见 [../ARCHITECTURE.md](../ARCHITECTURE.md)。
> 固件版本 0.2.0（对应架构 v0.4 硬件组合：PulseSensor + AD8232 + GSR + MPU6050 + MAX30100 选配）

## 功能

- 同时读取：PulseSensor（PPG 波形）、AD8232（ECG 波形）、思知瑞 GSR 皮肤电、MPU6050 加速度、裸 MAX30100（选配）
- 板上实时处理：PPG/ECG 自适应阈值心跳检测 → 逐跳 IBI → BPM 与 RMSSD（HRV）；GSR 平滑与 15 秒斜率
- **统一心率 `hr`**：按 ECG > PPG > MAX30100 优先级自动融合（逐跳更新，无 4 秒延迟）
- 10Hz NDJSON 特征流 + 逐跳 beat 事件 + 可开关的 100Hz 原始波形流
- 30 秒静息基线校准（`hr_delta` / `gsr_delta` 的参考零点）

## 快速开始

1. VSCode 安装 **PlatformIO** 扩展，`打开文件夹` 选择本目录（`firmware/`）
2. 按 HARDWARE.md 接线（**GSR 必须 3.3V 供电**；MPU6050 挂 I2C GPIO21/22）
3. 没接的传感器在 [include/config.h](include/config.h) 中把对应 `ENABLE_XXX` 改 0
4. 点状态栏 **Build（对勾）** → **Upload（箭头）**，完成后开 **Serial Monitor（插头）** 应看到：
   ```json
   {"type":"boot","fw":"0.2.0","mpu6050":1,"max30100":0,"gsr":1,"pulse":1,"ecg":1}
   {"type":"bio","seq":0,"t":1234,"hr":-1.0,...}
   ```
5. 上机自检与实时看图（先关闭 Serial Monitor 释放串口；macOS 串口名形如 `/dev/cu.usbserial-1210`）：
   ```bash
   pip install pyserial matplotlib numpy
   python tools/sensor_check.py --port COM5            # 15 秒后给出每个传感器 ✅/❌ 判定
   python tools/live_dashboard.py --port COM5          # 实时波形与趋势窗口；--snapshot x.png 可无窗口存图
   ```
6. 记录数据集（另开终端，关闭 Serial Monitor 以释放串口）：
   ```bash
   pip install pyserial pandas matplotlib
   python tools/serial_logger.py --port COM5 --calibrate --raw --tag P01
   # 静坐30秒完成校准 → 正常活动/游玩 → Ctrl+C 结束
   python tools/plot_session.py data/session_XXXX_P01
   ```

## 串口协议

**上行（ESP32 → 电脑）**，一行一条，115200 波特：

| 类型 | 示例 | 频率 |
|---|---|---|
| 启动 | `{"type":"boot","fw":"0.2.0","mpu6050":1,...}` | 开机一次，各传感器初始化结果 |
| 特征 | `{"type":"bio","seq":42,"t":10430,"hr":77.8,"hr_delta":5.3,"hr_p":77.2,"rmssd_p":41.5,"hr_e":77.8,"rmssd_e":38.2,"lead_off":0,"hr_m":-1.0,"gsr":1834.2,"gsr_raw":1840,"gsr_delta":0.183,"gsr_slope":1.25,"acc":0.012,"quality":7,"fw":"0.2.0"}` | 10 Hz |
| 心搏 | `{"type":"beat","src":"ecg","t":10412,"ibi":812}`（src: `ecg` / `ppg`） | 每跳一条 |
| 波形 | `R,10415,1873,2101,1840`（毫秒,ECG,Pulse,GSR，均为 12-bit ADC 原始值） | 100 Hz，仅 raw 模式 |
| 校准 | `{"type":"calib","started":1}` / `{"type":"calib","done":1,"gsr_base":1650.2,"hr_base":72.5}` | 事件 |

字段约定：
- `hr` = 统一心率（ECG > PPG > MAX30100 优先级融合）；`hr_p`/`hr_e`/`hr_m` 为各来源单独值
- 无效值一律为 `-1`（如手指未贴合、暖机中的 `rmssd_*`）
- `quality` 位掩码：bit0=有可信心率来源，bit1=GSR 在量程内，bit2=基线已建立（全好 = 7）
- `lead_off=1` 表示 ECG 电极脱落；GSR 单位为 ADC counts（分析用相对变化量，见架构文档）

**下行（电脑 → ESP32）**，一行一条指令：

| 指令 | 作用 |
|---|---|
| `calibrate` | 开始 30 秒静息基线校准（期间请勿移动） |
| `raw on` / `raw off` | 开/关 100Hz 波形流 |
| `ping` | 回 `pong`（测连通） |

## 目录结构

```
firmware/
├── platformio.ini            # 构建配置（仅 MAX30100lib 一个外部库）
├── include/config.h          # 引脚、频率、传感器开关（改这里适配硬件）
├── src/
│   ├── main.cpp              # 任务调度 + 心率融合 + 特征汇总 + JSON 输出
│   ├── BeatDetector.h        # PPG/ECG 通用心跳检测（IBI/BPM/RMSSD）
│   ├── MovingAverage.h       # 环形缓冲滑动平均
│   └── sensors/
│       ├── Mpu6050.h         # MPU6050 最小寄存器驱动（0x68，自动尝试 0x69）
│       └── Max30100Wrap.h    # 裸 MAX30100 封装（选配, oxullo 库, 0x57）
├── tools/
│   ├── sensor_check.py       # 上机自检：15 秒判定每个传感器在不在线（WIRING.md §5）
│   ├── live_dashboard.py     # 实时仪表盘：三路波形 + 心率/HRV/GSR/运动趋势（c 校准 / r raw / q 退出）
│   ├── serial_logger.py      # 数据集记录器 → session 文件夹
│   └── plot_session.py       # 记录结果四联图 + 波形图
└── data/                     # 记录输出（不入库）
```

> 后续会逐步演进到 ARCHITECTURE.md §4.1 的完整结构（transport 抽象、native 单元测试等）。

## 常见问题排查

| 症状 | 排查 |
|---|---|
| boot 行 `"mpu6050":0` | 检查 I2C 接线（GPIO21/22）与供电共地；AD0 引脚悬空或接地（0x68）；本驱动已自动尝试 0x69 |
| 没有 `src:"ppg"` beat / `hr_p` 一直 -1 | PulseSensor 贴太紧压闭血管，或太松漏光；调整力度，静待 3–5 秒 |
| 没有 `src:"ecg"` beat 且 `lead_off:1` | 电极贴片接触不良/脱落；皮肤先用酒精棉片清洁 |
| ECG 波形全是毛刺 | 手臂贴法下的肌电干扰：按键/用力时不可避免，改胸贴法或只在静息段用 |
| `hr` 忽跳忽停 | 看 `hr_e`/`hr_p` 哪路在失效；游玩时 ECG 受肌电影响会掉线，此时 `hr` 自动回落到 PPG |
| GSR 读值顶格 4095 或贴 0 | 检查是否误接 5V；指套线是否插到底；手太湿/太干（该模块无电位器，不能调基准） |
| MAX30100 启用后 begin 失败 | 上拉电阻问题，见 HARDWARE.md 的改装说明 |
| `rmssd_*` 一直 -1 | 需要连续约 30 秒稳定心搏才开始输出；先确认 beat 事件流稳定 |
| ESP32 反复重启 | USB 供电不足（换线/换口）；I2C 短路检查 |
