#!/usr/bin/env python3
"""chartgen — 音乐节拍分析 → 节奏游戏谱面 JSON 生成器

分析一首歌的 BPM / 节拍 / 音符起始点（onset），生成符合本项目谱面格式
（ARCHITECTURE.md §3.6）的 chart JSON，供 Unity ChartLoader 读取。

tier 分级逻辑（对应游戏内 note_density 的过滤机制）：
    tier 1 = 小节强拍（每 4 拍的第 1 拍）→ 节奏骨架，任何难度都保留
    tier 2 = 其余正拍
    tier 3 = 不在正拍上的 onset（切分/装饰音）→ 高密度才出现

用法：
    python chartgen.py song.ogg                          # 生成 song.chart.json
    python chartgen.py song.ogg --out ../BioRhythmGame/Assets/Charts/song.json
    python chartgen.py song.ogg --plot                   # 另存谱面预览图 PNG
    python chartgen.py song.ogg --bpm 128                # 已知 BPM 时手动指定（更准）

依赖：pip install -r requirements.txt
注意：.ogg/.wav/.flac 直接支持；.mp3 在 Windows 上可能需要额外安装 ffmpeg。
"""

import argparse
import json
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):  # Windows 控制台默认编码可能打不出中文
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np

try:
    import librosa
except ImportError:
    sys.exit("缺少 librosa：请先执行  pip install -r requirements.txt")


def estimate_downbeat_phase(beat_times: np.ndarray, onset_env: np.ndarray,
                            times: np.ndarray) -> int:
    """估计小节强拍相位（0–3）：假设 4/4 拍，取 onset 能量总和最大的那一相。"""
    strengths = np.interp(beat_times, times, onset_env)
    best_phase, best_sum = 0, -1.0
    for phase in range(4):
        s = strengths[phase::4].sum()
        if s > best_sum:
            best_sum, best_phase = s, phase
    return best_phase


def assign_lanes(note_times_ms: list, centroids: np.ndarray,
                 cent_times: np.ndarray, seed: int = 42) -> list:
    """按频谱质心把音符分配到 4 轨：音高低→左轨，高→右轨，加防重复约束。

    这样低音鼓点偏左手、高频旋律偏右手，玩起来和听感对应——比纯随机手感好。
    """
    rng = np.random.default_rng(seed)
    vals = np.interp(np.array(note_times_ms) / 1000.0, cent_times, centroids)
    # 按全曲分位数切成 4 档 → 初始轨道
    qs = np.quantile(vals, [0.25, 0.5, 0.75])
    lanes = np.digitize(vals, qs).tolist()  # 0..3

    # 约束修正：避免同轨连打过多（>2 连）以及 <150ms 的同轨双击
    result = []
    for i, lane in enumerate(lanes):
        if i >= 1 and note_times_ms[i] - note_times_ms[i - 1] < 150 and lane == result[-1]:
            lane = (lane + rng.integers(1, 4)) % 4          # 太近的同轨 → 挪开
        if i >= 2 and lane == result[-1] == result[-2]:
            lane = (lane + (1 if rng.random() < 0.5 else 3)) % 4  # 3 连打 → 挪开
        result.append(int(lane))
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="音乐 → 谱面 JSON 生成器")
    ap.add_argument("audio", help="音频文件（推荐 .ogg / .wav）")
    ap.add_argument("--out", help="输出 JSON 路径（默认 <音频名>.chart.json）")
    ap.add_argument("--bpm", type=float, default=None, help="手动指定 BPM（跳过自动估计）")
    ap.add_argument("--lead-in", type=int, default=2000,
                    help="开头留白毫秒数，此前不放音符（默认 2000）")
    ap.add_argument("--min-gap", type=int, default=120,
                    help="任意两音符最小间隔毫秒（可玩性下限，默认 120）")
    ap.add_argument("--seed", type=int, default=42, help="轨道分配随机种子（同种子结果可复现）")
    ap.add_argument("--plot", action="store_true", help="另存谱面预览图 PNG")
    args = ap.parse_args()

    path = pathlib.Path(args.audio)
    print(f"加载音频 {path.name} ...")
    y, sr = librosa.load(str(path), mono=True)
    duration_ms = int(len(y) / sr * 1000)

    # ---- 节拍检测 ----
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    env_times = librosa.times_like(onset_env, sr=sr)
    if args.bpm:
        tempo, beat_frames = librosa.beat.beat_track(
            y=y, sr=sr, start_bpm=args.bpm, tightness=100)
    else:
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(np.atleast_1d(tempo)[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    print(f"估计 BPM = {tempo:.1f}，检测到 {len(beat_times)} 个节拍")

    # ---- 强拍相位（tier 1）----
    phase = estimate_downbeat_phase(beat_times, onset_env, env_times)

    # ---- onset 检测（tier 3 候选）----
    onset_times = librosa.onset.onset_detect(y=y, sr=sr, units="time",
                                             backtrack=False)

    # ---- 组装音符列表 ----
    notes = []  # (t_ms, tier)
    for i, bt in enumerate(beat_times):
        t_ms = int(bt * 1000)
        tier = 1 if (i - phase) % 4 == 0 else 2
        notes.append((t_ms, tier))

    beat_ms = np.array([n[0] for n in notes])
    for ot in onset_times:
        t_ms = int(ot * 1000)
        if beat_ms.size and np.abs(beat_ms - t_ms).min() < 90:
            continue  # 离正拍太近的 onset 不重复放
        notes.append((t_ms, 3))

    # 排序 + 开头留白 + 最小间隔过滤（保留 tier 小/更重要的那个）
    notes.sort(key=lambda n: (n[0], n[1]))
    filtered = []
    for t_ms, tier in notes:
        if t_ms < args.lead_in or t_ms > duration_ms - 500:
            continue
        if filtered and t_ms - filtered[-1][0] < args.min_gap:
            if tier < filtered[-1][1]:
                filtered[-1] = (t_ms, tier)  # 重要度更高则替换
            continue
        filtered.append((t_ms, tier))

    # ---- 轨道分配（频谱质心 → 音高感对应左右手）----
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    cent_times = librosa.times_like(cent, sr=sr)
    times_ms = [n[0] for n in filtered]
    lanes = assign_lanes(times_ms, cent, cent_times, seed=args.seed)

    # ---- 难度估计（按密度粗估 1–5）----
    nps = len(filtered) / max(duration_ms / 1000.0, 1)  # notes per second
    base_difficulty = int(np.clip(round(nps * 1.5), 1, 5))

    chart = {
        "bpm": round(tempo, 1),
        "offset_ms": 0,
        "base_difficulty": base_difficulty,
        "song_duration_ms": duration_ms,
        "source_audio": path.name,
        "notes": [
            {"t": t, "lane": lane, "type": "tap", "tier": tier}
            for (t, tier), lane in zip(filtered, lanes)
        ],
    }

    out = pathlib.Path(args.out) if args.out else path.with_suffix(".chart.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(chart, ensure_ascii=False, indent=1), encoding="utf-8")

    n_by_tier = {t: sum(1 for _, tt in filtered if tt == t) for t in (1, 2, 3)}
    print(f"已写出 {out}")
    print(f"  时长 {duration_ms/1000:.1f}s | 音符 {len(filtered)} 个 "
          f"(tier1 骨架 {n_by_tier[1]} / tier2 正拍 {n_by_tier[2]} / tier3 装饰 {n_by_tier[3]})")
    print(f"  平均密度 {nps:.2f} notes/s | base_difficulty = {base_difficulty}")

    # ---- 预览图 ----
    if args.plot:
        import matplotlib.pyplot as plt
        plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
        plt.rcParams["axes.unicode_minus"] = False
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6), sharex=True,
                                       gridspec_kw={"height_ratios": [1, 2]})
        t_audio = np.arange(len(y)) / sr
        step = max(1, len(y) // 20000)
        ax1.plot(t_audio[::step], y[::step], linewidth=0.4, color="gray")
        ax1.set_ylabel("waveform")
        colors = {1: "#d62728", 2: "#1f77b4", 3: "#bbbbbb"}
        sizes = {1: 40, 2: 22, 3: 10}
        for (t_ms, tier), lane in zip(filtered, lanes):
            ax2.scatter(t_ms / 1000.0, lane, c=colors[tier], s=sizes[tier])
        ax2.set_yticks([0, 1, 2, 3], ["D", "F", "J", "K"])
        ax2.set_xlabel("time (s)")
        ax2.set_ylabel("lane")
        ax2.set_title(f"{path.name} — BPM {tempo:.1f} — "
                      f"红=tier1骨架 蓝=tier2正拍 灰=tier3装饰")
        ax2.grid(alpha=0.3, axis="x")
        fig.tight_layout()
        png = out.with_suffix(".png")
        fig.savefig(png, dpi=130)
        print(f"预览图已存 {png}")


if __name__ == "__main__":
    main()
