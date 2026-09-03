// ============================================================
// 生理信号数据采集固件 v0.2.0
// ------------------------------------------------------------
// 硬件组合（v0.4 架构）：PulseSensor(PPG) + AD8232(ECG) + Grove GSR
//                       + MPU6050(运动门控) + 裸 MAX30100(选配)
// 心率与 HRV 全部由板上波形心跳检测得出（逐跳更新），
// 统一心率 hr 按 ECG > PPG > MAX30100 优先级融合。
// 输出格式与串口指令说明见 firmware/README.md。
// 电脑端配套：tools/serial_logger.py（记录数据集）
// ============================================================

#include <Arduino.h>
#include <Wire.h>
#include <math.h>

#include "config.h"
#include "BeatDetector.h"
#include "MovingAverage.h"
#include "sensors/Mpu6050.h"
#if ENABLE_MAX30100
#include "sensors/Max30100Wrap.h"
#endif

// ---------- 传感器对象 ----------
Mpu6050 g_mpu;
#if ENABLE_MAX30100
Max30100Wrap g_max30100;
#endif
BeatDetector g_pulseBeat(300, 25.0f);   // PPG 波形较缓，阈值下限低一些
BeatDetector g_ecgBeat(300, 40.0f);     // ECG R 峰尖锐，阈值下限高一些抗噪

// ---------- GSR 状态 ----------
MovingAverage<50> g_gsrMa;              // 1 秒平滑 @50Hz
float g_gsrSmoothed = 0;
int g_gsrRaw = 0;
float g_gsrHistory[15] = {0};           // 每秒一个点，算 15 秒斜率
uint8_t g_gsrHistIdx = 0;
bool g_gsrHistFull = false;

// ---------- 运动状态 ----------
MovingAverage<5> g_accMa;

// ---------- 基线校准 ----------
float g_gsrBaseline = 0, g_hrBaseline = 0;
bool g_baselineReady = false;
bool g_calibrating = false;
uint32_t g_calibStart = 0;
double g_calibGsrSum = 0, g_calibHrSum = 0;
uint32_t g_calibGsrN = 0, g_calibHrN = 0;

// ---------- 输出控制 ----------
uint32_t g_seq = 0;
bool g_rawStream = false;
int g_lastEcgRaw = 0, g_lastPulseRaw = 0;

// ---------- 任务计时 ----------
uint32_t g_tFast = 0, g_tGsr = 0, g_tAcc = 0, g_tPacket = 0, g_tSlope = 0;
uint8_t g_rawDivider = 0;

static bool ecgLeadOff() {
#if ENABLE_AD8232
  return digitalRead(PIN_ECG_LOP) || digitalRead(PIN_ECG_LON);
#else
  return true;
#endif
}

// 统一心率：优先 ECG（最准），其次 PPG，再次 MAX30100；全部无效返回 -1
static float bestHr(uint32_t now) {
#if ENABLE_AD8232
  if (!ecgLeadOff() && g_ecgBeat.fresh(now)) {
    float h = g_ecgBeat.bpm();
    if (h > 0) return h;
  }
#endif
#if ENABLE_PULSESENSOR
  if (g_pulseBeat.fresh(now)) {
    float h = g_pulseBeat.bpm();
    if (h > 0) return h;
  }
#endif
#if ENABLE_MAX30100
  {
    float h = g_max30100.hr();
    if (h > 30) return h;
  }
#endif
  return -1.0f;
}

// 最近 15 秒 GSR 线性回归斜率（ADC counts / 秒）
static float gsrSlope() {
  uint8_t n = g_gsrHistFull ? 15 : g_gsrHistIdx;
  if (n < 5) return 0;
  float sx = 0, sy = 0, sxy = 0, sxx = 0;
  for (uint8_t i = 0; i < n; i++) {
    float y = g_gsrHistory[(g_gsrHistIdx + 15 - n + i) % 15];  // 从最旧到最新
    sx += i; sy += y; sxy += (float)i * y; sxx += (float)i * i;
  }
  float denom = n * sxx - sx * sx;
  return denom != 0 ? (n * sxy - sx * sy) / denom : 0;
}

static void handleCommand(const String &cmd) {
  if (cmd == "calibrate") {
    g_calibrating = true;
    g_calibStart = millis();
    g_calibGsrSum = g_calibHrSum = 0;
    g_calibGsrN = g_calibHrN = 0;
    g_baselineReady = false;
    Serial.println("{\"type\":\"calib\",\"started\":1}");
  } else if (cmd == "raw on") {
    g_rawStream = true;
    Serial.println("{\"type\":\"ack\",\"raw\":1}");
  } else if (cmd == "raw off") {
    g_rawStream = false;
    Serial.println("{\"type\":\"ack\",\"raw\":0}");
  } else if (cmd == "ping") {
    Serial.printf("{\"type\":\"pong\",\"t\":%lu,\"fw\":\"%s\"}\n",
                  (unsigned long)millis(), FW_VERSION);
  } else {
    Serial.printf("{\"type\":\"err\",\"msg\":\"unknown cmd\",\"cmd\":\"%s\"}\n", cmd.c_str());
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(300);

  analogReadResolution(12);
  analogSetPinAttenuation((uint8_t)PIN_GSR, ADC_11db);    // 量程 0–3.3V
  analogSetPinAttenuation((uint8_t)PIN_PULSE, ADC_11db);
  analogSetPinAttenuation((uint8_t)PIN_ECG, ADC_11db);
  pinMode(PIN_ECG_LOP, INPUT);
  pinMode(PIN_ECG_LON, INPUT);

  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);   // 单总线：MPU6050 + MAX30100(选配)
  Wire.setClock(400000);

  bool mpuOk = false, m100Ok = false;
#if ENABLE_MPU6050
  mpuOk = g_mpu.begin(Wire);
#endif
#if ENABLE_MAX30100
  m100Ok = g_max30100.begin();
#endif

  Serial.printf(
      "{\"type\":\"boot\",\"fw\":\"%s\",\"mpu6050\":%d,\"max30100\":%d,"
      "\"gsr\":%d,\"pulse\":%d,\"ecg\":%d}\n",
      FW_VERSION, mpuOk ? 1 : 0, m100Ok ? 1 : 0,
      ENABLE_GSR, ENABLE_PULSESENSOR, ENABLE_AD8232);
}

void loop() {
  uint32_t now = millis();

  // ---- 指令解析（非阻塞按行）----
  static String cmdBuf;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (cmdBuf.length()) handleCommand(cmdBuf);
      cmdBuf = "";
    } else if (cmdBuf.length() < 64) {
      cmdBuf += c;
    }
  }

#if ENABLE_MAX30100
  g_max30100.update(now);   // 该库要求每次 loop 都调用
#endif

  // ---- 快任务 @200Hz：ECG + PulseSensor 波形采样与心跳检测 ----
  if (now - g_tFast >= 1000 / FAST_TASK_HZ) {
    g_tFast = now;
#if ENABLE_AD8232
    bool leadOff = ecgLeadOff();
    g_lastEcgRaw = analogRead(PIN_ECG);
    if (!leadOff && g_ecgBeat.update((float)g_lastEcgRaw, now)) {
      Serial.printf("{\"type\":\"beat\",\"src\":\"ecg\",\"t\":%lu,\"ibi\":%u}\n",
                    (unsigned long)now, g_ecgBeat.lastIbi());
    }
#endif
#if ENABLE_PULSESENSOR
    g_lastPulseRaw = analogRead(PIN_PULSE);
    if (g_pulseBeat.update((float)g_lastPulseRaw, now)) {
      Serial.printf("{\"type\":\"beat\",\"src\":\"ppg\",\"t\":%lu,\"ibi\":%u}\n",
                    (unsigned long)now, g_pulseBeat.lastIbi());
    }
#endif
    // raw 波形流（降频到 RAW_STREAM_HZ）：R,毫秒,ECG,Pulse,GSR
    if (g_rawStream && ++g_rawDivider >= FAST_TASK_HZ / RAW_STREAM_HZ) {
      g_rawDivider = 0;
      Serial.printf("R,%lu,%d,%d,%d\n", (unsigned long)now, g_lastEcgRaw,
                    g_lastPulseRaw, g_gsrRaw);
    }
  }

  // ---- GSR 任务 @50Hz：过采样 + 平滑 ----
  if (now - g_tGsr >= 1000 / GSR_TASK_HZ) {
    g_tGsr = now;
#if ENABLE_GSR
    uint32_t sum = 0;
    for (int i = 0; i < 8; i++) sum += analogRead(PIN_GSR);
    g_gsrRaw = (int)(sum / 8);
    g_gsrMa.push((float)g_gsrRaw);
    g_gsrSmoothed = g_gsrMa.mean();
    if (g_calibrating) { g_calibGsrSum += g_gsrSmoothed; g_calibGsrN++; }
#endif
  }

  // ---- 每秒任务：GSR 斜率历史 + 校准期心率采样 ----
  if (now - g_tSlope >= 1000) {
    g_tSlope = now;
    g_gsrHistory[g_gsrHistIdx] = g_gsrSmoothed;
    g_gsrHistIdx = (uint8_t)((g_gsrHistIdx + 1) % 15);
    if (g_gsrHistIdx == 0) g_gsrHistFull = true;

    if (g_calibrating) {
      float h = bestHr(now);
      if (h > 0) { g_calibHrSum += h; g_calibHrN++; }
    }
  }

  // ---- 加速度任务 @25Hz ----
  if (now - g_tAcc >= 1000 / ACC_TASK_HZ) {
    g_tAcc = now;
#if ENABLE_MPU6050
    g_accMa.push(g_mpu.readMotion());
#endif
  }

  // ---- 校准结束判定 ----
  if (g_calibrating && now - g_calibStart >= CALIB_DURATION_MS) {
    g_calibrating = false;
    if (g_calibGsrN > 0) g_gsrBaseline = (float)(g_calibGsrSum / g_calibGsrN);
    if (g_calibHrN > 0) g_hrBaseline = (float)(g_calibHrSum / g_calibHrN);
    g_baselineReady = (g_calibGsrN > 0);
    Serial.printf("{\"type\":\"calib\",\"done\":1,\"gsr_base\":%.1f,\"hr_base\":%.1f}\n",
                  g_gsrBaseline, g_hrBaseline);
  }

  // ---- bio 特征数据包 @10Hz ----
  if (now - g_tPacket >= 1000 / PACKET_HZ) {
    g_tPacket = now;

    bool leadOff = ecgLeadOff();
    float hrP = g_pulseBeat.fresh(now) ? g_pulseBeat.bpm() : -1.0f;
    float hrE = (!leadOff && g_ecgBeat.fresh(now)) ? g_ecgBeat.bpm() : -1.0f;
    float hrM = -1.0f;
#if ENABLE_MAX30100
    hrM = g_max30100.hr();
    if (hrM <= 30) hrM = -1.0f;
#endif
    float hr = bestHr(now);
    float hrDelta = (g_baselineReady && hr > 0 && g_hrBaseline > 0)
                        ? hr - g_hrBaseline : 0;
    float gsrDelta = (g_baselineReady && g_gsrBaseline > 1.0f)
                         ? (g_gsrSmoothed - g_gsrBaseline) / g_gsrBaseline : 0;

    uint8_t quality = 0;
    if (hr > 0) quality |= 1;                            // bit0: 有可信心率来源
    if (g_gsrRaw > 5 && g_gsrRaw < 4090) quality |= 2;   // bit1: GSR 在量程内
    if (g_baselineReady) quality |= 4;                   // bit2: 基线就绪

    char buf[512];
    snprintf(buf, sizeof(buf),
             "{\"type\":\"bio\",\"seq\":%lu,\"t\":%lu,"
             "\"hr\":%.1f,\"hr_delta\":%.1f,"
             "\"hr_p\":%.1f,\"rmssd_p\":%.1f,"
             "\"hr_e\":%.1f,\"rmssd_e\":%.1f,\"lead_off\":%d,"
             "\"hr_m\":%.1f,"
             "\"gsr\":%.1f,\"gsr_raw\":%d,\"gsr_delta\":%.3f,\"gsr_slope\":%.2f,"
             "\"acc\":%.3f,\"quality\":%u,\"fw\":\"%s\"}",
             (unsigned long)g_seq++, (unsigned long)now,
             hr, hrDelta,
             hrP, g_pulseBeat.rmssd(),
             hrE, g_ecgBeat.rmssd(), leadOff ? 1 : 0,
             hrM,
             g_gsrSmoothed, g_gsrRaw, gsrDelta, gsrSlope(),
             g_accMa.mean(), quality, FW_VERSION);
    Serial.println(buf);
  }
}
