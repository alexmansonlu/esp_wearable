#!/usr/bin/env python3
"""
02_tag_correlation.py — 把每场的生理特征和你打的标签（难度 / BPM / 分数 / 失误……）放在一起，
算 Spearman 相关系数，看"越紧张的场，生理信号是不是也越高"。

先跑 01_session_summary.py 生成 results/summary/sessions_summary.csv，
并确认 data_gathering/sessions.csv 里每一场都填了标签。

用法：
    python experiment/analysis/02_tag_correlation.py
    python experiment/analysis/02_tag_correlation.py --min-sessions 4

产出（文件名带当天日期）：
    results/correlation/<YYYYMMDD>_tag_correlation.csv   长表：tag, feature, spearman_r, n
    results/correlation/<YYYYMMDD>_tag_correlation.png   热图（蓝=负相关，橙=正相关）
    results/correlation/<YYYYMMDD>_top_pairs.png         相关最强的 4 对散点图

注意：场次少（N < 8）时相关系数很不稳定，一两场极端值就能把 r 拉到 0.8。
      把它当"值得进一步看的线索"，不要当结论。
"""
import argparse
import pathlib

import numpy as np
import pandas as pd

import common as C

FEATURES = ["hr_mean", "hr_delta_mean", "hr_delta_max", "rmssd_mean",
            "gsr_delta_mean", "gsr_delta_max", "gsr_slope_pos_frac", "acc_mean"]
TAG_LABEL = {"level_difficulty": "关卡难度", "bpm": "游戏 BPM", "final_score": "最终分数",
             "big_mistake": "明显失误(0/1)", "missed_beats": "漏拍数", "tension_self": "主观紧张(1-5)"}
FEATURE_LABEL = {"hr_mean": "平均心率", "hr_delta_mean": "心率相对基线(均值)", "hr_delta_max": "心率相对基线(最大)",
                 "rmssd_mean": "RMSSD(HRV)", "gsr_delta_mean": "GSR相对基线(均值)", "gsr_delta_max": "GSR相对基线(最大)",
                 "gsr_slope_pos_frac": "GSR上升时间占比", "acc_mean": "平均运动量"}


def main() -> None:
    ap = argparse.ArgumentParser(description="生理特征 × 标签 的 Spearman 相关")
    ap.add_argument("--min-sessions", type=int, default=3, help="少于这个场数不算相关（默认 3）")
    ap.add_argument("--tags-csv", default=str(C.TAGS_CSV))
    ap.add_argument("--results-dir", default=str(C.RESULTS_DIR))
    args = ap.parse_args()
    results_dir = pathlib.Path(args.results_dir)

    summary_csv = results_dir / "summary" / "sessions_summary.csv"
    if not summary_csv.exists():
        raise SystemExit("先运行 01_session_summary.py 生成 results/summary/sessions_summary.csv")
    summary = pd.read_csv(summary_csv, dtype={"session_id": str})
    tags = C.load_tags(pathlib.Path(args.tags_csv))
    df = summary.merge(tags, on="session_id", how="inner")
    missing = set(summary["session_id"]) - set(tags["session_id"])
    if missing:
        print(f"⚠ 这些场在 sessions.csv 里没有标签，已跳过：{sorted(missing)}")
    if len(df) < args.min_sessions:
        raise SystemExit(f"只有 {len(df)} 场同时有数据和标签，少于 {args.min_sessions}，先多采几场")

    rows = []
    for tag in C.NUMERIC_TAGS:
        if tag not in df or df[tag].notna().sum() < args.min_sessions or df[tag].nunique() < 2:
            continue
        for feat in FEATURES:
            pair = df[[tag, feat]].dropna()
            if len(pair) < args.min_sessions or pair[feat].nunique() < 2:
                continue
            r = pair[tag].corr(pair[feat], method="spearman")
            rows.append({"tag": tag, "feature": feat, "spearman_r": round(float(r), 3), "n": len(pair)})
    if not rows:
        raise SystemExit("没有可算的标签列（每个标签至少要有 3 场、且数值不能全相同）")
    res = pd.DataFrame(rows)

    out_csv = C.result_path("correlation", "tag_correlation", "csv", results_dir=results_dir)
    res.to_csv(out_csv, index=False)
    print(f"表 → {out_csv.relative_to(results_dir.parent)}")
    pivot = res.pivot(index="feature", columns="tag", values="spearman_r").reindex(FEATURES)
    print(pivot.rename(index=FEATURE_LABEL, columns=TAG_LABEL).to_string())
    print(f"\n共 {len(df)} 场。" + ("场次 < 8，以上系数只当线索，不当结论。" if len(df) < 8 else ""))

    plt = C.setup_plot_style()
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("div", list(C.DIVERGING))

    # 热图
    fig, ax = plt.subplots(figsize=(1.6 * len(pivot.columns) + 4, 0.55 * len(pivot.index) + 2))
    im = ax.imshow(pivot.values.astype(float), cmap=cmap, vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), [TAG_LABEL.get(c, c) for c in pivot.columns], rotation=20, ha="right")
    ax.set_yticks(range(len(pivot.index)), [FEATURE_LABEL.get(i, i) for i in pivot.index])
    ax.grid(False)
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            v = pivot.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:+.2f}", ha="center", va="center", fontsize=9, color="#0b0b0b")
    fig.colorbar(im, ax=ax, label="Spearman r（-1 负相关 ... +1 正相关）", shrink=0.8)
    ax.set_title(f"生理特征 × 标签 相关系数（N = {len(df)} 场）")
    fig.tight_layout()
    out_png = C.result_path("correlation", "tag_correlation", "png", results_dir=results_dir)
    fig.savefig(out_png, dpi=130)
    plt.close(fig)
    print(f"图 → {out_png.relative_to(results_dir.parent)}")

    # 相关最强的 4 对散点
    top = res.reindex(res["spearman_r"].abs().sort_values(ascending=False).index).head(4)
    fig, axes = plt.subplots(1, len(top), figsize=(4.2 * len(top), 3.8))
    axes = np.atleast_1d(axes)
    for ax, (_, r) in zip(axes, top.iterrows()):
        pair = df[[r["tag"], r["feature"], "session_id"]].dropna()
        ax.scatter(pair[r["tag"]], pair[r["feature"]], s=40, color=C.SERIES_COLOR["hr"], edgecolor="white", linewidth=1)
        ax.set_xlabel(TAG_LABEL.get(r["tag"], r["tag"]))
        ax.set_ylabel(FEATURE_LABEL.get(r["feature"], r["feature"]))
        ax.set_title(f"r = {r['spearman_r']:+.2f}  (n={r['n']})", fontsize=10)
    fig.tight_layout()
    out_png2 = C.result_path("correlation", "top_pairs", "png", results_dir=results_dir)
    fig.savefig(out_png2, dpi=130)
    plt.close(fig)
    print(f"图 → {out_png2.relative_to(results_dir.parent)}")


if __name__ == "__main__":
    main()
