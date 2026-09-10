#!/usr/bin/env python3
"""
01_session_summary.py — 把每一场记录压缩成一行特征，并为每场画一张总览图。

用法：
    python experiment/analysis/01_session_summary.py                # 处理全部 session
    python experiment/analysis/01_session_summary.py --session session_20260911_1530_osu_lv5
    python experiment/analysis/01_session_summary.py --no-plot      # 只出表不画图

产出：
    results/summary/sessions_summary.csv          每场一行（反复运行会整表重生成）
    results/plots/<session_id>_overview.png       每场三联图：心率 / GSR 相对变化 / 运动量
"""
import argparse
import pathlib

import numpy as np
import pandas as pd

import common as C


def summarize(sdir: pathlib.Path) -> dict | None:
    bio = C.load_bio(sdir)
    if bio.empty:
        return None
    beats = C.load_beats(sdir)
    seq_gap = bio["seq"].diff().dropna()
    rmssd = bio["rmssd_p"].fillna(bio["rmssd_e"]) if "rmssd_e" in bio else bio["rmssd_p"]
    quality = bio["quality"].fillna(0).astype(int)
    return {
        "session_id": sdir.name,
        "duration_s": round(float(bio["t_s"].iloc[-1]), 1),
        "n_packets": int(len(bio)),
        "dropped_packets": int((seq_gap - 1).clip(lower=0).sum()),
        "baseline_ready_frac": round(float(((quality & 4) > 0).mean()), 3),
        "quality_ok_frac": round(float((quality == 7).mean()), 3),
        "hr_mean": round(float(bio["hr"].mean()), 1),
        "hr_max": round(float(bio["hr"].max()), 1),
        "hr_delta_mean": round(float(bio["hr_delta"].mean()), 2),
        "hr_delta_max": round(float(bio["hr_delta"].max()), 2),
        "rmssd_mean": round(float(rmssd.mean()), 1),
        "gsr_delta_mean": round(float(bio["gsr_delta"].mean()), 4),
        "gsr_delta_max": round(float(bio["gsr_delta"].max()), 4),
        "gsr_slope_pos_frac": round(float((bio["gsr_slope"] > 0).mean()), 3),
        "acc_mean": round(float(bio["acc"].mean()), 4),
        "acc_max": round(float(bio["acc"].max()), 3),
        "n_beats_ecg": int((beats["src"] == "ecg").sum()) if not beats.empty else 0,
        "n_beats_ppg": int((beats["src"] == "ppg").sum()) if not beats.empty else 0,
    }


def plot_overview(sdir: pathlib.Path, out: pathlib.Path) -> None:
    plt = C.setup_plot_style()
    bio = C.load_bio(sdir)
    t = bio["t_s"]
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    fig.suptitle(sdir.name)

    ax = axes[0]
    for col, label in [("hr", "统一心率 hr"), ("hr_p", "PulseSensor hr_p"), ("hr_e", "ECG hr_e")]:
        if col in bio and bio[col].notna().any():
            ax.plot(t, bio[col], label=label, color=C.SERIES_COLOR[col])
    ax.set_ylabel("心率 (bpm)")
    ax.margins(y=0.2)   # 顶部留空给图例，避免压住曲线
    ax.legend(loc="upper left", ncol=3, fontsize=8, frameon=False)

    ax = axes[1]
    ax.plot(t, bio["gsr_delta"] * 100, color=C.SERIES_COLOR["gsr_delta"])
    ax.axhline(0, color="#52514e", linewidth=0.8)
    ax.set_ylabel("GSR 相对基线 (%)")
    calib = ((bio["quality"].fillna(0).astype(int) & 4) > 0)
    if calib.any() and not calib.all():
        ax.axvline(t[calib.idxmax()], color="#52514e", linestyle="--", linewidth=0.8)
        ax.text(t[calib.idxmax()], ax.get_ylim()[1], " 基线就绪", va="top", fontsize=8, color="#52514e")

    ax = axes[2]
    ax.plot(t, bio["acc"], color=C.SERIES_COLOR["acc"])
    ax.axhline(0.8, color="#e34948", linewidth=0.8, linestyle=":")
    ax.text(t.iloc[-1], 0.8, "运动门控 0.8g ", ha="right", va="bottom", fontsize=8, color="#e34948")
    ax.set_ylabel("运动量 (g)")
    ax.set_xlabel("时间 (秒)")

    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description="每场记录 → 一行特征 + 一张总览图")
    ap.add_argument("--session", help="只处理这一个 session_id（文件夹名）")
    ap.add_argument("--no-plot", action="store_true")
    ap.add_argument("--sessions-dir", default=str(C.SESSIONS_DIR))
    ap.add_argument("--results-dir", default=str(C.RESULTS_DIR))
    args = ap.parse_args()
    sessions_dir, results_dir = pathlib.Path(args.sessions_dir), pathlib.Path(args.results_dir)

    sdirs = C.list_sessions(sessions_dir)
    if args.session:
        sdirs = [d for d in sdirs if d.name == args.session]
    if not sdirs:
        raise SystemExit(f"在 {sessions_dir} 下没找到 session（需要含 bio.csv 的文件夹）")

    rows = []
    for sdir in sdirs:
        row = summarize(sdir)
        if row is None:
            print(f"跳过（bio.csv 为空）: {sdir.name}")
            continue
        rows.append(row)
        if not args.no_plot:
            out = C.result_path("plots", f"{sdir.name}_overview", "png", dated=False, results_dir=results_dir)
            plot_overview(sdir, out)
            print(f"图  → {out.relative_to(results_dir.parent)}")

    df = pd.DataFrame(rows)
    out_csv = C.result_path("summary", "sessions_summary", "csv", dated=False, results_dir=results_dir)
    if args.session and out_csv.exists():   # 单场模式：更新那一行，不丢其他场
        old = pd.read_csv(out_csv, dtype={"session_id": str})
        df = pd.concat([old[~old["session_id"].isin(df["session_id"])], df]).sort_values("session_id")
    df.to_csv(out_csv, index=False)
    print(f"表  → {out_csv.relative_to(results_dir.parent)}  （{len(df)} 场）")
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print(df[["session_id", "duration_s", "quality_ok_frac", "hr_mean", "hr_delta_mean",
                  "rmssd_mean", "gsr_delta_mean", "gsr_delta_max", "acc_mean"]].to_string(index=False))


if __name__ == "__main__":
    main()
