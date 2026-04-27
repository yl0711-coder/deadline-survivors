# Deadline Survivors

[English](README.md) | 简体中文

这是一个使用 Python 和 `pygame-ce` 开发的本地单机动作小游戏。

玩家扮演一名后端工程师，在一波又一波的：

- Bug
- 会议
- 告警
- 需求膨胀

之中尽量活下来。

项目只面向本地运行：

- 从 GitHub clone 下来
- 直接运行源码
- 或下载对应系统的二进制包

## 为什么选这个技术栈

项目使用两个成熟的开源组件：

- `pygame-ce`：负责窗口、输入、渲染、音频和游戏循环
- `PyInstaller`：负责打包可分发的二进制文件

这样既方便快速开发，也方便后续维护和分发。

## 从源码运行

1. 创建虚拟环境
2. 安装依赖
3. 在终端启动游戏

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

## 打包二进制

仓库支持通过 `PyInstaller` 打包。

```bash
PYINSTALLER_CONFIG_DIR=.pyinstaller \
pyinstaller --noconfirm --clean --paths src --onefile --windowed --name deadline-survivors run_game.py
```

注意：

- `PyInstaller` 不能跨平台交叉编译
- Windows 二进制要在 Windows 上构建
- macOS 二进制要在 macOS 上构建
- Linux 二进制要在 Linux 上构建
- 在受限环境里，建议把 `PYINSTALLER_CONFIG_DIR` 指向项目内可写目录

仓库已经包含 GitHub Actions 工作流，可在以下系统生成构建产物：

- Windows
- Linux
- macOS

推送 tag 后也会自动生成可下载的 Release zip 包：

- `deadline-survivors-windows.zip`
- `deadline-survivors-macos-intel.zip`
- `deadline-survivors-macos-apple-silicon.zip`
- `deadline-survivors-linux.zip`

Intel 芯片 Mac 下载 `macos-intel`，M1 / M2 / M3 / M4 这类 Apple Silicon Mac 下载 `macos-apple-silicon`。每个 zip 包里包含可运行程序、README 和手册。推送类似 `v0.2.1` 的 tag 后，GitHub Release 会自动附带这些文件。

## 操作方式

- `WASD` 或方向键：移动
- 标题页按 `Up` / `Down`：选择菜单项
- 标题页按 `Enter` 或 `Space`：确认当前菜单项
- 结算页按 `Left` / `Right`：选择重新开始、成就页或主菜单
- 结算页按 `Enter`：确认当前操作
- 结算页按 `Space`：快速重新开始
- `1`、`2`、`3`：升级时选择选项
- 在标题页 / 结算页按 `1`、`2`、`3`：选择难度
- `How To Play` 页面：按 `Up` / `Down` 滚动，按 `Esc` 返回
- 在标题页 / 结算页按 `A`：打开成就页
- 在标题页 / 结算页按 `B`：切换已解锁 badge
- 在标题页 / 结算页按 `S`：切换已解锁皮肤
- 在标题页 / 结算页按 `T`：切换已解锁 patch 主题
- `P`：暂停 / 继续
- `Esc`：退出

## 核心玩法

- 持续移动，躲避敌人和红色 deadline 区域
- 自动发出 patch 修复问题
- 拾取 insight 碎片
- 拾取 Coffee Break、Refactor Bomb 和 CI Boost
- 抢占可选的 deploy window，获取爆发奖励
- 保持 momentum，提高 insight 收益和 patch 节奏
- `Outage` mini-boss 出现时要优先处理，否则场面会快速失控
- 升级并选择强化
- 尽可能活得更久
- 在不同压力阶段里调整自己的 build

## 标题菜单

标题页现在是更简洁的菜单，而不是把所有说明都塞在第一屏：

- `Start Game`：使用当前难度开始游戏
- `How To Play`：打开可滚动的玩法说明页，包含操作、升级和道具
- `Game Story`：说明开发者、小怪、告警、需求膨胀和 deadline 压力这些设定

标题页还包含一个小的游戏预览画面，让玩家在开始前能看出这是“开发者对抗线上压力”的生存游戏。

## 结算菜单

游戏结束页现在更像一个正式的结算界面，而不是密集统计列表：

- 顶部显示存活时间、最高纪录、难度和本局评价
- 中间卡片显示本局解决的压力数量、insight、deploy 次数和道具使用数
- 底部菜单可以选择重新开始、查看成就或返回主菜单

这样失败后画面更清爽，玩家也能更快决定下一步操作；详细成长信息则放到成就页里。

## Deploy Window 和 Momentum

这个游戏不应该是纯挂机射击。开局之后，地图上会周期性出现可选的 `Deploy Window` 小目标：

- 在倒计时结束前进入绿色 deploy 区域
- 在区域内坚持一小段时间完成 deploy
- 成功后获得额外 insight、小额回血和短暂的 `Focus Mode`

`Momentum` 用来奖励主动移动：

- 持续移动会积累 momentum
- 站着不动会快速衰减
- momentum 会进入 `Flow` 和 `Overdrive` 两个高档位
- `Flow` 和 `Overdrive` 会提高 insight 收益、吸取范围、patch 大小和 patch 节奏
- `Overdrive` 会改变 patch 颜色，让玩家能明显看到状态变化
- `Focus Mode` 会带来短暂爆发，让成功抢目标更有价值

这会形成一个风险收益循环：你可以冒险去抢目标加速成长，也可以在局面太危险时放弃它。

## 升级选项

升级选项主要负责本局长期 build。每次升级后，下一级所需 insight 会继续提高，所以同一颗 insight 碎片在后期占进度条的比例会越来越低。

当前经验需求曲线：

- 1 级升 2 级：70 insight
- 2 级升 3 级：107 insight
- 3 级升 4 级：158 insight
- 4 级升 5 级：223 insight
- 5 级升 6 级：302 insight

这样前期还能看到成长反馈，但中后期不会因为频繁升级打断游戏节奏。

- `Patch Notes`：提高 patch 伤害。
- `Coffee Rush`：提高移动速度。
- `Multicast`：多发一个 patch，直到达到 patch 数量上限。
- `Insight Radar`：扩大 insight 碎片吸取范围。
- `Cache Shield`：提高最大生命值，并回复一小部分生命。
- `Rollback Thread`：让 patch 可以穿透更多问题。
- `Pager Burst`：解锁并强化周期性故障清扫伤害。
- `Quiet Hour`：解锁并强化缓慢自动回血。
- `Code Review`：patch 命中后会继续连锁到附近问题。
- `Pair Programmer`：增加一个环绕主角的僚机，自动补发 patch。
- `Rollback Guard`：低血量时触发一次紧急稳定脉冲。
- `Overclocked Build`：在 Overdrive 状态下，patch 命中会产生小范围爆炸。

短期救场、临时爆发类效果仍然主要放在道具里，但升级池现在也开始包含更明显的机制型 build，让不同局之间的手感差异更大。部分升级收益会随等级小幅提高，避免后期只有敌人变强、玩家成长跟不上的感觉。

## 道具

敌人死亡时有概率掉落临时道具：

- `Coffee Break`：回复一部分生命，不是回满
- `Refactor Bomb`：造成全屏高额伤害，清掉大多数杂兵；Boss 可能存活，只有真正击败的敌人才会给奖励
- `CI Boost`：临时降低 patch 冷却，让修复明显变快

这样升级负责长期成长，道具负责即时爽感和救命时刻。
道具效果也会随等级小幅提高，让中后期的 Coffee Break、Refactor Bomb 和 CI Boost 仍然有救场价值。

## 难度模式

标题页和结算页现在支持三种难度：

- `Easy`：压力更轻，敌人更温和
- `Medium`：默认平衡
- `Hard`：刷怪更快，线上压力更大

难度会影响敌人血量、敌人伤害、刷怪节奏和 insight 收益。

## 战斗 HUD

游戏中的 HUD 现在改成紧凑半透明样式：

- 左上角显示阶段、时间、等级、难度、最高纪录、HP、insight 和 momentum
- 右上角只显示当前生效状态和简短控制提示
- 玩家移动到 HUD 下方时，不会再被完全挡住

## 角色造型

玩家角色现在不是一个普通小圆点，而是一个简单的开发者小人：

- 有头部和身体，更容易识别角色位置
- 有电脑造型，贴合后端工程师主题
- 电脑屏幕上有 `</>` 标记，更容易看出是写代码的人
- 移动时有轻微倾斜，让方向变化更有感觉

目前角色样式刻意保持简单，不依赖外部图片素材，方便后续继续迭代。

现在部分成就还会解锁主角皮肤。皮肤选择保存在本地存档里，可以在标题页或结算页按 `S` 切换，不影响平衡，只改变角色外观。
部分成就现在也会解锁 badge。badge 同样保存在本地存档里，可以在标题页或结算页按 `B` 切换，作为更轻量的长期展示奖励。
部分成就现在也会解锁 patch 主题色。主题同样保存在本地存档里，可以在标题页或结算页按 `T` 切换，并且在 `Flow` / `Overdrive` 状态下依然会继续发生明显的颜色变化。

## 结算统计

每局结束后，游戏会展示一份简短的生产事故报告：

- 本局评价称号
- 一句 build 风格总结
- 若干高光标签
- 本局新解锁的本地成就
- 本局获得的 insight
- 修复了多少 bug
- 躲开了多少 meeting
- 压掉了多少 alert
- 修掉了多少 scope creep
- 解决了多少 outage
- 完成了多少 deploy window
- 用掉了多少道具
- 本局难度

## 本地成就

游戏现在已经接入第一批本地成就，不需要联网、不需要账号：

- `First Patch Rush`：第一次进入 `Overdrive`
- `First Deploy`：第一次完成 deploy
- `First Outage`：第一次击败 `Production Outage`
- `Hard Survivor`：在 `Hard` 难度存活 10 分钟
- `Deploy Addict`：单局完成 5 次 deploy
- `Pair Flow`：拥有 2 个 `Pair Programmer`
- `Review Cascade`：连锁 patch 命中 3 个目标
- `Bug Tracker`：跨多局累计修复 500 个 bug

它们会和最高存活时间一起保存在本地存档里，用来提供离线状态下的长期目标。

成就页现在也按里程碑、挑战、build、长期精通四类分组展示，并对较长线的目标显示轻量进度文本。
顶部还会显示一个 `Next target` 提示，告诉玩家当前最接近完成的目标是什么。

## 反馈打磨

这一版还加入了不依赖外部素材的轻量反馈：

- 内置程序生成音效：patch、升级、拾取、受伤、危机事件、暂停、失败
- 轻微屏幕震动：命中、炸弹、脉冲、危机事件时会更有冲击感
- 暂停界面：长一点的试玩过程更容易中断和继续
- `Outage` 出现时会显示独立血条和遭遇提示
- 角色死亡时会有短暂爆炸反馈，随后进入结算报告

## 压力阶段

游戏现在不再只是线性刷怪，而是分为几段不同节奏：

- `Warmup`
- `Incident Queue`
- `Alert Storm`
- `Deadline Crunch`

这样前 1 分钟更容易进入状态，后期敌人组合也更有层次。

## 危机事件

更平缓的开局阶段之后，游戏会在玩家附近周期性触发危机事件：

- `Standup Swarm`：大量 Bug 加一个会议堵路怪
- `Pager Storm`：多只高速 Alert
- `Scope Review`：需求膨胀压力和分裂怪

## Outage Mini-Boss

进入中期后，游戏会偶尔刷出一个 `Production Outage` mini-boss：

- 它不会简单地贴脸追击，而是保持中距离压迫
- 它会释放一圈危险区，切碎安全走位空间
- 它会周期性召唤支援怪，逼迫你改变优先击杀目标
- 屏幕上会出现单独的 boss 血条，让这一段更像一次正式遭遇战

后期还会出现带橙色外圈的精英怪。它们更硬，用来防止高等级 build 进入挂机状态。

## Deadline 区域

中后期会出现红色 deadline 区域，位置会靠近玩家当前所在区域：

- 区域生效前会先出现红色预警圈
- 生效后，如果玩家还站在里面，会受到一次伤害
- 等级越高、阶段压力越大，区域出现越频繁

这是主要的反挂机机制。即使 Multicast build 能更快清怪，也不能一直站在原地安全输出。

## 平衡说明

`Multicast` 仍然很强，但现在有收益递减：

- 额外 patch 数量有上限
- patch 数量较高时，单个 patch 伤害会明显降低
- 达到上限后，继续选择 Multicast 会改为提升 patch 频率和伤害，而不是无限加 patch

## 手册

完整的玩家和维护手册见：

- [MANUAL.md](MANUAL.md)
- [README.md](README.md)
