#pragma once
#include <Arduino.h>
#include <Wire.h>
#include <math.h>

// MPU6050 最小寄存器驱动（只用加速度部分，不依赖第三方库）
// 配置：±2g，内部 1kHz 采样 + DLPF 44Hz；固件以 25Hz 读取
// 地址：AD0 接地 = 0x68（默认），AD0 接高 = 0x69（自动尝试）
class Mpu6050 {
public:
  bool begin(TwoWire &wire, uint8_t addr = 0x68) {
    m_wire = &wire;
    m_addr = addr;
    if (!probe()) {
      m_addr = 0x69;                 // 兼容 AD0 拉高的模块
      if (!probe()) return false;
    }
    writeReg(0x6B, 0x00);            // PWR_MGMT_1: 退出睡眠（上电默认在睡眠！）
    delay(10);
    writeReg(0x1C, 0x00);            // ACCEL_CONFIG: ±2g（16384 LSB/g）
    writeReg(0x1A, 0x03);            // CONFIG: DLPF 44Hz，滤高频振动
    m_ok = true;
    return true;
  }

  bool ok() const { return m_ok; }

  // 合加速度与 1g（重力）的偏差，单位 g；静止时约为 0，甩动时明显增大
  float readMotion() {
    if (!m_ok) return 0;
    uint8_t raw[6];
    if (!readRegs(0x3B, raw, 6)) return 0;   // ACCEL_XOUT_H 起连续 6 字节
    int16_t x = (int16_t)((raw[0] << 8) | raw[1]);
    int16_t y = (int16_t)((raw[2] << 8) | raw[3]);
    int16_t z = (int16_t)((raw[4] << 8) | raw[5]);
    float gx = x / 16384.0f, gy = y / 16384.0f, gz = z / 16384.0f;
    float mag = sqrtf(gx * gx + gy * gy + gz * gz);
    return fabsf(mag - 1.0f);
  }

private:
  bool probe() {
    // WHO_AM_I(0x75)：正品 MPU6050 为 0x68，各类兼容芯片可能是 0x70/0x71/0x72 等，
    // 这里只排除总线无应答的情况（0x00 / 0xFF）
    uint8_t who = readReg(0x75);
    return who != 0x00 && who != 0xFF;
  }
  uint8_t readReg(uint8_t reg) {
    m_wire->beginTransmission(m_addr);
    m_wire->write(reg);
    if (m_wire->endTransmission(false) != 0) return 0xFF;
    if (m_wire->requestFrom((int)m_addr, 1) != 1) return 0xFF;
    return (uint8_t)m_wire->read();
  }
  bool readRegs(uint8_t reg, uint8_t *buf, uint8_t n) {
    m_wire->beginTransmission(m_addr);
    m_wire->write(reg);
    if (m_wire->endTransmission(false) != 0) return false;
    if (m_wire->requestFrom((int)m_addr, (int)n) != n) return false;
    for (uint8_t i = 0; i < n; i++) buf[i] = (uint8_t)m_wire->read();
    return true;
  }
  void writeReg(uint8_t reg, uint8_t val) {
    m_wire->beginTransmission(m_addr);
    m_wire->write(reg);
    m_wire->write(val);
    m_wire->endTransmission();
  }

  TwoWire *m_wire = nullptr;
  uint8_t m_addr = 0x68;
  bool m_ok = false;
};
