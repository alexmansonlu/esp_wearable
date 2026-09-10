#!/usr/bin/env python3
"""
record.py — 采集一场数据：调用 firmware/tools/serial_logger.py 记录到 experiment/data_gathering/sessions/，
结束后（Ctrl+C）在终端问你几个标签问题，写进 sessions.csv。

用法：
    python experiment/data_gathering/record.py --port COM5 --tag osu_lv5
    python experiment/data_gathering/record.py --port /dev/cu.usbserial-1210 --tag rest --no-raw

流程：连上 → 自动发 calibrate（静坐 30 秒别动）→ 看到 calib done 后开始玩 → 玩完 Ctrl+C → 回答标签问题。
--tag 只用英文/数字/下划线，建议 <游戏>_<难度>，如 osu_lv5、pvz_hard、rest。
运行期间只能有一个程序占串口：先关掉 live_dashboard / Serial Monitor。
"""
import argparse
import csv
import datetime
import pathlib
import re
import shutil
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).resolve().parent                      # experiment/data_gathering/
REPO = HERE.parents[1]
LOGGER = REPO / "firmware" / "tools" / "serial_logger.py"
SESSIONS_DIR = HERE / "sessions"
TAGS_CSV = HERE / "sessions.csv"
TAG_COLUMNS = ["session_id", "date", "game", "level_difficulty", "bpm",
               "final_score", "big_mistake", "missed_beats", "tension_self", "notes"]

QUESTIONS = [  # (列名, 提示, 是否可留空)
    ("game", "游戏名（如 osu / 植物大战僵尸 / rest=静坐对照）", False),
    ("level_difficulty", "关卡难度 1–5（1 轻松 … 5 极难）", False),
    ("bpm", "游戏 BPM（节奏游戏填数字，其他游戏留空）", True),
    ("final_score", "最终分数 / 准确率（数字）", True),
    ("big_mistake", "有没有明显失误？1=有 0=没有", False),
    ("missed_beats", "漏拍 / 漏按次数（数字，不知道填 0）", True),
    ("tension_self", "你自己觉得这一场多紧张 1–5", False),
    ("notes", "备注（一句话：哪一段最紧张 / 发生了什么）", True),
]


def ask_tags(session_id: str) -> dict:
    print("\n=== 给这一场打标签（直接回车 = 留空）===")
    row = {"session_id": session_id, "date": datetime.date.today().isoformat()}
    for col, prompt, optional in QUESTIONS:
        while True:
            v = input(f"{prompt}: ").strip()
            if v or optional:
                break
            print("  这一项必填")
        row[col] = v
    return row


def append_tags(row: dict) -> None:
    new_file = not TAGS_CSV.exists() or TAGS_CSV.stat().st_size == 0
    with open(TAGS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=TAG_COLUMNS)
        if new_file:
            w.writeheader()
        w.writerow(row)
    print(f"标签已写入 {TAGS_CSV.relative_to(REPO)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="采集一场数据 + 打标签")
    ap.add_argument("--port", required=True, help="串口号，如 COM5 或 /dev/cu.usbserial-1210")
    ap.add_argument("--tag", required=True, help="场次标签，英文/数字/下划线，如 osu_lv5")
    ap.add_argument("--no-raw", action="store_true", help="不记录 100Hz 波形（文件更小）")
    ap.add_argument("--no-calibrate", action="store_true", help="不自动发 calibrate（一般不要用）")
    ap.add_argument("--skip-tags", action="store_true", help="结束后不问标签")
    args = ap.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9_]+", args.tag):
        raise SystemExit("--tag 只能用英文、数字、下划线，例如 osu_lv5")
    if not LOGGER.exists():
        raise SystemExit(f"找不到 {LOGGER}")
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, str(LOGGER), "--port", args.port, "--out", str(SESSIONS_DIR), "--tag", args.tag]
    if not args.no_calibrate:
        cmd.append("--calibrate")
    if not args.no_raw:
        cmd.append("--raw")

    before = {p.name for p in SESSIONS_DIR.iterdir() if p.is_dir()}
    print("开始记录。校准 30 秒内请静坐别动；玩完按 Ctrl+C 结束。\n")
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except KeyboardInterrupt:   # Ctrl+C 同时到达子进程，等它把文件关好
        proc.wait()

    new = sorted({p.name for p in SESSIONS_DIR.iterdir() if p.is_dir()} - before)
    if not new:
        raise SystemExit("没有生成新的 session 文件夹（串口没连上？）")
    session_id = new[-1]
    bio = SESSIONS_DIR / session_id / "bio.csv"
    if proc.returncode not in (0, None) or not bio.exists() or len(bio.read_text(encoding="utf-8").splitlines()) < 2:
        shutil.rmtree(SESSIONS_DIR / session_id, ignore_errors=True)   # 没记到数据的空文件夹不留
        raise SystemExit("这一场没有记录到数据（串口没连上 / 固件没输出），已删除空文件夹。"
                         "检查 --port 是否正确、Serial Monitor / live_dashboard 是否已关闭。")
    print(f"\n本场数据：{(SESSIONS_DIR / session_id).relative_to(REPO)}")

    if args.skip_tags:
        print(f"记得把 {session_id} 的标签补进 sessions.csv")
        return
    append_tags(ask_tags(session_id))
    print("\n下一步：python experiment/analysis/01_session_summary.py --session", session_id)


if __name__ == "__main__":
    main()
