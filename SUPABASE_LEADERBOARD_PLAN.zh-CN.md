# Supabase 排行榜接入方案

本文面向 `deadline-survivors`，目标是在不自建服务器、不自管数据库的前提下，为本地单机游戏增加可上线、可扩展的在线排行榜能力。

## 目标

- 不自建服务器
- 不自己维护数据库
- 先让 `deadline-survivors` 具备在线排行榜
- 后续能扩展到更多游戏、更多榜单、更多赛季

## 结论

优先采用：

- `Supabase`
- 客户端直连
- 只读排行榜
- 受限写入成绩
- 后续预留 `Edge Function` 增强校验

官方依据：

- Supabase 提供托管数据库、Data API、Auth、Realtime：
  - https://supabase.com/docs
- Supabase 提供 `Free Plan`：
  - https://supabase.com/docs/guides/platform/billing-on-supabase
- 客户端直连时需要依赖 `RLS`：
  - https://supabase.com/docs/guides/database/secure-data
- `anon key` 可暴露给客户端，但 `service role key` 不可暴露：
  - https://supabase.com/docs/guides/database/secure-data
- `RLS` 是权限控制核心：
  - https://supabase.com/docs/guides/auth/auth-deep-dive/auth-row-level-security

## 现实边界

这个项目是本地单机游戏，客户端源码公开，且暂时没有你自己的服务端验签，所以第一版不可能做到真正强防作弊。

第一版应该定位为：

- 社区娱乐榜
- 展示玩家成绩
- 增强项目完整度

而不是：

- 强竞技
- 强公正
- 电竞级对抗

目标应该是“提高作弊成本”，不是“假装绝对安全”。

## 总体架构

### Phase 1：最快上线版

- 游戏客户端 `Python`
- Supabase `Postgres`
- Supabase `REST API`
- 客户端直接提交成绩
- 客户端直接读取排行榜
- 通过 `RLS + 数据约束 + 基础规则` 限制滥用

适合当前阶段，开发成本最低。

### Phase 2：增强版

- 客户端不再直接写表
- 客户端调用 Supabase `Edge Function`
- 函数内部做：
  - 参数校验
  - 签名校验
  - 限流
  - 版本控制
  - 数据清洗
- 再由函数写数据库

这个阶段适合后续排行榜数据量上来后再做。

## 推荐数据模型

建议至少设计以下几张表：

- `games`
- `leaderboards`
- `runs`
- `score_submissions`
- `player_profiles`

第一版可以先只实现其中一部分，但结构最好先按可扩展方向规划。

### 1. `games`

用于支持多个小游戏共用同一套排行榜底层设施。

建议字段：

- `id`
- `slug`
- `name`
- `is_active`
- `created_at`

示例：

- `slug = deadline-survivors`

作用：

- 后面你做第二个、第三个小游戏时不需要重构整套系统。

### 2. `leaderboards`

一款游戏可能不止一个榜，所以不要把排行榜写死成一张表一个字段。

建议字段：

- `id`
- `game_id`
- `key`
- `name`
- `score_kind`
- `sort_order`
- `is_active`
- `season_key`
- `created_at`

示例 `key`：

- `global_best_time`
- `casual_best_time`
- `normal_best_time`
- `crunch_best_time`
- `weekly_best_time`

作用：

- 支持总榜、难度榜、周榜、赛季榜。

### 3. `runs`

`runs` 是最关键的表。排行榜不应该只存一个裸分数，应该保存一局游戏的完整结果。

建议字段：

- `id`
- `game_id`
- `client_run_id`
- `player_name`
- `difficulty`
- `survival_seconds`
- `insight`
- `bugs_fixed`
- `meetings_dodged`
- `alerts_silenced`
- `scope_trimmed`
- `deploys`
- `powerups_used`
- `game_version`
- `platform`
- `build_channel`
- `ended_at`
- `created_at`
- `checksum`
- `is_valid`
- `invalid_reason`

作用：

- 排行榜背后有完整 run 数据
- 方便做后续统计分析
- 方便清洗作弊数据

### 4. `score_submissions`

建议把“提交事件”和“成绩实体”分开，后续便于审计。

建议字段：

- `id`
- `run_id`
- `leaderboard_id`
- `submitted_score`
- `accepted_score`
- `rank_snapshot`
- `status`
- `reason`
- `created_at`

状态示例：

- `accepted`
- `rejected`
- `flagged`

作用：

- 审计提交
- 记录拒绝原因
- 后续接入函数校验时更容易平滑扩展

### 5. `player_profiles`

第一版即便不做完整注册系统，也建议预留这张表。

建议字段：

- `id`
- `player_name`
- `display_name`
- `country_code`
- `created_at`
- `last_seen_at`

作用：

- 第一版可以只用昵称
- 后面接匿名账号、GitHub 登录、邮箱登录时更顺

## 第一版最小可用结构

如果要压缩复杂度，第一版最小可用建议先只做：

- `leaderboards`
- `runs`

然后通过 `view` 或 `RPC` 暴露排行榜读取能力。

这是最适合 MVP 的做法。

## 排行榜读取设计

不建议让客户端自己写复杂 SQL。推荐在 Supabase 里提供固定的只读视图或 RPC。

### 方案 A：视图

建议至少提供：

- `leaderboard_top_view`
- `player_best_view`

#### `leaderboard_top_view`

职责：

- 返回某个排行榜前 N 名

建议返回字段：

- `leaderboard_key`
- `rank`
- `player_name`
- `survival_seconds`
- `difficulty`
- `game_version`
- `ended_at`

规则：

- 同一玩家默认只保留最好成绩
- 防止一个玩家占满榜单

#### `player_best_view`

职责：

- 给玩家查看自己的历史最好成绩

建议字段：

- `player_name`
- `best_survival_seconds`
- `best_rank`
- `last_run_at`

### 方案 B：RPC

如果后续读取逻辑变复杂，可以把排行榜读取包装成 Postgres 函数，再通过 Supabase RPC 暴露。

优点：

- 客户端接口更稳定
- 服务端逻辑更集中

第一版可以先用视图，后续再切 RPC。

## 成绩提交流程

第一版建议只允许在游戏结算后提交成绩，不允许中途上传。

流程：

1. 玩家死亡或一局结束
2. 玩家输入昵称
3. 客户端生成 `client_run_id`
4. 组装 run 数据
5. 提交到 Supabase
6. 返回是否成功
7. 成功后刷新最新排行榜

建议提交字段：

- `client_run_id`
- `player_name`
- `difficulty`
- `survival_seconds`
- `insight`
- `bugs_fixed`
- `meetings_dodged`
- `alerts_silenced`
- `scope_trimmed`
- `deploys`
- `powerups_used`
- `game_version`
- `platform`
- `build_channel`
- `ended_at`

## RLS 设计原则

这是第一版成败的关键。

原则：

- 客户端只使用 `anon key`
- 开启 `RLS`
- 允许安全范围内的只读
- 允许受限插入
- 禁止客户端 `update`
- 禁止客户端 `delete`

### `leaderboards` 表建议

- `select`：允许匿名读
- `insert`：禁止
- `update`：禁止
- `delete`：禁止

### `runs` 表建议

- `select`：不直接开放整表，优先只开放视图
- `insert`：允许匿名插入，但必须满足字段和约束规则
- `update`：禁止
- `delete`：禁止

## 数据约束建议

客户端可写时，数据库层的约束必须尽量严格。

建议加入：

- `player_name` 长度限制
- `player_name` 非空
- `difficulty` 只允许：
  - `casual`
  - `normal`
  - `crunch`
- `survival_seconds >= 0`
- 所有统计字段 `>= 0`
- `client_run_id` 唯一
- `game_version` 长度限制
- `platform` 长度限制
- `build_channel` 长度限制

可加入明显异常的上限：

- `survival_seconds <= 86400`
- `insight` 上限
- 各类击杀统计上限

目的不是彻底防作弊，而是先挡掉大量低级脏数据。

## 第一版防作弊建议

没有独立后端时，不要追求伪强安全。优先做低成本、高收益的防滥用。

### 1. 每局唯一 `run_id`

- 防止重复提交同一局

### 2. 只允许结算提交

- 中途不开放上传入口

### 3. 成绩交叉校验

例如：

- `survival_seconds` 极高但 `bugs_fixed = 0`
- `deploys` 远超合理范围
- `powerups_used` 与生存时间严重不匹配

这类可以标记为可疑数据。

### 4. 版本字段

建议区分：

- `release`
- `dev`
- `source`

第一版排行榜可以默认只展示：

- `release`

或者单独给 `source/dev` 分榜。

### 5. 昵称规则

- 长度限制
- 过滤空白
- 过滤敏感词
- 过滤明显垃圾字符

### 6. 保留审核字段

在 `runs` 中保留：

- `is_valid`
- `invalid_reason`

后续手工清理异常数据会方便很多。

### 7. 榜单展示去重

- 每个昵称只展示最好成绩

防止单人刷屏霸榜。

## 第二阶段增强：Edge Function

后续最值得做的升级是把成绩提交改为 `Edge Function`。

### 改造思路

- 客户端不再直接写 `runs`
- 客户端调用 `submit-score`
- Edge Function 使用安全凭证写数据库
- 在函数内完成：
  - 参数校验
  - 签名校验
  - 提交频率限制
  - 游戏版本控制
  - 数据清洗
  - 自动同步多榜单

### Edge Function 能带来的价值

- 客户端权限更少
- 逻辑更集中
- 便于做基础反作弊
- 便于未来扩展赛季榜和挑战榜

## 扩展路线设计

### A. 多榜单

同一款游戏可以扩展：

- 全局生存榜
- `Casual / Normal / Crunch` 分榜
- 周榜
- 月榜
- 赛季榜
- 挑战榜

挑战榜示例：

- 不使用道具最长存活
- 只玩 `Crunch` 的最长存活
- 完成最多 deploy 的 run

### B. 多游戏

后续你做其他小游戏时，可复用同一套 Supabase 基础设施。

例如：

- `deadline-survivors`
- `maze-chase`
- 未来新的 Python/CLI 游戏

所以 `games` 表很重要。

### C. 玩家体系

后续可以从“纯昵称”扩展到：

- 匿名账号
- GitHub 登录
- 邮箱登录

Supabase 自带 Auth，扩展路径是顺的：

- https://supabase.com/docs/guides/auth

### D. 战绩详情

后续可以额外保存：

- 随机种子
- 最终等级
- 升级选择列表
- 关键事件时间线

再做：

- 战绩详情页
- 可分享链接
- 本局 build 展示

### E. 赛季重置

建议在 `leaderboards` 中加入：

- `season_key`

示例：

- `2026-s1`
- `2026-04-week4`

这样赛季重置不需要删历史数据。

### F. 社区功能

以后还能做：

- 玩家个人最好成绩页
- 最近战绩流
- 今日榜
- 国家/语言分榜
- 好友榜

## 客户端接入建议

针对 `deadline-survivors` 的 Python 客户端，建议拆成三个模块：

### 1. `leaderboard_client.py`

负责：

- 请求 Supabase
- 提交成绩
- 获取排行榜

### 2. `score_payload.py`

负责：

- 构造提交数据
- 本地校验字段
- 规范化昵称

### 3. 本地缓存

建议本地缓存：

- 最近一次排行榜
- 待上传成绩队列

例如：

- `data/leaderboard_cache.json`
- `data/pending_scores.json`

### 离线与失败重试

建议客户端具备：

- 启动时可完全离线
- 结算时如果上传失败：
  - 提示“成绩未上传，可稍后重试”
- 下次启动时自动重试待上传队列

这能显著提升可用性。

## 推荐版本推进顺序

### v0.2

- 建立 Supabase 项目
- 建表
- 开启 RLS
- 客户端提交成绩
- 客户端读取 Top 20
- 本地失败重试

### v0.3

- Edge Function 接管提交
- 基础反作弊
- 分难度榜
- 玩家最好成绩

### v0.4

- 周榜 / 赛季榜
- 昵称配置
- 战绩详情

## 当前最合适的落地方案

针对当前项目，建议直接采用：

- 1 个 Supabase 项目
- 2 张核心表：
  - `leaderboards`
  - `runs`
- 2 个视图：
  - `leaderboard_top_view`
  - `player_best_view`
- 客户端直连
- `RLS`
- 客户端只允许 `insert`
- 客户端禁止 `update/delete`
- 榜单按昵称去重展示最好成绩

先不做：

- 复杂账号体系
- 强反作弊
- 实时推送
- 社交关系
- 复杂赛季系统

原因很明确：这些都不是当前短板，会明显拖慢项目推进。

## 安全底线

必须明确：

- `anon key` 可以放客户端，但前提是 `RLS` 正确
- `service role key` 绝不能放客户端
- 新建表必须启用 `RLS`

参考：

- https://supabase.com/docs/guides/database/secure-data
- https://supabase.com/docs/guides/auth/auth-deep-dive/auth-row-level-security

## 最终建议

`deadline-survivors` 很适合加排行榜，因为它天然有明确可比的核心分数：

- 生存时间
- 难度
- 本局统计

它适合做：

- 社区娱乐榜
- GitHub 展示功能
- 可分享成绩的小作品

它暂时不适合做：

- 强竞技排行榜
- 赛事级公正榜

这套方案已经足够支撑第一版上线，并且不会堵死后续扩展路径。

## 后续可直接落地的下一步

在这份方案基础上，下一步可以继续产出：

1. Supabase 建表 SQL
2. `RLS policy` 示例
3. Python 客户端提交/查询接口设计
4. 游戏内排行榜 UI 接入位置
5. 第一版必须实现字段清单

