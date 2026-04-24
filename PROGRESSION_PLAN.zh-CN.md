# Deadline Survivors 结算评价与本地成就设计方案

本文用于规划 `deadline-survivors` 的下一阶段成长系统，重点包括：

- 结算页评价
- 本地成就
- 后续可扩展的解锁系统

目标不是简单堆功能，而是借鉴成熟同类游戏的结构，让游戏更有“多玩几局”的理由。

## 设计依据

这一方案主要参考了同类幸存者游戏的成熟做法：

- `Vampire Survivors`
  - 核心特点是 `Achievements / Unlocks` 不只是勋章，而是长期成长和新内容解锁系统。
  - 参考：
    - https://vampire.survivors.wiki/w/Achievements
    - https://vampire.survivors.wiki/w/Stages
- `20 Minutes Till Dawn`
  - 核心特点是大量挑战型成就，用来定义玩法路线和构筑差异。
  - 参考：
    - https://20minutestilldawn.wiki.gg/wiki/Achievements
    - https://20minutestilldawn.wiki.gg/wiki/Modes

从这些成熟作品里，真正值得学习的是三点：

1. 成就不能只是无聊累计数字。
2. 成就应该鼓励玩家尝试不同打法和风险选择。
3. 结算页要能总结这一局的风格，而不是只显示流水账。

## 一、为什么现在要做这套系统

当前 `deadline-survivors` 已经有：

- 完整游戏闭环
- 多类敌人
- 道具
- 难度
- 升级 build
- mini-boss

但目前还缺少两类内容：

### 1. 单局结束时的“评价感”

现在结算页主要是统计信息，例如：

- 存活时间
- insight
- bug 修复数
- deploy 数

这些是数据，但不是“总结”。

玩家结束一局后，还缺少这种感觉：

- 这局我是怎么赢/怎么死的
- 这局是什么 build 风格
- 这局有没有打出一个代表性的玩法

### 2. 多局游玩时的“长期目标”

目前玩家重开更多依赖即时乐趣，但缺少长期牵引，例如：

- “再玩一局把这个挑战做掉”
- “再玩一局尝试另一种 build”
- “再玩一局把某个里程碑完成”

所以现在适合引入：

- 结算页评价：提升单局结束反馈
- 本地成就：提升多局持续动力

## 二、结算页评价是什么

结算页评价的目标是：

- 识别这局 run 的风格
- 用称号和短句进行概括
- 让玩家感觉系统“看懂了自己这一局是怎么打的”

它不等同于成绩高低，而是更偏“风格识别”。

## 三、结算页评价的设计原则

### 1. 优先识别玩法，不只识别分数

不建议只做：

- 存活时间超过 5 分钟 = A
- 超过 10 分钟 = S

这种太平，没有性格。

应该优先根据玩法风格给出评价，例如：

- 高移动
- 高 deploy
- 高爆发
- 高生存
- 高风险
- 专攻 boss

### 2. 一局只给一个主评价

不要结算时同时出现很多称号，否则会失焦。

建议结构：

- 一个主称号
- 一句副描述
- 再配统计数据

### 3. 评价要与主题一致

游戏主题是“开发者在 deadline 下生存”，所以称号和文案也要围绕这个世界观。

不要突然变成传统奇幻 RPG 风格。

## 四、首版结算页评价方案

### 结构建议

结算页新增一个板块：

- `Run Evaluation`
- `Run Style`

显示内容：

- 主称号
- 一句副描述
- 1 到 2 个高光标签

### 候选称号设计

#### 1. `Patch Sprinter`

适用条件：

- 高 momentum 覆盖
- 高移动距离
- deploy 数较多

风格说明：

- 偏机动与节奏控制

副描述示例：

- 你靠持续移动和节奏控制把生产线拉了起来。

#### 2. `Incident Cleaner`

适用条件：

- 清怪量高
- 脉冲、爆炸、清场类效果占比高

风格说明：

- 偏清场与波次处理

副描述示例：

- 你更像一个故障清扫器，而不是只顾着逃命。

#### 3. `Deploy Specialist`

适用条件：

- deploy 完成数高

风格说明：

- 偏目标导向与风险收益

副描述示例：

- 你在最拥挤的时候仍然敢抢部署窗口。

#### 4. `Outage Hunter`

适用条件：

- 解决了多个 `Outage`

风格说明：

- 偏 boss 优先级和场面掌控

副描述示例：

- 你没有被故障节奏带走，而是主动把它压了下去。

#### 5. `Last-Minute Hero`

适用条件：

- 低血量持续时间长
- `Rollback Guard` 多次触发
- 但仍然活了较久

风格说明：

- 偏极限求生

副描述示例：

- 这局不是稳定推进，而是一次又一次从事故边缘救回来。

#### 6. `Pair Programming Lead`

适用条件：

- `Pair Programmer` build 很明显

风格说明：

- 偏僚机 build

副描述示例：

- 这局不是单兵作战，而是团队协作式修复。

#### 7. `Code Review Machine`

适用条件：

- 连锁 patch、穿透、范围命中明显

风格说明：

- 偏连锁与 build 扩散

副描述示例：

- 一个 patch 不够，你让问题自己连锁暴露了出来。

#### 8. `Steady Maintainer`

适用条件：

- 没有特别突出的 build 标签
- 但总体存活稳定

风格说明：

- 平衡型

副描述示例：

- 你没有走极端路线，但把系统稳稳维持住了。

## 五、结算页高光标签建议

除了主称号，可以加 1 到 2 个小标签。

例如：

- `High Momentum`
- `Boss Priority`
- `Deploy Focus`
- `Low HP Survivor`
- `Wave Cleaner`
- `Chain Build`
- `Support Build`

作用：

- 让结算页更像“战报”
- 也方便以后接成就系统

## 六、本地成就是什么

本地成就是存储在本机的长期目标系统。

特点：

- 不联网
- 不依赖排行榜
- 不依赖账号
- 可以直接本地 JSON 存档

第一阶段它只负责：

- 给玩家长期目标
- 鼓励尝试不同玩法
- 增强项目完整度

第一阶段不负责：

- 解锁新角色
- 解锁新地图
- 解锁新系统

这些放到后续阶段再考虑。

## 七、本地成就设计原则

### 1. 不要全是累计数字题

例如：

- 打死 100 个敌人
- 打死 500 个敌人
- 打死 1000 个敌人

这种成就过多会很无聊。

### 2. 要有“鼓励不同玩法”的成就

成熟同类游戏很重要的一点就是：成就引导玩家尝试不同 build、不同难度、不同风险打法。

### 3. 要分层

建议分成四类：

- `Milestone`
- `Challenge`
- `Build`
- `Mastery`

这样结构清晰，也更方便以后扩展。

## 八、首批本地成就清单

### A. Milestone 成就

适合作为第一次接触系统时的引导。

#### 1. `First Patch Rush`

- 第一次进入 `Overdrive`

#### 2. `First Deploy`

- 第一次完成 `Deploy Window`

#### 3. `First Rescue`

- 第一次触发 `Rollback Guard`

#### 4. `First Outage`

- 第一次击败 `Production Outage`

#### 5. `First Long Night`

- 第一次存活超过 5 分钟

### B. Challenge 成就

适合制造明确的“再玩一局试一下”动机。

#### 6. `Nimble Coder`

- 一局内 4 分钟不吃伤害

#### 7. `No Coffee Run`

- 一局内不使用任何回血道具，存活 6 分钟

#### 8. `Deploy Addict`

- 一局内完成 5 次 Deploy

#### 9. `Crunch Survivor`

- 在 `Crunch` 难度存活 10 分钟

#### 10. `Boss Focus`

- 一局内击败 2 个 `Outage`

### C. Build 成就

用来引导玩家尝试不同升级路线。

#### 11. `Pair Flow`

- 同时拥有 2 个 `Pair Programmer`

#### 12. `Review Cascade`

- 单次连锁 patch 命中 3 个目标

#### 13. `Safe Rollback`

- 一局内 `Rollback Guard` 触发 3 次且没有死亡

#### 14. `Sweep Operator`

- `Pager Burst` 或爆炸类效果一次命中大量敌人

#### 15. `Overclocked Shift`

- 在 `Overdrive` 状态下累计造成一定量伤害

### D. Mastery 成就

偏长期积累，适合作为持续目标。

#### 16. `Bug Tracker`

- 累计修复 500 个 bug

#### 17. `Meeting Resistant`

- 累计躲开 200 个 meeting

#### 18. `Alert Tamer`

- 累计压制 300 个 alert

#### 19. `Scope Wrangler`

- 累计处理 150 个 scope creep

#### 20. `Outage Manager`

- 累计解决 20 个 `Outage`

## 九、哪些成就最适合首版先做

第一版不要一口气做 20 个。

建议先做 8 到 10 个，优先这几类：

- 第一次进入 `Overdrive`
- 第一次完成 `Deploy`
- 第一次击败 `Outage`
- `Crunch` 存活 10 分钟
- 一局完成 5 次 Deploy
- 2 个 `Pair Programmer`
- 连锁 patch 命中 3 个目标
- 累计修复 500 个 bug

这样既有：

- 新手引导
- 挑战目标
- build 引导
- 长期积累

## 十、存档结构建议

建议新增一个本地文件，例如：

- `.deadline_survivors/progression.json`

建议结构：

```json
{
  "achievements": {
    "first_overdrive": {
      "unlocked": true,
      "unlocked_at": "2026-04-24T12:00:00Z"
    },
    "first_deploy": {
      "unlocked": false
    }
  },
  "totals": {
    "bugs_fixed": 132,
    "meetings_dodged": 48,
    "alerts_silenced": 53,
    "scope_trimmed": 27,
    "outages_resolved": 3,
    "deploys": 14,
    "runs_played": 9,
    "best_time": 421.6
  }
}
```

第一版不需要复杂数据库，本地 JSON 足够。

## 十一、实现顺序建议

### Phase 1

- 增加结算页称号
- 增加结算副描述
- 增加高光标签

### Phase 2

- 本地成就 JSON
- 解锁检测
- 结算时弹出新成就提示

### Phase 3

- 标题页增加 `Achievements` 查看入口
- 显示已解锁 / 未解锁列表

### Phase 4

- 再考虑把部分成就绑定到：
  - 新皮肤
  - 新模式
  - 新难度
  - 新道具

## 十二、当前最推荐的实际推进方案

下一步最合适的是：

1. 先做 `结算页评价`
2. 再做首批 `8-10 个本地成就`
3. 暂时不做成就解锁新内容

原因：

- 风险低
- 实现快
- 反馈明显
- 不会把范围扩散成大重构

## 十三、最终结论

这套系统应该学习成熟同类游戏的“结构”而不是表面：

- `Vampire Survivors` 学的是长期成长和解锁链路
- `20 Minutes Till Dawn` 学的是挑战条件和 build 引导

对应到 `deadline-survivors`，当前最合理的路线是：

- 先让结算页能识别玩家这一局的风格
- 再用本地成就驱动多局重复游玩
- 等内容更多后，再把成就与新内容解锁绑定

这是能兼顾质量、趣味性和项目节奏的方案。

