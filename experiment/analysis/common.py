#!/usr/bin/env python3
"""
common.py — 所有分析脚本共用的读取 / 路径 / 画图设置。

约定（详见 experiment/README.md）：
    experiment/data_gathering/sessions/<session_id>/   一场记录（bio.csv / beats.csv / raw.csv / log.txt）
    experiment/data_gathering/sessions.csv             每场的标签（游戏、难度、分数……），session_id 对应文件夹名
    experiment/results/<类别>/<YYYYMMDD>_<名字>.<ext>  分析产物；脚本只写 results/，绝不改 data_gathering/
"""
import datetime
import pathlib
import sys

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):  # Windows 控制台默认编码可能打不出中文
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parents[1]          # experiment/
SESSIONS_DIR = ROOT / "data_gathering" / "sessions"
TAGS_CSV = ROOT / "data_gathering" / "sessions.csv"
RESULTS_DIR = ROOT / "results"

# sessions.csv 的固定列（record.py 写、02_tag_correlation.py 读）
TAG_COLUMNS = ["session_id", "date", "game", "level_difficulty", "bpm",
               "final_score", "big_mistake", "missed_beats", "tension_self", "notes"]
NUMERIC_TAGS = ["level_difficulty", "bpm", "final_score", "big_mistake", "missed_beats", "tension_self"]

# bio.csv 里 -1 代表"无效"，读入时统一换成 NaN 的列
INVALID_MINUS_ONE = ["hr", "hr_p", "hr_e", "hr_m", "rmssd_p", "rmssd_e"]

# 画图：固定的系列颜色（同一个量在所有图里永远同一个颜色）
SERIES_COLOR = {
    "hr": "#2a78d6",        # 统一心率
    "hr_p": "#eb6834",      # PulseSensor
    "hr_e": "#1baf7a",      # AD8232 ECG
    "gsr_delta": "#eda100",
    "rmssd": "#4a3aa7",
    "acc": "#52514e",
}
DIVERGING = ("#2a78d6", "#f0efec", "#eb6834")   # 相关系数热图：负 / 零 / 正


CJK_FONT_CANDIDATES = ["PingFang SC", "Hiragino Sans GB", "Heiti SC", "Arial Unicode MS",   # macOS
                       "Microsoft YaHei", "SimHei",                                          # Windows
                       "Noto Sans CJK SC", "WenQuanYi Micro Hei"]                            # Linux


def pick_cjk_font() -> list[str]:
    """返回本机装了的中文字体（按优先级），找不到就退回 DejaVu Sans（中文会变方块但不报错）。"""
    from matplotlib import font_manager
    installed = {f.name for f in font_manager.fontManager.ttflist}
    found = [n for n in CJK_FONT_CANDIDATES if n in installed]
    return found + ["DejaVu Sans"]


def setup_plot_style():
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = pick_cjk_font()
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.spines.right"] = False
    plt.rcParams["axes.grid"] = True
    plt.rcParams["grid.alpha"] = 0.25
    plt.rcParams["lines.linewidth"] = 1.2
    return plt


def list_sessions(sessions_dir: pathlib.Path = SESSIONS_DIR) -> list[pathlib.Path]:
    """按名字排序返回所有含 bio.csv 的 session 文件夹。"""
    if not sessions_dir.exists():
        return []
    return sorted(p for p in sessions_dir.iterdir() if p.is_dir() and (p / "bio.csv").exists())


def load_bio(session_dir: pathlib.Path) -> pd.DataFrame:
    """读一场的 10Hz 特征流。加一列 t_s（相对开始的秒数）；-1 无效值换成 NaN。"""
    path = session_dir / "bio.csv"
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty:
        return df
    for c in INVALID_MINUS_ONE:
        if c in df:
            df[c] = df[c].where(df[c] > 0)
    df["t_s"] = (df["t"] - df["t"].iloc[0]) / 1000.0
    return df


def load_beats(session_dir: pathlib.Path) -> pd.DataFrame:
    path = session_dir / "beats.csv"
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=["host_ts", "t", "src", "ibi"])
    return pd.read_csv(path)


def load_tags(tags_csv: pathlib.Path = TAGS_CSV) -> pd.DataFrame:
    if not tags_csv.exists():
        return pd.DataFrame(columns=TAG_COLUMNS)
    df = pd.read_csv(tags_csv, dtype={"session_id": str})
    for c in NUMERIC_TAGS:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def result_path(category: str, name: str, ext: str, dated: bool = True,
                results_dir: pathlib.Path = RESULTS_DIR) -> pathlib.Path:
    """results/<category>/<YYYYMMDD>_<name>.<ext>（dated=False 时不加日期，用于会反复重生成的汇总表）。"""
    d = results_dir / category
    d.mkdir(parents=True, exist_ok=True)
    stem = f"{datetime.date.today():%Y%m%d}_{name}" if dated else name
    return d / f"{stem}.{ext}"
