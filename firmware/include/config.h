#pragma once

// ============================================================
// 传感器开关：没接的传感器设为 0，固件其余部分照常工作
// ============================================================
#define ENABLE_GSR           1   // 思知瑞 GSR 皮肤电模块（3 针 GND/VCC/ADC）
#define ENABLE_PULSESENSOR   1   // PulseSensor 光电脉搏（模拟波形，主力心率来源）
#define ENABLE_AD8232        1   // AD8232 心电（模拟波形 + 导联脱落检测，HRV 金标准）
#define ENABLE_MPU6050       1   // MPU6050 六轴（只用加速度做运动门控）
#define ENABLE_MAX30100      0   // 裸 MAX30100（I2C 0x57）：多数板需先改上拉电阻，
                                 // 见 HARDWARE.md，改装验证后再置 1

// ============================================================
// 引脚分配（与 HARDWARE.md 接线总表一致）
// ============================================================
#define PIN_GSR       34   // ADC1_CH6，纯输入
#define PIN_PULSE     35   // ADC1_CH7，纯输入
#define PIN_ECG       32   // ADC1_CH4
#define PIN_ECG_LOP   27   // AD8232 LO+（高电平 = 电极脱落）
#define PIN_ECG_LON   14   // AD8232 LO-
#define PIN_I2C_SDA   21   // 单条 I2C 总线：MPU6050(0x68) + MAX30100(0x57, 选配)
#define PIN_I2C_SCL   22

// ============================================================
// 采样与输出频率
// ============================================================
#define FAST_TASK_HZ     200   // ECG / PulseSensor 波形采样 + 心跳检测
#define RAW_STREAM_HZ    100   // raw 模式下波形流输出频率（必须整除 FAST_TASK_HZ）
#define GSR_TASK_HZ      50    // GSR 过采样读取
#define ACC_TASK_HZ      25    // MPU6050 读取
#define PACKET_HZ        10    // bio 特征数据包输出

#define CALIB_DURATION_MS 30000  // 基线校准时长（静坐 30 秒）

#define SERIAL_BAUD 115200
#define FW_VERSION  "0.2.0"
