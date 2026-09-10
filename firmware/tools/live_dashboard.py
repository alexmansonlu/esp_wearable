#!/usr/bin/env python3
"""
live_dashboard.py — 实时可视化仪表盘（ESP32 生理信号固件 v0.2.0）

左列：三路原始波形（ECG / PPG / GSR，100Hz raw 流，最近 8 秒），心搏用竖线标记
右列：趋势（统一心率与两路来源、RMSSD、GSR 平滑值、运动量，最近 120 秒）
顶部：状态栏（心率来源、导联状态、quality、包率、校准状态）

用法：
    python tools/live_dashboard.py --port /dev/cu.usbserial-1210
    python tools/live_dashboard.py --port COM5 --snapshot shot.png --seconds 20   # 无窗口，跑 20 秒存图

窗口内快捷键：  c = 发送 calibrate（30 秒静息校准）   r = 开/关 raw 波形流   q = 退出
依赖：pip install pyserial matplotlib numpy
"""
import argparse
import collections
import json
import threading
import time

import serial

WAVE_SEC = 8        # 波形窗口（秒）
TREND_SEC = 120     # 趋势窗口（秒）
RAW_HZ = 100
BIO_HZ = 10


class SerialReader(threading.Thread):
    """后台线程：读串口、解析三种行、填充环形缓冲。所有缓冲用 lock 保护。"""

    def __init__(self, port, baud):
        super().__init__(daemon=True)
        self.ser = serial.Serial(port, baud, timeout=0.2)
        self.lock = threading.Lock()
        n_wave = WAVE_SEC * RAW_HZ + 50
        n_trend = TREND_SEC * BIO_HZ + 20
        self.wave_t = collections.deque(maxlen=n_wave)
        self.wave_ecg = collections.deque(maxlen=n_wave)
        self.wave_ppg = collections.deque(maxlen=n_wave)
        self.wave_gsr = collections.deque(maxlen=n_wave)
        self.beats_ppg = collections.deque(maxlen=60)   # 时间戳 ms
        self.beats_ecg = collections.deque(maxlen=60)
        self.trend = collections.deque(maxlen=n_trend)  # bio dict
        self.last_bio = None
        self.boot = None
        self.calib = None
        self.events = collections.deque(maxlen=6)       # 最近的事件文本
        self.raw_on = False
        self.n_bio = 0
        self.t_rate = time.time()
        self.rate = 0.0
        self.running = True

    def send(self, cmd):
        self.ser.write((cmd + "\n").encode())
        self.events.append(f"→ {cmd}")

    def run(self):
        while self.running:
            try:
                line = self.ser.readline().decode(errors="replace").strip()
            except serial.SerialException:
                self.events.append("串口断开")
                break
            if not line:
                continue
            if line.startswith("R,"):
                p = line.split(",")
                if len(p) == 5:
                    try:
                        t, e, pu, g = int(p[1]), int(p[2]), int(p[3]), int(p[4])
                    except ValueError:
                        continue
                    with self.lock:
                        self.wave_t.append(t); self.wave_ecg.append(e)
                        self.wave_ppg.append(pu); self.wave_gsr.append(g)
                continue
            if not line.startswith("{"):
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            typ = d.get("type")
            with self.lock:
                if typ == "bio":
                    self.trend.append(d); self.last_bio = d; self.n_bio += 1
                    now = time.time()
                    if now - self.t_rate >= 2:
                        self.rate = self.n_bio / (now - self.t_rate)
                        self.n_bio = 0; self.t_rate = now
                elif typ == "beat":
                    (self.beats_ecg if d.get("src") == "ecg" else self.beats_ppg).append(d["t"])
                elif typ == "boot":
                    self.boot = d; self.events.append(f"boot fw={d.get('fw')} mpu={d.get('mpu6050')}")
                elif typ == "calib":
                    self.calib = d
                    self.events.append("校准开始（静坐 30 秒）" if d.get("started")
                                       else f"校准完成 gsr_base={d.get('gsr_base')} hr_base={d.get('hr_base')}")
                elif typ == "ack":
                    self.raw_on = bool(d.get("raw")); self.events.append(f"raw={'on' if self.raw_on else 'off'}")
                elif typ == "pong":
                    self.events.append("pong")
                elif typ == "err":
                    self.events.append(f"err: {d.get('msg')}")

    def stop(self):
        self.running = False
        try:
            self.ser.write(b"raw off\n"); time.sleep(0.2); self.ser.close()
        except Exception:
            pass


def build_figure(plt, reader, port):
    C = {"ecg": "#e4572e", "ppg": "#17bebb", "gsr": "#ffc914", "hr": "#ffffff",
         "hr_p": "#17bebb", "hr_e": "#e4572e", "acc": "#a06cd5", "grid": "#333"}
    plt.style.use("dark_background")
    fig = plt.figure(figsize=(15, 8.5))
    fig.canvas.manager.set_window_title(f"Bio Dashboard — {port}") if hasattr(fig.canvas, "manager") and fig.canvas.manager else None
    gs = fig.add_gridspec(4, 2, width_ratios=[1.35, 1], height_ratios=[0.28, 1, 1, 1],
                          left=0.05, right=0.98, top=0.96, bottom=0.06, hspace=0.42, wspace=0.18)

    ax_status = fig.add_subplot(gs[0, :]); ax_status.axis("off")
    status_txt = ax_status.text(0, 0.9, "", fontsize=12, va="top", transform=ax_status.transAxes)
    event_txt = ax_status.text(1.0, 0.9, "", fontsize=9, va="top", ha="right",
                               color="#aaa", transform=ax_status.transAxes)

    ax_ecg = fig.add_subplot(gs[1, 0]); ax_ppg = fig.add_subplot(gs[2, 0], sharex=ax_ecg)
    ax_gsrw = fig.add_subplot(gs[3, 0], sharex=ax_ecg)
    ax_hr = fig.add_subplot(gs[1, 1]); ax_hrv = fig.add_subplot(gs[2, 1], sharex=ax_hr)
    ax_gsrt = fig.add_subplot(gs[3, 1], sharex=ax_hr)
    ax_acc = ax_gsrt.twinx()

    for ax, title in [(ax_ecg, "ECG 心电波形 (AD8232, GPIO32)"), (ax_ppg, "PPG 脉搏波形 (PulseSensor, GPIO35)"),
                      (ax_gsrw, "GSR 皮肤电原始 (GPIO34)"), (ax_hr, "心率 bpm"), (ax_hrv, "RMSSD (HRV) ms"),
                      (ax_gsrt, "GSR 平滑值 (左) / 运动量 acc g (右)")]:
        ax.set_title(title, fontsize=10, loc="left", color="#ddd")
        ax.grid(True, color=C["grid"], lw=0.5)
        ax.tick_params(labelsize=8)
    ax_gsrw.set_xlabel("秒（0 = 现在）", fontsize=8); ax_gsrt.set_xlabel("秒（0 = 现在）", fontsize=8)

    L = {}
    L["ecg"], = ax_ecg.plot([], [], color=C["ecg"], lw=1)
    L["ppg"], = ax_ppg.plot([], [], color=C["ppg"], lw=1)
    L["gsrw"], = ax_gsrw.plot([], [], color=C["gsr"], lw=1)
    L["hr"], = ax_hr.plot([], [], color=C["hr"], lw=2, label="hr 统一")
    L["hr_p"], = ax_hr.plot([], [], color=C["hr_p"], lw=1, alpha=0.8, label="hr_p PPG")
    L["hr_e"], = ax_hr.plot([], [], color=C["hr_e"], lw=1, alpha=0.8, label="hr_e ECG")
    L["rmssd_p"], = ax_hrv.plot([], [], color=C["hr_p"], lw=1.2, label="rmssd_p")
    L["rmssd_e"], = ax_hrv.plot([], [], color=C["hr_e"], lw=1.2, label="rmssd_e")
    L["gsrt"], = ax_gsrt.plot([], [], color=C["gsr"], lw=1.5, label="gsr")
    L["acc"], = ax_acc.plot([], [], color=C["acc"], lw=1, alpha=0.8, label="acc")
    ax_acc.axhline(0.8, color=C["acc"], ls=":", lw=0.8); ax_acc.set_ylim(0, 1.5); ax_acc.tick_params(labelsize=8)
    ax_hr.legend(fontsize=8, loc="upper left"); ax_hrv.legend(fontsize=8, loc="upper left")
    ax_hr.set_ylim(40, 140)
    beat_lines = {"ecg": ax_ecg.vlines([], 0, 1, color="#fff", alpha=0.35, lw=1),
                  "ppg": ax_ppg.vlines([], 0, 1, color="#fff", alpha=0.35, lw=1)}

    def set_vlines(coll, xs, ax):
        y0, y1 = ax.get_ylim()
        coll.set_segments([[(x, y0), (x, y1)] for x in xs])

    def autoscale(ax, ys, pad=0.1, minspan=50):
        if not ys:
            return
        lo, hi = min(ys), max(ys)
        span = max(hi - lo, minspan)
        ax.set_ylim(lo - span * pad, hi + span * pad)

    def update(_):
        with reader.lock:
            wt = list(reader.wave_t); we = list(reader.wave_ecg); wp = list(reader.wave_ppg); wg = list(reader.wave_gsr)
            bp = list(reader.beats_ppg); be = list(reader.beats_ecg)
            tr = list(reader.trend); lb = reader.last_bio; events = list(reader.events)
            rate = reader.rate; raw_on = reader.raw_on; calib = reader.calib
        now_ms = lb["t"] if lb else (wt[-1] if wt else 0)

        if wt:
            x = [(t - now_ms) / 1000 for t in wt]
            L["ecg"].set_data(x, we); L["ppg"].set_data(x, wp); L["gsrw"].set_data(x, wg)
            ax_ecg.set_xlim(-WAVE_SEC, 0)
            autoscale(ax_ecg, we); autoscale(ax_ppg, wp); autoscale(ax_gsrw, wg, minspan=30)
            set_vlines(beat_lines["ecg"], [(t - now_ms) / 1000 for t in be if now_ms - t < WAVE_SEC * 1000], ax_ecg)
            set_vlines(beat_lines["ppg"], [(t - now_ms) / 1000 for t in bp if now_ms - t < WAVE_SEC * 1000], ax_ppg)
        elif not raw_on:
            ax_ecg.set_title("ECG 心电波形 — 按 r 打开 raw 波形流", fontsize=10, loc="left", color="#ddd")

        if tr:
            x = [(d["t"] - now_ms) / 1000 for d in tr]
            def series(k):
                return [d[k] if d[k] > 0 else float("nan") for d in tr]
            L["hr"].set_data(x, series("hr")); L["hr_p"].set_data(x, series("hr_p")); L["hr_e"].set_data(x, series("hr_e"))
            L["rmssd_p"].set_data(x, series("rmssd_p")); L["rmssd_e"].set_data(x, series("rmssd_e"))
            L["gsrt"].set_data(x, [d["gsr"] for d in tr]); L["acc"].set_data(x, [d["acc"] for d in tr])
            ax_hr.set_xlim(-TREND_SEC, 0)
            rm = [v for d in tr for v in (d["rmssd_p"], d["rmssd_e"]) if v > 0]
            ax_hrv.set_ylim(0, max(100, max(rm) * 1.1) if rm else 100)
            autoscale(ax_gsrt, [d["gsr"] for d in tr], minspan=50)

        if lb:
            q = lb["quality"]
            src = "ECG" if lb["hr_e"] > 0 and not lb["lead_off"] else ("PPG" if lb["hr_p"] > 0 else "无")
            leads = "贴合" if lb["lead_off"] == 0 else "脱落"
            cal = ("校准中…" if calib and calib.get("started") and not (q & 4) else
                   "已校准" if q & 4 else "未校准 (按 c)")
            status_txt.set_text(
                f"HR {lb['hr']:6.1f} bpm  来源 {src:3s}   |  PPG {lb['hr_p']:6.1f}   ECG {lb['hr_e']:6.1f}  电极{leads}   |  "
                f"GSR {lb['gsr']:7.1f} (Δ{lb['gsr_delta']:+.2f}, 斜率 {lb['gsr_slope']:+.1f}/s)   |  acc {lb['acc']:.2f}g\n"
                f"quality {q} [{'心率' if q & 1 else '  '}|{'GSR' if q & 2 else '   '}|{'基线' if q & 4 else '  '}]   "
                f"{cal}   |  包率 {rate:4.1f}/s   raw {'ON' if raw_on else 'off'}   t={lb['t']/1000:.0f}s   fw {lb['fw']}"
            )
        event_txt.set_text("\n".join(events[-3:]))
        return []

    return fig, update


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--no-raw", action="store_true", help="启动时不自动打开 raw 波形流")
    ap.add_argument("--snapshot", help="无窗口模式：跑 --seconds 秒后把画面存成 PNG")
    ap.add_argument("--seconds", type=int, default=15)
    args = ap.parse_args()

    import matplotlib
    if args.snapshot:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    for f in ["Hiragino Sans GB", "PingFang SC", "Heiti TC", "Arial Unicode MS", "Microsoft YaHei", "SimHei", "Noto Sans CJK SC"]:
        if any(f == x.name for x in font_manager.fontManager.ttflist):
            plt.rcParams["font.family"] = f; break
    plt.rcParams["axes.unicode_minus"] = False

    reader = SerialReader(args.port, args.baud)
    reader.start()
    if not args.no_raw:
        time.sleep(0.3); reader.send("raw on")

    fig, update = build_figure(plt, reader, args.port)

    if args.snapshot:
        time.sleep(args.seconds); update(0); fig.savefig(args.snapshot, dpi=110)
        reader.stop(); print("saved", args.snapshot); return

    from matplotlib.animation import FuncAnimation

    def on_key(ev):
        if ev.key == "c":
            reader.send("calibrate")
        elif ev.key == "r":
            reader.send("raw off" if reader.raw_on else "raw on")
        elif ev.key == "q":
            plt.close(fig)
    fig.canvas.mpl_connect("key_press_event", on_key)
    anim = FuncAnimation(fig, update, interval=100, cache_frame_data=False)  # noqa: F841
    try:
        plt.show()
    finally:
        reader.stop()


if __name__ == "__main__":
    main()
