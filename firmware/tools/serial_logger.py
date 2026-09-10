#!/usr/bin/env python3
"""串口数据集记录器 — 把 ESP32 固件的输出保存为一个 session 文件夹。

用法示例：
    python serial_logger.py --port COM5                     # 只记录特征流
    python serial_logger.py --port COM5 --raw               # 同时开启波形流
    python serial_logger.py --port COM5 --calibrate --raw   # 连接后先做30秒基线校准

运行中可直接在终端输入指令并回车转发给固件：calibrate / raw on / raw off / ping
按 Ctrl+C 结束并关闭文件。

产出（默认在 ./data/ 下）：
    session_YYYYmmdd_HHMMSS/
        bio.csv     10Hz 特征流（每行一个 bio 数据包）
        beats.csv   逐跳心搏事件（ECG 与 PPG 的 IBI）
        raw.csv     100Hz 波形流（仅 --raw 或手动 "raw on" 时有内容）
        log.txt     boot/校准/异常等其他行
"""

import argparse
import csv
import datetime
import json
import pathlib
import sys
import threading
import time

if hasattr(sys.stdout, "reconfigure"):  # Windows 控制台默认编码可能打不出中文
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import serial  # pyserial
except ImportError:
    sys.exit("缺少 pyserial：请先执行  pip install pyserial")

BIO_FIELDS = [
    "host_ts", "seq", "t",
    "hr", "hr_delta",
    "hr_p", "rmssd_p", "hr_e", "rmssd_e", "lead_off", "hr_m",
    "gsr", "gsr_raw", "gsr_delta", "gsr_slope",
    "acc", "quality", "fw",
]


def stdin_forwarder(ser: "serial.Serial", stop: threading.Event) -> None:
    """把用户在终端输入的行转发给固件（阻塞读 stdin，daemon 线程随主程序退出）。"""
    while not stop.is_set():
        try:
            line = sys.stdin.readline()
        except Exception:
            return
        if not line:
            return
        line = line.strip()
        if line:
            ser.write((line + "\n").encode("ascii", errors="ignore"))
            print(f">> 已发送指令: {line}")


def main() -> None:
    ap = argparse.ArgumentParser(description="ESP32 生理信号数据集记录器")
    ap.add_argument("--port", required=True, help="串口号，如 COM5")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--out", default="data", help="输出目录（默认 ./data）")
    ap.add_argument("--raw", action="store_true", help="连接后自动开启波形流")
    ap.add_argument("--calibrate", action="store_true", help="连接后自动发送 calibrate")
    ap.add_argument("--tag", default="", help="附加到 session 文件夹名的标签，如受试者编号 P01")
    args = ap.parse_args()

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"session_{stamp}" + (f"_{args.tag}" if args.tag else "")
    outdir = pathlib.Path(args.out) / name
    outdir.mkdir(parents=True, exist_ok=True)

    ser = serial.Serial(args.port, args.baud, timeout=1)
    time.sleep(1.5)  # 等 ESP32 复位后的 boot 行
    print(f"已连接 {args.port} @ {args.baud}，记录到 {outdir}/")

    if args.calibrate:
        ser.write(b"calibrate\n")
        print(">> 已发送 calibrate（请受试者静坐 30 秒）")
    if args.raw:
        ser.write(b"raw on\n")
        print(">> 已开启波形流")

    stop = threading.Event()
    threading.Thread(target=stdin_forwarder, args=(ser, stop), daemon=True).start()

    bio_f = open(outdir / "bio.csv", "w", newline="", encoding="utf-8")
    bio_w = csv.DictWriter(bio_f, fieldnames=BIO_FIELDS, extrasaction="ignore")
    bio_w.writeheader()
    beats_f = open(outdir / "beats.csv", "w", newline="", encoding="utf-8")
    beats_w = csv.writer(beats_f)
    beats_w.writerow(["host_ts", "t", "src", "ibi"])
    raw_f = open(outdir / "raw.csv", "w", newline="", encoding="utf-8")
    raw_w = csv.writer(raw_f)
    raw_w.writerow(["host_ts", "t", "ecg", "pulse", "gsr"])
    log_f = open(outdir / "log.txt", "w", encoding="utf-8")

    n_bio = n_beat = n_raw = n_drop = 0
    last_seq = None
    last_stats = time.time()
    last_bio = {}

    try:
        while True:
            line = ser.readline().decode("ascii", errors="ignore").strip()
            if not line:
                continue
            host_ts = round(time.time(), 3)

            if line.startswith("R,"):
                parts = line.split(",")
                if len(parts) == 5:
                    raw_w.writerow([host_ts] + parts[1:])
                    n_raw += 1
                continue

            j = line.find("{")
            if j > 0:
                line = line[j:]           # 行首乱码（复位后常见）去掉
            if not line.startswith("{"):
                log_f.write(f"{host_ts} {line}\n")
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                log_f.write(f"{host_ts} [坏行] {line}\n")
                continue

            typ = obj.get("type")
            if typ == "bio":
                seq = obj.get("seq")
                if last_seq is not None and seq is not None and seq != last_seq + 1:
                    n_drop += seq - last_seq - 1
                last_seq = seq
                obj["host_ts"] = host_ts
                bio_w.writerow(obj)
                n_bio += 1
                last_bio = obj
            elif typ == "beat":
                beats_w.writerow([host_ts, obj.get("t"), obj.get("src"), obj.get("ibi")])
                n_beat += 1
            else:
                # boot / calib / ack / pong / err 等
                log_f.write(f"{host_ts} {line}\n")
                print(f"<< {line}")

            now = time.time()
            if now - last_stats >= 5:
                rate = n_bio / (now - last_stats) if last_stats else 0
                print(
                    f"[{datetime.datetime.now():%H:%M:%S}] "
                    f"bio {n_bio} 行 ({rate:.1f}/s) | beat {n_beat} | raw {n_raw} | 丢包 {n_drop} | "
                    f"hr={last_bio.get('hr')} hr_e={last_bio.get('hr_e')} "
                    f"gsr={last_bio.get('gsr')} acc={last_bio.get('acc')} q={last_bio.get('quality')}"
                )
                n_bio = n_beat = n_raw = 0
                last_stats = now
    except KeyboardInterrupt:
        print("\n停止记录。")
    finally:
        stop.set()
        for f in (bio_f, beats_f, raw_f, log_f):
            f.close()
        ser.close()
        print(f"数据已保存到 {outdir}/")


if __name__ == "__main__":
    main()
