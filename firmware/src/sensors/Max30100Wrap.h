#pragma once
#include <Arduino.h>
#include <MAX30100_PulseOximeter.h>

// 裸 MAX30100（oxullo MAX30100lib）封装 — 选配，config.h 中 ENABLE_MAX30100=1 时启用。
// 挂 I2C 总线0（Wire, GPIO21/22），地址 0x57。
//
// ⚠️ 多数 GY-MAX30100 板需要改上拉电阻（板上 4.7k 接到了 1.8V 轨），
//    未改装时 begin() 会失败或读数全 0——详见 HARDWARE.md 5.3。
//
// 注意：该库要求 update() 在 loop 中尽可能频繁地被调用（内部 100Hz 采样）。
class Max30100Wrap {
public:
  bool begin() {
    m_ok = m_pox.begin();
    if (m_ok) {
      m_pox.setIRLedCurrent(MAX30100_LED_CURR_7_6MA);
      instance() = this;
      m_pox.setOnBeatDetectedCallback(&Max30100Wrap::onBeat);
    }
    return m_ok;
  }

  void update(uint32_t tMs) {
    if (!m_ok) return;
    m_tMs = tMs;
    m_pox.update();
  }

  bool ok() const { return m_ok; }
  float hr() { return m_ok ? m_pox.getHeartRate() : -1.0f; }
  uint16_t lastIbi() const { return m_ibi; }

private:
  // C++11 下用函数内静态变量存单例指针（该库的回调不带用户参数）
  static Max30100Wrap *&instance() {
    static Max30100Wrap *p = nullptr;
    return p;
  }

  static void onBeat() {
    Max30100Wrap *self = instance();
    if (!self) return;
    uint32_t t = self->m_tMs;
    if (self->m_lastBeat != 0) {
      uint32_t ibi = t - self->m_lastBeat;
      if (ibi >= 300 && ibi <= 1500) self->m_ibi = (uint16_t)ibi;
    }
    self->m_lastBeat = t;
  }

  PulseOximeter m_pox;
  bool m_ok = false;
  uint32_t m_tMs = 0, m_lastBeat = 0;
  uint16_t m_ibi = 0;
};
