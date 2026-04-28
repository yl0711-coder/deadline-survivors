# Deadline Survivors 推广检查清单

这份清单用于把 GitHub 项目页整理成适合对外分享的状态。

## GitHub 仓库首屏

- `About` 描述建议：`A tiny local arcade survival game about shipping patches while bugs, meetings, alerts, and production outages close in.`
- `Website` 暂时可以留空；如果后续创建 itch.io 页面，再填 itch.io 链接。
- `Topics` 建议：`python`、`pygame`、`pygame-ce`、`arcade-game`、`survival-game`、`indie-game`、`desktop-game`、`open-source-game`、`pyinstaller`。
- README 首屏需要能直接说明：这是什么、为什么好玩、怎么下载、是否需要服务器、是否收集数据。

## Release 页

- 最新 Release 标题建议保持版本号清晰，例如 `Deadline Survivors v0.2.6`。
- Release 描述里应包含四个平台下载包：Windows、macOS Intel、macOS Apple Silicon、Linux。
- macOS 包需要提示未签名开源构建可能出现系统安全提示。
- Windows 包需要提示解压后运行可执行文件，不需要安装 Python。

## 对外分享前自检

- README 英文和中文内容同步。
- `assets/demo.gif` 可以在 GitHub 首屏正常加载。
- `assets/screenshots/` 的四张图能清楚展示启动页、游戏中、升级页和结算页。
- 最新 GitHub Actions 全部通过。
- 最新 Release 资产可下载，且 Windows、macOS Intel、macOS Apple Silicon、Linux 四个平台包名称清晰。
- 项目明确写出：不需要服务器、不需要账号、没有遥测统计、数据保存在本地。

## 后续可补充

- 创建 itch.io 页面后，在 README 的下载位置增加 itch.io 链接。
- 如果收到玩家反馈，可以把常见问题沉淀到 `MANUAL.md`。
- 如果玩法继续变化，GIF 和截图需要同步更新。
