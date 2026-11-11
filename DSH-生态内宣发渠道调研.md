# AI Agent 生态内宣发渠道调研：DeepSeek Harness（DSH）

> 调研时间：2026-11-11（Asia/Shanghai）
> 方法：全部结论来自实际抓取的页面 / GitHub API 快照，文末标注来源 URL。凡未查到的，明确写「未查到」，不做推测填充；少数区间值为推算，已单独标注「推算」。

---

## 0. 先看五条结论（会改变你的动作）

1. **DSH 没有官方插件市场，也不存在「提交审核 → 上架官方商店」这条链路。** 官方 `deepseek-ai/deepseek-harness` 仓库 **issues 和 PR 都是关闭的**（API 字段 `has_issues: false`、`has_pull_requests: false`），`CONTRIBUTING.md` 原文写明「we cannot accept external pull requests at the moment」。官方给的唯一机制是：**GitHub Discussions 提反馈 + 给仓库打 `dsh-plugin` topic**。
2. **打 topic 是一次「不可选择目标的广播」。** `dsh-plugin` 这个 topic 会被 dshfind、dsh-market、dshbase、dsh.so、radar 等十几个站点同时自动抓取。你不能只投一家；唯一能控制的是那些「必须提 PR 才进」的目录（awesome 列表类）。
3. **收录 ≠ 审核 ≠ 安全审计。** 绝大多数站点是每日自动扫描 + 静态校验；dshbase 的 `Verified` 是唯一真正跑安装测试的（L1–L4），目前 26,834 个插件里只有 7,872 个通过。
4. **曝光量级差异是数量级的。** 真正能带来万级 star 的是「被 tianyi 在 X 上 team pick」或「产品本身击穿需求」（dsh-Go 10 天 1.8 万 star，没靠推荐）；纯目录收录带来的是长尾安装量，不是 star。
5. **skills 没有官方 registry。** DSH 的 skill 是**文件系统扫描**（`~/.dsh/skills` 等 6 个路径 + `SKILL.md` frontmatter），没有「提交 → 上架」的官方通道；社区侧有一批第三方 skill 市场。

---

## A. 官方渠道

### A1. 官方主仓库 + Discussions + `dsh-plugin` topic

| 项 | 内容 |
|---|---|
| URL | https://github.com/deepseek-ai/deepseek-harness · Discussions: https://github.com/deepseek-ai/deepseek-harness/discussions |
| 仓库快照 | 278,368 ★ / 34,204 forks / MIT / 创建于 2026-08-13 / 默认分支 master / topics: `ai-agents`, `cordis`, `dsh`, `dsh-plugin` |
| **投稿方式** | **没有投稿通道**。issues 与 PR 均关闭。官方路径：① 在 Discussions 发帖/给讨论点赞（团队说会看，但不保证回复）；② 给自己的插件仓库打 `dsh-plugin` topic；③ 写 blog / how-to（CONTRIBUTING 明确鼓励）；④ 在社区答疑 |
| 门槛 | 无。但 CONTRIBUTING 原文说明「packages in the official repository are not inherently more important than community packages」，官方仓库不承诺收录你的插件 |
| 预期曝光 | Discord/Discussions 层面为主；对 star 的直接拉动未查到公开数据 |
| 成本 | 0 元；发一个 Discussion 约 10 分钟 |
| 备注 | **这是最容易搞错的一环：不要花时间准备给官方仓库的 PR，它不会开。** 官方真正的「推荐」出口是 A2 |

### A2. 官方 X 系列【DSH 社区插件推荐】/ team pick（最高杠杆）

| 项 | 内容 |
|---|---|
| URL | https://x.com/tianyi （系列首期示例：https://x.com/tianyi/status/2104565558712959065） |
| 机制（已核实） | tianyi 每天推荐 1 个优质第三方 DSH 插件，**并在推文里邀请插件作者在 thread 下自荐**（"inviting plugin authors to self-nominate in the thread"）。被推荐后会进入第三方 awesome 列表的 Official Picks 区（自动跟进，非投稿） |
| 公开的推荐标准 | **未查到成文标准。** 可观察到的取向：① 补齐 DSH 缺失形态（TUI、侧边栏底座）；② 底座类/可组合性强的项目；③ 解决插件作者真实痛点（如版本升级适配）；④ tianyi 公开说过希望作者做**垂直细分领域**（医疗、经济等），而不是大而全 |
| 门槛 | 无形式门槛，但实际隐含：项目要真实可用、能被 `dsh plugin add` 装、有维护痕迹；自荐需要能一句话说清「补了什么缺口」 |
| 预期曝光 | 单条推文点赞量级 585–4,356（抽样）；带来的 star 增量见第 4 节实证 |
| 成本 | 0 元；写一段自荐文案 + 跟进 ≈ 30 分钟，但要持续在 thread 里出现 |
| 备注 | **这是唯一「官方背书」性质的曝光，且明确不接受投稿、只接受自荐。** 也是唯一会写进 Official Picks 的入口 |

### A3. 官方 Discord

| 项 | 内容 |
|---|---|
| URL | https://discord.gg/4MrtZUhpxg |
| 投稿方式 | 加群自荐、答疑、发插件 |
| 门槛 | 无 |
| 预期曝光 | 未查到成员数与活跃度公开数据 |
| 成本 | 0 元 |
| 备注 | README 的 "Community and support" 段落是官方列出的三个入口之一（另两个是 Discussions 和 topic） |

### A4. 官方文档 / 官方博客署名

- 官方 README 与 CONTRIBUTING 都把「Write blog posts and how-to guides about DeepSeek Harness」列为正式贡献方式。
- **官方文档站**：https://deepseek-harness.github.io/deepseek-harness/ （抓到的是 JS 壳，正文未能完整取回，**内容结构未核实**）。
- 门槛：无；但官方文档站未见「外链投稿」入口，**未查到**可投稿的文档 PR 通道（主仓库 PR 关闭）。

---

## B. GitHub awesome 列表类（唯一「可控」的投稿）

> 这一类是**必须主动 PR 才进**的，与 topic 广播互补。三个主要仓库的规则差异很大。

### B1. Dominic789654/awesome-deepseek-harness

| 项 | 内容 |
|---|---|
| URL | https://github.com/Dominic789654/awesome-deepseek-harness |
| 快照 | 429 ★ / 230 forks / license NOASSERTION / 创建 2026-08-13 |
| **投稿方式** | Fork → **同时改 `README.md` 和 `README.zh-CN.md`（两份要同步）** → 在合适分类下加一行 `- [Name](https://link) — 一句话描述`（中文文件用 ` —— ` 分隔）→ 提 PR。前置：仓库打 `dsh` / `dsh-plugin` / `dsh-skill` / `deepseek-harness` topic |
| 门槛（CI 自动卡，只检查你新增的行） | ① 格式匹配；② 描述非空（光一个 `⭐N` 徽章不算）；③ 链接可解析（404/410 直接挂）；④ GitHub 仓库必须带上述 topic 之一；⑤ PR 只能碰两个 README；⑥ **纯新增**，不许改动/删除既有行 |
| 人工审核 | 有。`main` 开了分支保护，要求 PR + 检查通过；描述要求「factual and hype-free」，禁 "revolutionary"/"best-ever" |
| 预期曝光 | 429★ 的列表，量级有限；但它是 Official Picks 的镜像页所在地，被推荐的项目会在这里获得第二次曝光 |
| 成本 | 20–40 分钟；**最容易踩的坑是把条目插进别人那一行导致描述被截断**（CONTRIBUTING 专门用 diff 举例） |
| 备注 | 排除项：聚合/目录站本身、误标 topic 的仓库、无描述可疑项、archived 仓库。**Official Picks 专栏不接受外部投稿**，唯一途径是被 A2 推荐 |

### B2. awesome-dsh-plugin/awesome-dsh-plugin（**权重最高，也是 dshmarket 的上游**）

| 项 | 内容 |
|---|---|
| URL | https://github.com/awesome-dsh-plugin/awesome-dsh-plugin · 站点 https://awesome-dsh-plugin.com |
| 快照 | **24,227 ★ / 7,859 forks / CC0-1.0**（8 月 22 日时 11,137★，2 个多月翻倍） |
| **投稿方式** | PR 单个文件 `data/plugins/<owner>__<repo>.yml`，然后**本地跑 `npm ci && node scripts/generate-readme.mjs` 重新生成两个 README 一起提交**（禁止手改 README） |
| 门槛 | ① 根包必须有非空 `dsh.bundle.patch`（`dsh.client` 不算，这是最常见被拒原因）；② **仓库创建满 1 天且提交数 ≥ 10**（CI 自动卡）；③ 打 `dsh-plugin` topic；④ 描述必须属实——原文「写『46 个工具、六大领域』，就应该真有 46 个工具和六个领域」；⑤ 分类从 20 个固定值里选（`agi ui usage theme model identity session memory tools browser vision voice docs skill workflow git notify dev security remote market fun`） |
| 人工审核 | **有，且是这一批里最重的**：维护者会读源码核对描述。单 PR 上限 3 条 |
| 预期曝光 | **最高的一档目录曝光**：它是 dshmarket（npm 周下载 289,995）与 dshmarket.com 的唯一数据源，也是 dsh-plugin-catalog（jsDelivr 上的 index.json）的来源。收录后 ≈ 一天内同步到所有下游 |
| 成本 | 2–4 小时（含跑生成脚本、核对描述与代码一致）；0 元 |
| 备注 | 会清退：停更、归档、恶意、明显缺陷的条目会被移除。原文「规则不是先来后到，规则是谁更好」 |

### B3. imsai-sh/awesome-deepseek-harness-plugins（1024Store 目录仓）

| 项 | 内容 |
|---|---|
| URL | https://github.com/imsai-sh/awesome-deepseek-harness-plugins · 站点 https://deepseek1024.com （站点直连抓取失败，**页面未核实**） |
| 快照 | 385 ★ / 423 forks / MIT |
| **投稿方式** | PR 一个 JSON：`catalog/plugins/<id>.json`（id 规则：每段小写、非字母数字转 `-`、段间 `--`，如 `1Ecc/dsh-plugin` → `1ecc--dsh-plugin.json`） |
| 门槛 | ① `package.json` 有非空 `dsh.bundle.patch` 且 patch 文件同 revision 存在；② 已打 `dsh-plugin` topic；③ **PR 只能碰 `catalog/plugins/`**，动 README/workflow 一律拒；④ 恰好 1 条新条目才走自动合并 |
| 人工审核 | **无**（静态检查过即自动 squash merge）。更新/删除既有条目才需人工 |
| 预期曝光 | 中；但**最快的正反馈**——无年龄门槛、自动合并，适合用来验证 `dsh.bundle` 声明是否被 CI 接受 |
| 成本 | 30–60 分钟；0 元 |
| 备注 | 实例：`1Ecc/dsh-plugin` 的 [PR #263](https://github.com/imsai-sh/awesome-deepseek-harness-plugins/pull/263) 已自动合并。注意 `imsai-sh/dsh-1024store` 是站点代码仓，**明确不接受插件提交** |

### B4. 需要纠正的两条线索：官方 awesome 列表不是 DSH 插件渠道

| 仓库 | 快照 | 实际定位 |
|---|---|---|
| https://github.com/deepseek-ai/awesome-deepseek-integration | 39,790 ★ / CC0-1.0 / 最后 push **2026-02-23** | **「Integrate the DeepSeek API into popular software」**——DeepSeek API 集成清单，早于 DSH 发布半年，与 DSH 插件生态无关，且已停更 9 个月。**不建议投** |
| https://github.com/deepseek-ai/awesome-deepseek-agent | 6,418 ★ / 无 license / 最后 push 2026-09-17 | **「guides for integrating DeepSeek models into popular AI agent tools」**——AstrBot/Cline/Codex/OpenClaw 等 22 个工具的接入指南。**不是在 DSH 里装插件**。它的 CONTRIBUTING 接受新 guide 的 issue/PR，但收录的是「某工具怎么接 DeepSeek 模型」，不是「你的 DSH 插件」 |

> 这两条是原始线索里最需要修正的地方：**它们不是 DSH 生态内渠道，投了也不会带来 DSH 插件安装。**

---

## C. 插件导航站（自动聚合为主，手动为辅）

### C1. dshfind.com（hikariming/dshfind）

| 项 | 内容 |
|---|---|
| URL | https://dshfind.com （中文 https://dshfind.com/zh ）· https://github.com/hikariming/dshfind |
| 快照 | 346 ★ / 21 forks / 5 contributors / TypeScript；站点有「论坛」板块 `/bbs` |
| **投稿方式** | **零操作**：给**公开**仓库打 `dsh-plugin` topic。定时任务每天 **02:17 UTC** 同步，约 1 天内出现。**不需要 issue 或 PR** |
| 门槛 | 公开仓库 + topic。连续两次同步仍未出现 → 可能被判 off-topic 或被过滤（私有/归档） |
| 收录后的额外加工 | 站点给每个插件打 **S/A/B/C 等级**（示例：DSH-better-sidebar = **A81**，评分明细：活跃度 21.1 / Star 热度 30 / 工程规范 19.7 / 维护者 10），并显示「近 7 天增长」「下载量（npm + 镜像拆分）」「贡献者数」，另有作者榜与项目榜 |
| 预期曝光 | 示例页数据：DSH-better-sidebar 下载量 **996,887**（npm 622,292 + 镜像 374,595），7 天 star +201。这是**安装量**维度，不是 star 维度 |
| 成本 | 0 元 / 5 分钟（打个 topic） |
| 备注 | 官方 team pick 第 3 期就是推导航站（dshfind / dshmarket / awesome-dsh-plugin 三家并列），说明这三家是官方认可的发现入口 |

### C2. dshmarket.com（dsh-market/dsh-market）

| 项 | 内容 |
|---|---|
| URL | https://dshmarket.com · https://github.com/dsh-market/dsh-market · npm `dshmarket` |
| 快照 | 站点称 **10,119 个插件**；npm **周下载 289,995**；MIT；215 个版本 |
| **投稿方式** | **不要往这个仓库提插件 PR。** README「Submit your plugin」原文：本仓库是市场应用，不是目录；目录来自 awesome-dsh-plugin，**去那边提 PR**，站点与本市场通常一天内自动同步 |
| 门槛 | 继承 B2（`dsh.bundle` + 1 天/10 commits + 描述属实） |
| 预期曝光 | **安装转化最高的一档**：它是唯一能装进 DSH 设置页 / Plugins 页的市场，用户点一下就装。周下载 29 万说明分发面很广 |
| 成本 | 0 元（成本已计入 B2 的 PR） |
| 备注 | 安全边界：安装源被限制在 awesome-dsh-plugin 的 curated registry 内，其他来源直接拒绝；build script 默认封锁。**「市场需求文档」里若写「提交到 dsh-market」是错的** |

### C3. dshbase.com（ylwl1997/dshbase）

| 项 | 内容 |
|---|---|
| URL | https://dshbase.com （中文 https://dshbase.com/zh/plugins/directory/ ）· 审计方法 https://dshbase.com/audit/ |
| 快照（2026-11-08） | **26,834 插件 / 15 大类 / 26,825 仓库；7,872 verified（7,134 L3 + 738 Web L4）/ 10,666 pending / 8,296 listed（未实测）/ 1,496 MIT** |
| **投稿方式** | **GitHub Issue 表单**：https://github.com/ylwl1997/dshbase/issues/new?template=plugin-submission.yml （页面明确给出「提交你的插件 →」按钮）。另有 `dshbase-catalog` 插件可让 agent 直接从该目录装插件 |
| 门槛（唯一的真·安装测试） | **L1 安装**（干净 profile + 锁定 DSH 版本）→ **L2 加载**（profile 启动并 dump 配置）→ **L3 headless**（带插件回答一个问题）→ 若 L3 返回 web-only，**必须过 L4 Web CDP**（起 web profile + 浏览器 CDP 问答）。三级通过才是 `verified`；只从 npm/GitHub 元数据抓到的是 `listed`（不算 verified） |
| 预期曝光 | 26,834 量级目录里带 `Verified` 徽章 + 可嵌 README 的徽章（`https://dshbase.com/badges/<id>.svg`）；提供英文/中文双语页 |
| 成本 | 0 元；提 issue 约 10 分钟。**但要等排队**（10,666 个 pending） |
| 备注 | 明确写「Verified 意思是我们的 CI 真的跑了 `dsh plugin add` 并启动成功——仅此而已。不是安全审计，不是背书」。这句话可以反向用作你对外文案的免责模板 |

### C4. 长尾目录站（可一并覆盖，边际成本≈0）

| 站点 | 抓到的信息 | 投稿方式 |
|---|---|---|
| https://dshplugin.app | 独立目录 + 证据页，支持提交公开 GitHub 仓库，做源码/manifest/依赖/安装路径/兼容性信号分析；明示「Indexed ≠ 安全认证」 | 网页提交仓库 URL（**表单细节未核实**） |
| https://www.dshget.com | 可搜索 web 目录，有插件详情页与安装命令；目录快照公开在 `bobby-sheng/dshget-data` | 未查到明确提交通道 |
| dsh.so | dshbase 的数据源之一（「GitHub dsh-plugin topic + dsh.so 目录合并」）；有 `/zh/artifact/...` 详情页 | 未查到 |
| https://github.com/AdamPlatin123/dsh-plugin-radar | 1,500 ★；2.1 万+ 候选、1.3 万+ k8s 运行级实测、15 分钟快照；自动生成 catalog | 自动聚合，未查到提交入口 |

---

## D. GitHub topic（一次打标，全网广播）

| 项 | 内容 |
|---|---|
| URL | https://github.com/topics/dsh-plugin （主）· `dsh` · `dsh-plugins` · `dsh-skill` · `deepseek-harness` |
| 机制 | 官方 README 与 CONTRIBUTING 都把「给你的插件仓库加 `dsh-plugin` topic」写成正式贡献方式；dshfind、dshmarket 上游、dshbase、dsh.so、radar 全部基于 topic 抓取 |
| 门槛 | **仓库必须 public**、有真实可用代码（非占位/纯 README）、未归档 |
| 预期曝光 | 一次打标同时进十几个目录 + 被搜索引擎索引。**代价是不可撤回**：改回 private 能挡后续访问，已被爬取/缓存的内容收不回来 |
| 成本 | 5 分钟 / 0 元 |
| **副作用（重要）** | topic 任何人都能用，所以目录里混入大量「贴了 dsh-plugin 但不是可安装插件」的高星项目（DSH 平台本体 24.1 万★、ruflo、PicGo、nocobase 等）。这意味着**你的竞品位次会被这些项目挤占**，纯按 star 排序的榜对你没有意义——这也是 dshbase 要做 manifest 审计、awesome-dsh-plugin 要卡 `dsh.bundle` 的原因 |

---

## E. npm 发布（不是「渠道」，但决定所有渠道的转化率）

| 项 | 内容 |
|---|---|
| 事实 | `dsh plugin add <spec>` 支持三种来源：npm 包名（如 `dshmarket`、`dsh-better-sidebar`）、`github:owner/repo`、Release `.tgz` URL |
| 为什么必须发 npm | ① npm 装不触发 build script 审批，体验最顺；② dshmarket 明确「Installs prefer repo-verified npm packages」→ 优先秒装；③ dshmarket 的「Most installed」榜是**按 npm 周下载排**，不发 npm 就进不了这个榜；④ 多个目录站用 npm 下载量做排序/展示 |
| 门槛 | 包名合法、SemVer、`main`/`exports` 指向**已编译的纯 JS**（不能是 .ts）、根 `package.json` 带 `dsh.bundle.patch`、patch 文件真实存在 |
| 预期曝光 | 见 C2 的 289,995/周（dshmarket 自身）；单插件量级未查到公开基准 |
| 成本 | 0 元 + 一次 CI 配置；**持续成本高**：`peerDependencies` 的 `@deepseek-ai/*` 全是预发布版本，node-semver 规则会导致范围静默排除新版本 → 上游每发一个 `0.x.y` 就要补一段 `||`，否则用户 `npm install` 撞 ERESOLVE |

---

## F. Skills 渠道（回答「有没有官方 skill 市场」）

### F1. 结论：官方没有 skill registry，也没有「上架」概念

- DSH 的 `@deepseek-ai/dsh-skill-filesystem` 只做**目录扫描**，路径优先级（只扫顶层，不递归）：

| 优先级 | 路径 | 作用域 |
|---|---|---|
| 100 | `<project>/.dsh/skills` | 项目级 |
| 200 | `<project>/.agents/skills` | 项目级备选 |
| 300 | 自定义目录 | 用户配置 |
| 400 | `~/.dsh/skills` | 用户级 |
| 500 | `~/.agents/skills` | 用户级备选（与 Codex/Claude 共用） |

- **一个 skill = 一个 `<name>/SKILL.md` + YAML frontmatter**，放进上述任一目录即被发现，改文件即热更新，**不需要安装、不需要注册、没有 registry**。
- 已知坑（官方文档明写）：frontmatter 里含冒号、括号、逗号的值不加引号 → YAML 解析失败 → **skill 被静默拒绝，不报错，就是不出现**。一律加引号。

### F2. 社区侧的 skill 市场（想「被分发」就走这些）

| 名称 | URL | 投稿方式 | 门槛 / 备注 |
|---|---|---|---|
| **deepseek.stream（DeepSeek Harness Hub）** | https://deepseek.stream/guide · Skill 市场 https://deepseek.stream/skills · 发布页 https://deepseek.stream/upload | **网页上传表单**（拖拽 zip 或直接粘贴 SKILL.md 文本）+ 账号 | 服务端沙盒解析校验。SKILL.md 必填 `name`(kebab-case) / `category`（**限定 8 类**：academic, security, reverse, workflow, dev, ops, prompt, tools）/ `description`；强烈推荐 `whenToUse`；可选 `version`、`disableModelInvocation`、`userInvocable`、`tags`。**第三方站，非官方**；另有「需求广场」悬赏可接 |
| **dsh-skills-marketplace** | https://github.com/cxdyun/dsh-skills-marketplace · npm `dsh-skills-marketplace` | 你的仓库本身就是「市场源」：DSH 里 `设置 → Skill 插件市场 → 添加插件市场` 填你的仓库 URL + ref + 稀疏路径 | **零改造**：约定式扫 `plugins/*/skills/*/SKILL.md`，或提供 `dsh.market.json`。安装落到 `~/.dsh/skills/`。**这是「让别人能一键装你的 skill」的最短路径** |
| **dshbase** | https://dshbase.com/zh/plugins/directory/ | 同上 C3 的 issue 表单 | 分类里没有单独 Skills 大类，skill 类项目混在 Knowledge/Developer 等；有 verified 机制 |
| **awesome-dsh-plugin** | 同上 B2 | 同上 PR | **category 选 `skill`**；注意纯 SKILL.md 仓库因缺 `dsh.bundle` **过不了 CI**（需做成 bundle 插件才行） |
| **DSH-SkillsHub** | https://github.com/WLX2007/DSH-SkillsHub · npm `@wulongxi/dsh-skills-hub` | 它是「技能中心」客户端，聚合 **SkillHub / skills.sh / GitHub** 三个源 | 想被它搜到，需先被这三个源收录；**SkillHub / skills.sh 的收录规则未核实** |

> 一句话：**skill 没有「投稿」，只有「放到别人会扫的路径/仓库里」。** 想要分发量，要么走 deepseek.stream 的表单，要么把自己的仓库做成 dsh-skills-marketplace 的一个市场源（成本最低、转化最好）。

---

## G. 付费曝光（存在，但不建议作为主路径）

| 项 | 内容 |
|---|---|
| **《DSH 插件周榜》赞助位** | https://514006234.github.io/dsh-weekly-check/sponsor/ |
| 价格（明码标价） | 标准 **¥99/月**（4 期赞助位 + 4 个永久收录位）；季度 ¥279；年度 ¥999；独家一期 ¥299；创始价 ¥99/年（限 3 席）。定制插件开发 ¥3,000 起；私有部署 ¥4,999 起；可信插件白名单 ¥6,999/份 |
| 购买方式 | 扫码付款 → 开 GitHub issue（`sponsor.yml`）留仓库地址 + ≤40 字推荐语 → 下一期上线，全程标「赞助」；7 天内未发布可全额退款 |
| 门槛 | 推荐语必须可核实，不接受夸张；**不卖排名**（榜内排序永远按真实 star） |
| 真实流量 | **站方自己写明「当前流量很小」，且浏览量栏目本期采集失败（GitHub traffic API 403）**——即目前无可用流量数据 |
| 免费互推 | 你在 README 加它的一行链接 → 它在下一期推荐位提你一次并标「互推」；**不承诺阅读量** |
| 成本 | ¥99/月起；互推 0 元 |
| 建议 | 只把它当「中文长尾补量」，不要当主投放。互推档可以白拿，优先走这个 |

---

## H. 国内社区（回答第 6 问）

| 渠道 | 入口 | 性质 / 状态 |
|---|---|---|
| **微信主群** | https://github.com/deepseek-ai/deepseek-harness/discussions/1128 （标题「DeepSeek Harness 微信主群（最新置顶）」，二维码贴在 Discussion 里） | 34 条评论，更新到 2026-10-29；发帖人 `author_association: NONE`，即**社区自发**、非官方运营。二维码会过期（有 issue 反馈 0829 版已失效） |
| **Discord** | https://discord.gg/4MrtZUhpxg | 官方 README 列出，算准官方 |
| **QQ 群** | `577011007`（dsh-better-sidebar README 的 Community 段） | 插件作者自建，偏单一插件用户 |
| **即刻** | 多条真实讨论帖，如 https://m.okjike.com/originalPosts/6a866d8f141b85b292505cd0 、https://m.okjike.com/originalPosts/6ae063095d364e665a5925f5 | 有真实使用体感讨论，也有「没人讨论 DSH 了」这类降温帖；**圈子/话题页未查到官方运营** |
| **知乎** | 问题示例：https://www.zhihu.com/question/2040450519303288568 （「如何看待 DeepSeek 组建 Harness 团队对标 Claude Code？」） | 有问答但**未见 DSH 插件专门话题页**；未查到官方运营账号 |
| **B 站** | 教程类：https://www.bilibili.com/video/BV1REx46NEc4/ （50 分钟 DSH 教程）；插件类：https://www.bilibili.com/video/BV1QRax6VEM1/ （dsh-TUI）；https://www.bilibili.com/video/BV1jkHN6vEkY/ （长期记忆插件）；「大肥鱼」桌宠事件 | **确实有一批 up 主在做 DSH 内容**，但播放量未取到（页面正文被截断）。36kr 采访里提到 B 站「大肥鱼入侵」是 DSH 破圈现象 |
| **CSDN / DeepSeek 技术社区** | https://deepseek.csdn.net/ （有 DSH 专栏文章、生态周报式复盘） | 可投稿，SEO 权重高；适合承接「DSH 插件怎么做」长尾搜索 |
| **大佬说 locdd.com** | https://locdd.com/t/topic/98923 （「DSH 似乎用别人插件不如自己写插件？」） | 中文技术论坛，有真实讨论 |
| **cocoloop.cn** | https://www.cocoloop.cn/t/topic/14726 （「开源了个 DSH 插件开发工具」） | 小论坛，可发帖 |
| **微信公众号** | 有《关于 DeepSeek Harness 官方信息发布及服务渠道的说明》类文章（**原文被微信验证码拦截，正文未核实**） | 生态里已有专门做 DSH 的公众号，但**具体号名与粉丝量未查到** |
| **飞书** | **未查到**任何公开的 DSH 飞书群/知识库入口 | — |

---

## 4. Team pick 的机制与实证（回答第 4 问）

### 4.1 机制（已核实的三层）

1. **入口是自荐，不是投稿**：tianyi 每日推荐 1 个插件，并在推文 thread 里邀请作者自荐。
2. **标准未成文**，但可从已推荐名单反推取向（补齐形态 / 底座 / 作者痛点 / 垂直细分）。
3. **下游自动跟进**：第三方 awesome 列表的 `docs/official-picks.md` 与 README 置顶的 Official Picks 区由自动化每日跟进，「只收录 @tianyi 本人公开推荐」，「**不接受外部投稿——想进专栏，唯一途径是被官方推荐**」。

已核实的推荐样本（含原推链接）：

| # | 项目 | 推荐日 | 类型 |
|---|---|---|---|
| 1 | [dsh-TUI](https://github.com/ccch1mneyyy/dsh-TUI) | 2026-09-26 | 补齐 TUI 形态 |
| 2 | [DSH-better-sidebar](https://github.com/omdsh-dev/DSH-better-sidebar) | 2026-09-27 | 底座 / 可组合性 |
| 3 | dshfind / dshmarket / awesome-dsh-plugin（三家导航站） | 2026-09-28 | 不推单插件，推生态入口 |
| 4 | [dsh-plugin-upgrade-skill](https://github.com/oh-my-dsh/dsh-plugin-upgrade-skill) | 2026-10-05 | 解决插件作者版本适配痛点 |

### 4.2 star 增长实证（**注意：精确的「推荐当天 star 数」未查到**）

GitHub API 只给当前值，star 历史需要第三方里程碑数据。下表把「已核实的里程碑」与「当前值」并列，中间区间标为**推算**：

| 项目 | 推荐日 | 推荐前（已核实的里程碑） | 当前（2026-11-11 API） | 结论 |
|---|---|---|---|---|
| **dsh-TUI** | 09-26 | 破 1k：08-15；破 2.5k：08-25 | **7,457 ★**（+3.0k/30 天，99/天；破 5k 于 10-20） | 推荐时点**推算在 2.5k–3.5k 区间**；推荐后约 3 周破 5k，7 周内到 7.4k |
| **DSH-better-sidebar** | 09-27 | 破 1k：08-15；破 2.5k：08-21 | **5,062 ★**（+926/30 天；破 5k 于 11-08） | 推荐时点**推算在 2.5k–3.5k 区间**；增长更平缓，5k 用了约 6 周 |
| **dsh-plugin-upgrade-skill** | 10-05 | 未查到里程碑 | **318 ★**（周榜显示周增 +7） | **反例：被推荐不等于会涨。** 工具型/受众窄的插件，推荐带来的量级远小于形态型插件 |
| （对照）**dsh-Go** | **未被 team pick** | — | **约 1.8 万 ★**（10-30 上线 3 小时破 1k，10 天 1.8 万） | **产品击穿需求 > 任何渠道**。作者同期也被 36kr 专访 |

补充参照（同一生态、无推荐依赖的量级）：
- 官方主仓库：8 天 18 万★（2026-08-22 快照 180,941★）→ 现在 278,368★。
- awesome-dsh-plugin：08-22 时 11,137★ → 现在 24,227★。
- anywhere-labs/dsh-desktop：08-22 时 17,533★（9 天）→ 现在 34,471★（dshbase 页）。

> **诚实的结论**：team pick 能带来「数周内 +2k~4k star」量级的推动（形态型项目），但它只是放大器，不是发动机；真正决定量级的是「你是否补上了 DSH 缺失的一个形态」和「是否被 36kr/知乎/B站这类站外媒体二次放大」。**精确的推荐日 star 数未查到**，因为公开渠道只有里程碑（破 1k/2.5k/5k 的日期），没有逐日曲线。

---

## 5. 曝光量级对比（一页速查）

| 渠道 | 类型 | 一次动作成本 | 审核强度 | 曝光量级（可核实口径） |
|---|---|---|---|---|
| X team pick（@tianyi） | 官方背书 | 30 分钟（自荐） | 编辑选择（无公开标准） | 单推 585–4,356 赞；star 数周 +2k~4k（形态型） |
| awesome-dsh-plugin PR | 目录（dshmarket 上游） | 2–4 小时 | **高**（读源码 + 1 天/10 commits） | 24,227★ 列表 → 日更同步到 10,119 插件的市场（周下载 289,995） |
| dsh-plugin topic | 广播 | 5 分钟 | 无（public 即可） | 同时进十几个目录；不可撤回 |
| dshmarket 收录 | 分发 | 0（随 B2） | 继承 B2 | 唯一可装进设置页；周下载 289,995（市场本体） |
| dshbase Verified | 实测认证 | 10 分钟（issue） | **最高（L1–L4 真装测）** | 26,834 目录中 7,872 个 verified；带 README 徽章 |
| dshfind 收录 | 自动 | 5 分钟 | 无（topic） | 346★ 站点；示例页显示下载量 996,887 |
| 1024Store PR | 目录 | 30–60 分钟 | 低（自动合并） | 385★ 目录仓；最快正反馈 |
| Dominic awesome PR | 目录 | 20–40 分钟 | 中（CI 6 项 + 分支保护） | 429★ 列表；Official Picks 镜像 |
| deepseek.stream 上传 | Skill 市场 | 20 分钟 | 沙盒解析 | 第三方站，流量未查到 |
| 周榜赞助 | 付费 | ¥99/月 | 低 | **站方自述「流量很小」，无公开浏览数据** |
| 国内社区（Discord/微信/QQ/即刻/知乎/B站/CSDN） | 社群 | 0 | 无 | 具体量级**未查到**（B 站播放量未取到） |

---

## 6. 建议执行顺序（把成本压到最低，先拿可验证的正反馈）

> 逻辑：**先把「能被装」做对（npm + bundle manifest），再用 topic 广播，再用自动合并站验证，最后才攻高门槛目录与官方背书。**

| 阶段 | 动作 | 时间 | 为什么排这里 |
|---|---|---|---|
| 0 | 修 `dsh.bundle.patch`、发 npm、pin 好 peer 范围 | 半天 | 不做这步，后面所有 PR 都会被 CI 拒（`dsh.client` ≠ `dsh.bundle` 是首要被拒原因） |
| 1 | 打 `dsh-plugin` + `dsh` + `deepseek-harness` topic | 5 分钟 | 一次广播进十几个站，零成本 |
| 2 | PR 到 1024Store（B3） | 40 分钟 | 无年龄门槛 + 自动合并，**用它验证 manifest 是否被 CI 接受** |
| 3 | 补齐「1 天 / 10 commits」后 PR 到 awesome-dsh-plugin（B2） | 2–4 小时 | 权重最高，且自动同步到 dshmarket |
| 4 | PR 到 Dominic awesome（B1） | 30 分钟 | 进 Official Picks 的镜像页前置 |
| 5 | dshbase issue 提交（C3） | 10 分钟 | 排队等 L1–L4；拿到 Verified 徽章可嵌 README |
| 6 | 在 tianyi 的推荐 thread 下自荐（A2） | 30 分钟 | 要有前 5 步的「被收录」事实做背书，自荐才站得住 |
| 7 | 中文长尾：周榜互推（免费档）→ CSDN/知乎/B站 | 2 小时 | 承接搜索与破圈 |

**不建议做的三件事**：
1. 给 `deepseek-ai/deepseek-harness` 提 PR（PR 已关闭）。
2. 给 `dsh-market/dsh-market` 提插件 PR（README 明确说去上游）。
3. 投 `awesome-deepseek-integration` / `awesome-deepseek-agent`（不是 DSH 插件渠道，前者已停更 9 个月）。

---

## 7. 未查到 / 需复核清单（不编数字）

| 项 | 状态 |
|---|---|
| 各插件「推荐当天」的精确 star 数与逐日曲线 | **未查到**（只有破 1k/2.5k/5k 的里程碑日期） |
| 各目录站的真实 UV / 点击量 | **未查到**（dshbase、dshfind、dshmarket 均未公开流量；周榜自述流量很小且采集失败） |
| team pick 的成文推荐标准 | **未查到**，只有可观察取向 |
| `Dominic789654/awesome-deepseek-harness` 的「5000+ 条目」 | **未核实**（CONTRIBUTING 与 API 都未给条目数） |
| 官方文档站正文结构 / 是否有外链投稿入口 | 抓取只得到 JS 壳，**未核实** |
| dshplugin.app / dshget.com / dsh.so 的投稿表单细节 | 未核实 |
| B 站相关视频播放量 | 页面正文被截断，**未取到** |
| 是否有 DSH 飞书群 | **未查到** |
| SkillHub / skills.sh 的收录规则 | **未核实**（只确认 DSH-SkillsHub 会搜这两个源） |
| 国内公众号的具体号名与粉丝量 | 微信原文被验证码拦截，**未核实** |
| 官方主仓库 star 数的口径差异 | 周榜写 241.0k（11-09），GitHub API 给 278,368（11-11）；以 API 为准，差异原因未查明 |

---

## 附：主要来源

- 官方站点 https://www.deepseek.com/harness/ ｜ 主仓库 API https://api.github.com/repos/deepseek-ai/deepseek-harness ｜ CONTRIBUTING https://github.com/deepseek-ai/deepseek-harness/blob/master/CONTRIBUTING.md ｜ Discussions #1128 https://github.com/deepseek-ai/deepseek-harness/discussions/1128
- Official Picks https://github.com/Dominic789654/awesome-deepseek-harness/blob/main/docs/official-picks.md ｜ CONTRIBUTING https://github.com/Dominic789654/awesome-deepseek-harness/blob/main/CONTRIBUTING.md
- awesome-dsh-plugin https://awesome-dsh-plugin.com ｜ https://github.com/awesome-dsh-plugin/awesome-dsh-plugin
- dshmarket https://dshmarket.com ｜ https://www.npmjs.com/package/dshmarket
- dshfind https://dshfind.com ｜ 插件页示例 https://dshfind.com/zh/plugins/omdsh-dev/DSH-better-sidebar
- dshbase https://dshbase.com/audit/ ｜ https://dshbase.com/zh/plugins/directory/
- 1024Store 目录仓 https://github.com/imsai-sh/awesome-deepseek-harness-plugins ｜ 收录机制复盘 https://github.com/1Ecc/dsh-plugin/blob/main/docs/marketplace-listing.md ｜ 另一份 https://github.com/foggy-projects/foggy-deepseek-harness-plugin/blob/main/docs/COMMUNITY-MARKETPLACES.md
- Skills：deepseek.stream https://deepseek.stream/guide ｜ dsh-skills-marketplace https://cdn.jsdelivr.net/npm/dsh-skills-marketplace@1.1.2/docs/guide.md
- Star 里程碑：https://gittrend.io/repo/ccch1mneyyy/dsh-TUI ｜ https://gittrend.io/repo/omdsh-dev/DSH-better-sidebar
- team pick 报道：https://rss.bz/post/deepseek-harness-plugin-ecosystem-monthly ｜ 插件政策 https://rss.bz/post/deepseek-harness-agent-os-plugin-policy ｜ 推荐追踪 https://github.com/AdamPlatin123/dsh-plugin-radar/blob/main/data/cui-picks.json
- 生态量级：https://deepseek.csdn.net/6a8a2bb6662f9a54cb9f8ad7.html ｜ https://eu.36kr.com/en/p/4063892080694408
- 周榜赞助 https://514006234.github.io/dsh-weekly-check/sponsor/
