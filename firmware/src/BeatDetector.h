#pragma once
#include <Arduino.h>
#include <math.h>

// 自适应阈值心跳检测器：对 PPG（PulseSensor）与 ECG（AD8232）的模拟波形通用。
//
// 处理链：慢基线扣除 -> 峰值包络自适应阈值 -> 带不应期与滞回的上穿触发
//         -> IBI（逐跳间隔）序列 -> BPM / RMSSD
//
// 生理约束：IBI 限定在 300–1500ms（40–200bpm），范围外视为伪影不入窗。
class BeatDetector {
public:
  // refractoryMs: 不应期（两次心跳最短间隔，300ms 对应 200bpm 上限）
  // minThreshold: 阈值下限（ADC counts），防止无信号时噪声触发
  explicit BeatDetector(uint16_t refractoryMs = 300, float minThreshold = 30.0f)
      : m_refractoryMs(refractoryMs), m_minThreshold(minThreshold) {}

  // 每个采样点调用一次（本项目 200Hz）；返回 true 表示检测到一次心跳
  bool update(float v, uint32_t tMs) {
    if (!m_init) { m_baseline = v; m_init = true; }
    m_baseline += (v - m_baseline) * 0.01f;   // 慢基线，约 0.5s 时间常数 @200Hz
    float x = v - m_baseline;

    m_envelope *= 0.999f;                     // 包络每秒衰减约 18% @200Hz
    if (x > m_envelope) m_envelope = x;
    float th = m_envelope * 0.5f;
    if (th < m_minThreshold) th = m_minThreshold;

    bool beat = false;
    if (!m_above && x > th) {
      if (tMs - m_lastBeatMs > m_refractoryMs) {
        if (m_lastBeatMs != 0) pushIbi(tMs - m_lastBeatMs);
        m_lastBeatMs = tMs;
        beat = true;
      }
      m_above = true;
    } else if (m_above && x < th * 0.7f) {
      m_above = false;                        // 滞回退出，防抖动重复触发
    }
    return beat;
  }

  // 最近有效搏动的平均心率（bpm）；有效数据不足时返回 -1
  float bpm() const {
    if (m_count < 3) return -1.0f;
    uint16_t n = m_count < 8 ? m_count : 8;
    float sum = 0;
    for (uint16_t i = 0; i < n; i++) sum += ibiAt((uint16_t)(m_count - 1 - i));
    return 60000.0f / (sum / n);
  }

  // RMSSD（ms）：相邻 IBI 差的均方根，窗口约 30–40 秒；不足时返回 -1
  // 注：伪影被剔除后相邻两个存储值未必是真正连续的心搏，属教学级简化。
  float rmssd() const {
    if (m_count < 5) return -1.0f;
    float sumSq = 0;
    uint16_t n = 0;
    for (uint16_t i = 1; i < m_count; i++) {
      float d = (float)ibiAt(i) - (float)ibiAt((uint16_t)(i - 1));
      sumSq += d * d;
      n++;
    }
    return n ? sqrtf(sumSq / n) : -1.0f;
  }

  uint16_t lastIbi() const { return m_lastIbi; }

  // 最近 maxAgeMs 内是否检测到心跳（判断信号是否存活）
  bool fresh(uint32_t tMs, uint32_t maxAgeMs = 3000) const {
    return m_lastBeatMs != 0 && (tMs - m_lastBeatMs) < maxAgeMs;
  }

  void reset() {
    m_start = m_count = 0;
    m_lastIbi = 0;
    m_lastBeatMs = 0;
    m_envelope = 0;
    m_above = false;
    m_init = false;
  }

private:
  static const uint16_t kMaxIbis = 40;        // 约 30–40 秒的搏动窗口

  void pushIbi(uint32_t ibi) {
    m_lastIbi = (uint16_t)ibi;
    if (ibi < 300 || ibi > 1500) return;      // 生理范围外视为伪影
    m_buf[(m_start + m_count) % kMaxIbis] = (uint16_t)ibi;
    if (m_count < kMaxIbis) m_count++;
    else m_start = (uint16_t)((m_start + 1) % kMaxIbis);
  }

  uint16_t ibiAt(uint16_t i) const { return m_buf[(m_start + i) % kMaxIbis]; }

  uint16_t m_buf[kMaxIbis] = {0};
  uint16_t m_start = 0, m_count = 0;
  uint16_t m_lastIbi = 0;
  uint16_t m_refractoryMs;
  float m_minThreshold;
  float m_baseline = 0, m_envelope = 0;
  uint32_t m_lastBeatMs = 0;
  bool m_above = false, m_init = false;
};
