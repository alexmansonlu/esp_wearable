# 让 AI 帮你分析数据 — 提示词模板

> 用法：在 VSCode 打开本仓库，Codex 侧栏里把模板整段粘贴，【】里的换成你的。**每次 AI 写完代码或给出结论，都追问一句"逐段解释 / 你怎么得出的"**——这是答辩弹药。
> 先读 `experiment/README.md` 的命名规范；让 AI 写新脚本时把规范一起贴给它。

## P0 先让它读懂数据长什么样

```
我是零基础学生。请读 experiment/README.md 和 experiment/analysis/common.py，
然后打开 experiment/data_gathering/sessions/【session_id】/bio.csv，
用一张表告诉我每一列是什么意思、单位、正常范围、-1 或 0 代表什么。
再告诉我 quality 这一列的 7 是怎么来的。
```

## P1 跑现有脚本，看一场

```
帮我运行 python experiment/analysis/01_session_summary.py --session 【session_id】，
把生成的 results/plots/【session_id】_overview.png 打开，
用三句话描述：心率什么时候升高、GSR 相对基线什么时候爬升、有没有运动伪影（acc > 0.8g）。
然后对照 experiment/data_gathering/sessions.csv 里这一场的 notes，看图上的时间点和我记的对不对得上。
```

## P2 相关性：生理信号和标签有没有关系

```
我采了【N】场游戏数据，标签在 experiment/data_gathering/sessions.csv，
每场的生理特征在 experiment/results/summary/sessions_summary.csv（先跑 01_session_summary.py）。
请运行 python experiment/analysis/02_tag_correlation.py，然后回答：
1. 关卡难度、BPM、最终分数、明显失误、漏拍、主观紧张，各自和 gsr_delta_mean / hr_delta_mean / rmssd_mean 的 Spearman 相关系数是多少？
2. 哪些是正相关（难度越高信号越高）、哪些是负相关？RMSSD 应该和紧张是什么方向？
3. 只有【N】场，这些系数可信吗？多少场才够？举一个"一场极端值把 r 拉高"的例子。
4. 用我能听懂的话解释 Spearman 和 Pearson 的区别，为什么这里用 Spearman。
```

## P3 让它写一个新的小分析（保持规范）

```
请在 experiment/analysis/ 下新写 03_【动词_对象】.py，规则：
- import common.py 的 load_bio / list_sessions / result_path / setup_plot_style
- 只读 data_gathering/，只写 results/【类别】/，文件名按 README 命名规范
- 做的事：【例：把每一场按"校准后前 60 秒 / 中间 / 最后 60 秒"切三段，比较三段的 gsr_delta 均值，画成分组柱状图】
写完后逐段解释代码，并告诉我怎么验证它算对了（比如拿一场手算一个数对一下）。
```

## P4 质疑它（答辩常考）

```
你刚才说【难度和 GSR 正相关】。请给我三个"其实不是因为紧张"的替代解释
（提示：运动伪影、电极松了、时间顺序、我玩的顺序），
以及每一个替代解释我可以用数据里的哪一列来排除。
```

## P5 出题考自己

```
针对 01_session_summary.py 和 02_tag_correlation.py，出 8 道预测题
（"如果把 gsr_delta 的基线换成全场平均，图会怎么变"这种），
我先答，你再批改并打分。
```

## 写结论时的格式（放 results/reports/<日期>_<主题>.md）

```
# 【主题】
采了几场、哪些游戏、每场多长
## 看到了什么（贴图，相对路径 ../plots/…）
## 相关性表（贴 02 的输出）
## 我的判断：哪些像真的、哪些不可信、为什么
## 下次要改的采集方式
```
