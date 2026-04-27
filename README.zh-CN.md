# Deadline Survivors

[English](README.md) | 简体中文

这是一个使用 Python 和 `pygame-ce` 开发的本地单机街机生存小游戏。

玩家扮演一名后端工程师，一边自动发出 patch，一边在 Bug、会议、告警、需求膨胀、deadline 区域和线上故障中尽量活下来。

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

可以从 GitHub Releases 下载对应系统的 zip 包：

- `deadline-survivors-windows.zip`
- `deadline-survivors-macos-intel.zip`
- `deadline-survivors-macos-apple-silicon.zip`
- `deadline-survivors-linux.zip`

Intel 芯片 Mac 使用 Intel 包，Apple Silicon 芯片 Mac 使用 Apple Silicon 包。

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

更多内容：

- [MANUAL.md](MANUAL.md)：完整玩家和维护手册
- [ARCHITECTURE.md](ARCHITECTURE.md)：代码结构和重构规则
- [README.md](README.md)：英文 README
