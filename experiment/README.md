# experiment/ — 数据采集与分析

> 从 L1 起，所有佩戴采集的数据、分析代码、分析结果都放这里。三个文件夹各司其职，**结构和命名规范不要改**——后面每一次分析、每一次答辩、最后的报告都靠它们互相对得上。

```
experiment/
├── README.md                    ← 本文件：结构、流程、命名规范
├── data_gathering/              ← ① 原始数据（只增不改）
│   ├── record.py                  采集一场：连串口 → 校准 → 记录 → Ctrl+C → 问标签
│   ├── sessions.csv               每场一行的标签表（游戏 / 难度 / 分数 / 失误 / 主观紧张……）
│   └── sessions/
│       └── session_20260911_153000_osu_lv5/     一场 = 一个文件夹（名字就是 session_id；整个 sessions/ 不入 git）
│           ├── bio.csv       10 Hz 特征流（hr / hr_delta / rmssd / gsr_delta / gsr_slope / acc / quality…）
│           ├── beats.csv     逐跳心搏（src = ecg / ppg，ibi 毫秒）
│           ├── raw.csv       100 Hz 波形（ECG / PPG / GSR 原始 ADC）
│           └── log.txt       boot / calib / 异常行
├── analysis/                    ← ② 分析代码（只读 data_gathering/，只写 results/）
│   ├── common.py                  读取 / 路径 / 画图设置，所有脚本 import 它
│   ├── 01_session_summary.py      每场 → 一行特征 + 一张总览图
│   ├── 02_tag_correlation.py      特征 × 标签 的相关系数（热图 + 散点）
│   └── prompts.md                 让 AI 帮你分析时用的提示词模板
└── results/                     ← ③ 分析产物（可以随时删掉重生成）
    ├── summary/                   汇总表：sessions_summary.csv
    ├── plots/                     每场的图：<session_id>_overview.png
    ├── correlation/               相关分析：<日期>_tag_correlation.csv / .png、<日期>_top_pairs.png
    └── reports/                   你写的结论：<日期>_<主题>.md（如 20260915_L1_homework.md）
```

## Python 环境（第一次做一遍，Mac / Windows 都一样）

在仓库根目录建一个专属的虚拟环境 `venv`，之后所有脚本都在里面跑，不污染系统 Python。

**Mac**（终端；先装好 python.org 的 Python 3.11 或 3.12）
```bash
cd ~/Desktop/esp_wearable            # 换成你 clone 到的路径
python3 -m venv venv                 # 建虚拟环境（只做一次）
source venv/bin/activate             # 激活：提示符前面出现 (venv)
python -m pip install --upgrade pip
pip install -r requirements.txt      # 装 pyserial / numpy / pandas / matplotlib
python -c "import serial, pandas, matplotlib, numpy; print('ok')"   # 打印 ok 就装好了
ls /dev/cu.usbserial-*               # 插上 ESP32 后找串口名，填给 --port
```

**Windows**（PowerShell）
```powershell
cd Desktop\esp_wearable
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -c "import serial, pandas, matplotlib, numpy; print('ok')"
```
串口名在设备管理器里看（`COM5` 之类）。

之后每次开新终端都要先 `source venv/bin/activate`（Windows：`venv\Scripts\activate`）。VSCode 里按 `Cmd+Shift+P` → "Python: Select Interpreter" → 选 `venv` 里的那个，Codex 跑脚本就会用它。让 AI 装东西时说"装进本项目的 venv，不要装到系统 Python"。

## 采一场数据（标准流程）

1. 戴好：GSR 指套 + PulseSensor 在**不按键的手**，ECG 三片电极（可选），MPU6050 在 PulseSensor 那只手背
2. 关掉所有占串口的程序（live_dashboard、Serial Monitor）
3. 运行（`--tag` 用英文，建议 `<游戏>_<难度>`）：
   ```bash
   python experiment/data_gathering/record.py --port COM5 --tag osu_lv5
   ```
4. 看到 `calib started` 后**静坐 30 秒别动、别说话**，看到 `calib done` 再开始玩
5. 玩完一关 / 一首 → `Ctrl+C` → 回答终端里的标签问题（游戏、难度、BPM、分数、失误、漏拍、主观紧张）
6. 每天最后跑一次汇总，看图：
   ```bash
   python experiment/analysis/01_session_summary.py
   ```

**为什么每场都要校准**：一切生理特征用的是"相对基线的变化量"（`gsr_delta = (当前 − 基线) / 基线`，`hr_delta = 当前 − 基线`）。基线来自这 30 秒静坐的平均值；今天的手汗、电极贴合度和昨天不一样，所以基线每场重做。校准没完成时 `quality` 的 bit2 = 0，`gsr_delta` 和 `hr_delta` 全是 0，那一场等于白采。

## 命名规范

| 东西 | 规则 | 例子 |
|---|---|---|
| session 文件夹（= session_id） | `session_<YYYYMMDD>_<HHMMSS>_<tag>`，record.py 自动生成 | `session_20260911_153000_osu_lv5` |
| `--tag` | 英文 / 数字 / 下划线；`<游戏>_<难度>`；静坐对照用 `rest` | `osu_lv5`、`pvz_hard`、`rest` |
| sessions.csv 列 | 固定 10 列，不加不减：`session_id, date, game, level_difficulty, bpm, final_score, big_mistake, missed_beats, tension_self, notes` | 见 `analysis/common.py` 的 `TAG_COLUMNS` |
| 分析脚本 | `NN_动词_对象.py`，NN 两位数按依赖顺序；新脚本 import `common.py` | `03_compare_games.py` |
| 结果文件 | `results/<类别>/<YYYYMMDD>_<名字>.<ext>`；每场一张的图用 `<session_id>_<名字>.png`；会整表重生成的汇总表不加日期 | `20260915_tag_correlation.png`、`session_..._overview.png`、`sessions_summary.csv` |
| 报告 | `results/reports/<YYYYMMDD>_<主题>.md`，里面用相对路径引用图 | `20260915_L1_homework.md` |

规则只有三条：**data_gathering/ 只增不改**；**analysis/ 只写 results/**；**results/ 里的东西都能删掉重跑出来**。

## 标签怎么打

| 列 | 填什么 |
|---|---|
| `game` | 游戏名；静坐对照写 `rest` |
| `level_difficulty` | 1–5，自己定义但**同一个游戏内要一致** |
| `bpm` | 节奏游戏填曲子 BPM；别的游戏留空 |
| `final_score` | 分数或准确率，数字 |
| `big_mistake` | 这一场有没有一次"啊！"的明显失误：1 / 0 |
| `missed_beats` | 漏拍 / 漏按次数；不知道填 0 |
| `tension_self` | 玩完立刻凭感觉打 1–5 |
| `notes` | 一句话，哪一段最紧张、发生了什么——这一列是以后看图对照的线索 |

## 入库约定

- `data_gathering/sessions/` 里的原始数据**不入 git**（.gitignore 已排除）：留在本地，定期复制到网盘/移动硬盘备份
- 入 git 的是：`sessions.csv` 标签表、`analysis/` 代码、`results/` 全部产物（汇总表、图、报告）——这些是作业交付物，答辩看这些
