# unity/tools — 谱面工具

## chartgen.py — 音乐 → 谱面 JSON

分析音乐的 BPM、节拍与 onset，自动生成本项目格式的谱面（含 tier 密度分级），供 Unity `ChartLoader` 读取。

```bash
pip install -r requirements.txt

python chartgen.py 歌.ogg --plot                # 生成 歌.chart.json + 预览图 PNG
python chartgen.py 歌.ogg --bpm 128             # 已知 BPM 时指定，检测更准
python chartgen.py 歌.ogg --out ../BioRhythmGame/Assets/Charts/song1.json
```

**工作原理**（也是好的教学素材）：
1. librosa 节拍追踪 → BPM + 每一拍的时刻
2. 强拍相位估计（onset 能量最大的一相）→ 每小节第 1 拍标为 **tier 1**（骨架），其余正拍 **tier 2**
3. onset 检测找出不在正拍上的音头 → **tier 3**（装饰音，高密度才出现）
4. 频谱质心分轨：低音偏左轨（D/F）、高音偏右轨（J/K），加"防同轨连打"约束
5. 开头 2 秒留白 + 最小间隔 120ms 过滤，保证可玩性

**注意事项**：
- 音频格式推荐 `.ogg` / `.wav`（`.mp3` 在 Windows 可能需要另装 ffmpeg）
- 自动检测的 BPM 偏差大时（切分多的歌常见），用 `--bpm` 手动指定
- 生成的是**初稿**：先用 `--plot` 看分布，进 Unity 试玩后手动微调 JSON（删/挪个别音符）是正常工作流
- 同一 `--seed` 结果完全可复现（实验需要固定谱面时别改 seed）

**输出格式**（对应 ARCHITECTURE.md §3.6）：

```json
{
  "bpm": 120.0,
  "offset_ms": 0,
  "base_difficulty": 3,
  "song_duration_ms": 30000,
  "source_audio": "song.ogg",
  "notes": [ {"t": 2020, "lane": 0, "type": "tap", "tier": 2}, ... ]
}
```

`t` 为相对音频起点的毫秒；`lane` 0–3 对应 D/F/J/K；`tier` 与游戏内 `note_density` 联动（密度低时只保留小 tier）。

已验证：合成 120 BPM 测试音轨 → 110 音符 / 三档 tier / 无同轨密集连打（2026-09-03）。
