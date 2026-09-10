#!/usr/bin/env python3
"""
sensor_check.py — 一眼看出每个传感器在不在线（对应 WIRING.md §5 上机步骤）

用法：
    python tools/sensor_check.py --port /dev/cu.usbserial-1210
    python tools/sensor_check.py --port COM5 --seconds 20

每秒刷新一行仪表盘，结束时给出每个传感器的判定。Ctrl+C 随时退出。
依赖：pip install pyserial
"""
import argparse
import json
import statistics
import sys
import time

import serial


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True, help="串口，如 /dev/cu.usbserial-1210 或 COM5")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--seconds", type=int, default=15, help="观察时长（秒）")
    args = ap.parse_args()

    s = serial.Serial(args.port, args.baud, timeout=1)
    s.reset_input_buffer()
    print(f"已连接 {args.port} @ {args.baud}，观察 {args.seconds} 秒…（Ctrl+C 退出）\n")

    bio, beats, boot = [], {"ppg": 0, "ecg": 0}, None
    t0 = time.time()
    last_print = 0
    try:
        while time.time() - t0 < args.seconds:
            line = s.readline().decode(errors="replace").strip()
            if not line or not line.startswith("{"):
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = d.get("type")
            if t == "boot":
                boot = d
                print("BOOT:", line)
            elif t == "beat":
                beats[d.get("src", "?")] = beats.get(d.get("src", "?"), 0) + 1
            elif t == "bio":
                bio.append(d)
                if time.time() - last_print >= 1:
                    last_print = time.time()
                    print(
                        f"[{int(time.time()-t0):3d}s] "
                        f"hr={d['hr']:6.1f} (ppg {d['hr_p']:6.1f} | ecg {d['hr_e']:6.1f})  "
                        f"lead_off={d['lead_off']}  gsr_raw={d['gsr_raw']:4d}  "
                        f"acc={d['acc']:.3f}g  quality={d['quality']}  "
                        f"beats ppg/ecg={beats.get('ppg',0)}/{beats.get('ecg',0)}"
                    )
    except KeyboardInterrupt:
        pass
    finally:
        s.close()

    if not bio:
        print("\n❌ 没收到任何 bio 数据包。检查：串口是否被别的程序占用、波特率 115200、是否烧录成功。")
        sys.exit(1)

    dur = max(1e-6, bio[-1]["t"] - bio[0]["t"]) / 1000
    rate = len(bio) / dur
    col = lambda k: [b[k] for b in bio]
    gsr = col("gsr_raw")
    hrp = [v for v in col("hr_p") if v > 0]
    hre = [v for v in col("hr_e") if v > 0]
    acc = col("acc")
    lead_ok = any(b["lead_off"] == 0 for b in bio)

    print("\n========== 判定 ==========")
    print(f"数据流   : {'✅' if rate > 8 else '❌'} {rate:.1f} 包/秒（应≈10）")
    if boot:
        print(f"MPU6050  : {'✅ 在线' if boot.get('mpu6050') else '❌ 未检测到（查 I2C 21/22 接线）'}"
              f"，acc 静止 {min(acc):.3f}g / 最大 {max(acc):.3f}g")
    else:
        print(f"MPU6050  : （未见 boot 行，按 EN 复位后再跑可看到）acc 范围 {min(acc):.3f}–{max(acc):.3f}g")
    gsr_state = ("❌ 恒为 0（没接线/没供电）" if max(gsr) == 0 else
                 "⚠️ 顶格 4095（超量程：误接 5V 或指套没插紧）" if min(gsr) >= 4090 else
                 "✅ 有读数")
    print(f"GSR      : {gsr_state}，gsr_raw {min(gsr)}–{max(gsr)}（戴指套后应明显高于不戴）")
    if hrp:
        rm = [v for v in col("rmssd_p") if v > 0]
        stab = "稳定" if (statistics.pstdev(hrp) < 8) else "波动大（手指再轻贴、别动）"
        print(f"脉搏 PPG : ✅ 检测到 {beats.get('ppg',0)} 次心搏，hr_p {min(hrp):.0f}–{max(hrp):.0f}，{stab}"
              + (f"，rmssd_p≈{statistics.mean(rm):.0f}ms" if rm else ""))
    else:
        print(f"脉搏 PPG : ❌ 没检测到心搏（{beats.get('ppg',0)} 次）。手指轻贴传感器等 5 秒；查 GPIO35 与 3V3")
    if lead_ok:
        if hre:
            print(f"心电 ECG : ✅ 电极接触正常，{beats.get('ecg',0)} 次心搏，hr_e {min(hre):.0f}–{max(hre):.0f}")
        else:
            print("心电 ECG : ⚠️ 电极接触正常（lead_off=0）但没检测到 R 峰 → 试着对调红/绿电极；拔掉笔记本充电器")
    else:
        print("心电 ECG : ⏸ lead_off 一直为 1 → 电极没贴 / 没插线 / 模块没接。贴好三片电极后模块红灯应随心跳闪")
    src = "ECG" if hre else ("PPG" if hrp else "无")
    print(f"统一心率 : 当前来源 {src}（优先级 ECG > PPG）")
    print(f"quality  : 出现过的值 {sorted(set(col('quality')))}（7 = 心率+GSR+基线全就绪；基线需先发 calibrate）")


if __name__ == "__main__":
    main()
