# AGENTS.md — 给 Codex / 其他 AI 编程助手的项目说明

> 本项目的全部上下文在 [CLAUDE.md](CLAUDE.md)。**开始任何任务前先完整读一遍 CLAUDE.md**，再按它的"核心文档地图"读需要的文档。

## 必守规则（摘要，细节见 CLAUDE.md）

- 文档一律简体中文；给学生的材料假设零编程基础，多用比喻，给可直接复制的提示词
- 硬件定稿 v0.4：PulseSensor（GPIO35）+ AD8232（GPIO32，LO± 27/14）+ 思知瑞 GSR（GPIO34，必须 3.3V）+ MPU6050（I2C 0x68）+ 裸 MAX30100（选配，默认停用）。**不要再提 Grove GSR / MAX30102 / LIS2DH**
- 已定案的设计决策（传输选型、双时间尺度、状态规则、难度调整、对照组实验、相对基线）不要重新讨论
- 固件在 [firmware/](firmware/)（PlatformIO），串口协议见 firmware/README.md；上机步骤见 [WIRING.md](WIRING.md)
- 学生作业以 git commit 交付，提交信息由学生自己写；帮学生写代码后**必须逐段解释**
