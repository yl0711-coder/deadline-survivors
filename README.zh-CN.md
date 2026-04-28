# Deadline Survivors

[English](README.md) | 简体中文

[![Build](https://github.com/yl0711-coder/deadline-survivors/actions/workflows/build.yml/badge.svg)](https://github.com/yl0711-coder/deadline-survivors/actions/workflows/build.yml)
[![Latest Release](https://img.shields.io/github/v/release/yl0711-coder/deadline-survivors?label=release)](https://github.com/yl0711-coder/deadline-survivors/releases/latest)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

这是一个关于“程序员一边修 bug，一边躲会议、告警、需求膨胀、deadline 和线上故障”的本地单机街机生存小游戏。

不需要服务器，不需要账号，没有遥测统计。下载 zip，解压后就可以在本地玩。

## 为什么值得试玩

- 启动快：选择难度后直接开始一局短节奏生存挑战。
- 设定明确：Bug、会议、告警、需求膨胀、deadline 区域和 Production Outage 都是敌人或压力源。
- 局内有变化：升级、道具、Deploy Window、成就、badge、皮肤、本地历史记录和设置。
- 桌面端友好：提供 Windows、macOS Intel、macOS Apple Silicon、Linux 四种 Release 包。
- 开源可维护：使用 Python 和 `pygame-ce` 开发，包含测试、静态检查、重点模块类型检查、CI 和 Release 打包流程。

## 演示

![Deadline Survivors 玩法演示](assets/demo.gif)

## 截图

| 启动页 | 游戏中 |
| --- | --- |
| ![启动页](assets/screenshots/title.png) | ![游戏中](assets/screenshots/gameplay.png) |

| 升级选择 | 结算页 |
| --- | --- |
| ![升级选择](assets/screenshots/upgrade.png) | ![结算页](assets/screenshots/game-over.png) |

## 游玩

最简单的试玩方式是通过 itch.io 页面下载：

- [在 itch.io 下载 Deadline Survivors](https://yl0711.itch.io/deadline-survivors)

也可以从 [最新 GitHub Release](https://github.com/yl0711-coder/deadline-survivors/releases/latest) 下载对应系统的 zip 包：

- `deadline-survivors-windows.zip`
- `deadline-survivors-macos-intel.zip`
- `deadline-survivors-macos-apple-silicon.zip`
- `deadline-survivors-linux.zip`

Intel 芯片 Mac 使用 Intel 包，Apple Silicon 芯片 Mac 使用 Apple Silicon 包。

如果浏览器或系统提示“来自未知开发者”，这是未签名开源构建的正常现象。游戏不需要联网，设置、成就和历史记录都只保存在本地。

## 从源码运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 run_game.py
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py run_game.py
```

## 操作

- `WASD` 或方向键：移动
- `Enter` / `Space`：确认菜单操作
- `1`、`2`、`3`：选择难度或升级选项
- `A`：打开成就页
- `H`：打开本地历史记录
- `O`：打开设置页
- `B`：切换 badge
- `S`：切换角色皮肤
- `T`：切换 patch 主题色
- `P`：暂停 / 继续
- `Esc`：关闭菜单或退出

## 玩法

- 持续移动，躲避敌人和 deadline 区域。
- patch 会自动攻击附近威胁。
- 拾取 insight 碎片升级。
- 选择升级，形成本局 build。
- 拾取 Coffee Break、Refactor Bomb 和 CI Boost 救场。
- 抢占 Deploy Window，获得额外 insight、回血和 Focus Mode。
- 移动可以积累 Momentum，高 Momentum 会强化 patch 和拾取节奏。
- Production Outage 出现后要优先处理，否则会制造危险区并召唤支援敌人。
- 按 `H` 可以查看最近 10 局完成记录，数据只保存在本地。
- 按 `O` 可以开关音效、开关浮动文字，或二次确认后清空本地存档。

## 项目说明

项目使用：

- `pygame-ce`：窗口、输入、渲染、音频和游戏循环
- `PyInstaller`：生成 Windows、macOS、Linux 包
- GitHub Actions：测试、打包后二进制 smoke test 和 Release zip
- `ruff`：轻量静态检查
- `mypy`：对纯规则和工厂模块做重点类型检查

更多内容：

- [MANUAL.md](MANUAL.md)：完整玩家和维护手册
- [ARCHITECTURE.md](ARCHITECTURE.md)：代码结构和重构规则
- [README.md](README.md)：英文 README

## 反馈

欢迎提交问题和试玩反馈：

- [itch.io 页面](https://yl0711.itch.io/deadline-survivors)
- [反馈 bug](https://github.com/yl0711-coder/deadline-survivors/issues/new)
- [查看 Release](https://github.com/yl0711-coder/deadline-survivors/releases)
- [源码仓库](https://github.com/yl0711-coder/deadline-survivors)
