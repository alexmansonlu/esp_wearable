#!/usr/bin/env python3
"""快速可视化一个 session 的记录数据。

用法：
    python plot_session.py data/session_20260902_150000_P01

产出四联图（心率对比 / HRV / GSR / 运动量），保存为 session 目录下的 summary.png 并弹窗显示。
若存在 raw.csv 且非空，另绘最后 15 秒的 ECG/PPG 波形图 waveform.png。
"""

import argparse
import pathlib
import sys

import pandas as pd
import matplotlib.pyplot as plt


def load_csv(path: pathlib.Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("session", help="session 文件夹路径")
    args = ap.parse_args()
    sdir = pathlib.Path(args.session)
    bio = load_csv(sdir / "bio.csv")
    if bio.empty:
        sys.exit(f"{sdir}/bio.csv 不存在或为空")

    t = (bio["t"] - bio["t"].iloc[0]) / 1000.0  # 秒，相对起点

    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    fig.suptitle(f"Session: {sdir.name}")

    # 1) 三路心率对比
    ax = axes[0]
    for col, label in [("hr", "fused HR"), ("hr_p", "PulseSensor"),
                       ("hr_e", "AD8232 ECG"), ("hr_m", "MAX30100")]:
        if col in bio:
            v = bio[col].where(bio[col] > 0)  # -1 视为无效
            ax.plot(t, v, label=label, linewidth=1)
    ax.set_ylabel("HR (bpm)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.3)

    # 2) HRV (RMSSD)
    ax = axes[1]
    for col, label in [("rmssd_p", "RMSSD (PPG)"), ("rmssd_e", "RMSSD (ECG)")]:
        if col in bio:
            v = bio[col].where(bio[col] > 0)
            ax.plot(t, v, label=label, linewidth=1)
    ax.set_ylabel("RMSSD (ms)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.3)

    # 3) GSR
    ax = axes[2]
    ax.plot(t, bio["gsr"], label="GSR (smoothed ADC)", linewidth=1)
    if "gsr_slope" in bio:
        ax2 = ax.twinx()
        ax2.plot(t, bio["gsr_slope"], color="tab:orange", alpha=0.5,
                 linewidth=0.8, label="slope")
        ax2.set_ylabel("slope (counts/s)", fontsize=8)
    ax.set_ylabel("GSR")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)

    # 4) 运动量 + 质量位
    ax = axes[3]
    ax.plot(t, bio["acc"], label="motion (g)", linewidth=1)
    if "lead_off" in bio:
        ax.fill_between(t, 0, bio["lead_off"] * bio["acc"].max() if bio["acc"].max() > 0 else bio["lead_off"],
                        alpha=0.15, color="red", label="ECG lead off")
    ax.set_ylabel("acc (g)")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.3)

    fig.tight_layout()
    out = sdir / "summary.png"
    fig.savefig(out, dpi=130)
    print(f"已保存 {out}")

    # 波形图（最后 15 秒）
    raw = load_csv(sdir / "raw.csv")
    if not raw.empty:
        raw["sec"] = (raw["t"] - raw["t"].iloc[0]) / 1000.0
        tail = raw[raw["sec"] >= raw["sec"].max() - 15]
        fig2, (a1, a2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
        a1.plot(tail["sec"], tail["ecg"], linewidth=0.6)
        a1.set_ylabel("ECG (ADC)")
        a1.grid(alpha=0.3)
        a2.plot(tail["sec"], tail["pulse"], linewidth=0.6, color="tab:green")
        a2.set_ylabel("PPG (ADC)")
        a2.set_xlabel("time (s)")
        a2.grid(alpha=0.3)
        fig2.suptitle("最后 15 秒波形（ECG 应见规律尖峰 R 波；PPG 应见圆润脉搏波）")
        fig2.tight_layout()
        out2 = sdir / "waveform.png"
        fig2.savefig(out2, dpi=130)
        print(f"已保存 {out2}")

    plt.show()


if __name__ == "__main__":
    main()
