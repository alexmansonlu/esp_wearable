#pragma once
#include <stdint.h>

// 定长环形缓冲滑动平均
template <uint16_t N>
class MovingAverage {
public:
  void push(float v) {
    m_sum -= m_buf[m_idx];
    m_buf[m_idx] = v;
    m_sum += v;
    m_idx = (uint16_t)((m_idx + 1) % N);
    if (m_count < N) m_count++;
  }
  float mean() const { return m_count ? m_sum / m_count : 0.0f; }
  bool full() const { return m_count == N; }
  void reset() {
    for (uint16_t i = 0; i < N; i++) m_buf[i] = 0;
    m_sum = 0; m_idx = 0; m_count = 0;
  }

private:
  float m_buf[N] = {0};
  float m_sum = 0;
  uint16_t m_idx = 0;
  uint16_t m_count = 0;
};
