# 海外宣发渠道与成本调研（2026-11）

> 对象：中国个人开发者，GitHub 2013 年注册、47 followers、最高 16 stars；产品为 DeepSeek Harness（DSH）Skill：`ear`（离线音频/视频 → 结构化时间轴）+ 若干小工具。
> 目标：低成本让海外开发者看到。以下只写查到的公开数据；查不到的明确标注“未查到”。时间成本为本报告估算，不是平台数据。

## 0. 一句话结论

**最值得先做的不是“发一条 HN”，而是把 `ear` 变成陌生人 60 秒内能试的东西，然后同时打三个点：`awesome-dsh-plugin` 收录（DSH 内置 Discover 的索引源）+ Show HN + r/LocalLLaMA。** GitHub Trending 对 16 stars 的新仓库基本不可控；Product Hunt 没有受众时大概率不被 featured；付费 newsletter 对个人项目 ROI 极差。

`ear` 有一个必须先修的叙事矛盾：README 写“离线音频/视频”，但 `basic` 依赖 Qwen Audio 云端调用；HN/Reddit 会抓住“offline 还要 API key”这一点打。要么提供无需 key 的本地 demo（VAD/BEATs + 样例输出），要么把定位改成“local-first, cloud optional”，并在第一条评论里主动说明。

---

## 1. 渠道总表

| 渠道 | 规则 / 门槛 | 金钱成本 | 时间成本（估算） | 实际带量（公开数据） | 0 受众冷启动 |
|---|---|---|---|---|---|
| **Show HN** | 必须是“你做的东西，别人能试”；博客/落地页/waitlist/newsletter 不算；标题 `Show HN: 名称 – 它做什么`；可带项目链接；一个产品基本只有一次；发布后 2 小时内可改标题 | 0 | 2–4 周养号（每天 30 分钟评论）+ 8–12h 准备 + 发布后 4h 守帖，合计约 20h | 中位数 **2 分**；90 分位 24；99 分位 263；50+ 约 top 6%。首页 5k–30k uniques/24h 是广泛引用但来源弱的范围；真实案例之一：上首页仅 **~500 HN uniques / ~6k pageviews**。未上首页通常只有几十次访问 | **中高**：免费、账号 2013 年有价值；但只有一次机会，且必须“可试” |
| **Product Hunt** | 免费提交；分 Featured / All；只有约 **10%** 被 featured；不能直接求 upvote；Product of the Day 约 **450–1,200** 质量加权 upvote；前 4 小时决定 | 0 | 提前 6 周准备素材 + 发布日 12h+，约 30–40h | Featured top3：5k–15k visitors、100–400 signups；4–10 名：1k–3k、30–100；11–30 名：300–700、10–30；**未 featured：100–500 visitors、1–15 signups**。转化 1–5%，48h 后回落 | **低**：没有受众基本进不了 featured；个人项目不建议作为第一站 |
| **GitHub Trending** | 无官方算法；核心是 24–48h star 增速；分 daily/weekly/monthly、语言榜；另有 spoken language（含 Chinese）筛选 | 0 | 20–40h（README、demo、发布协调） | 第三方估算：All Languages **80–150 stars/day**；Python **50–100/day**；TypeScript 40–80；Go/Rust 30–60；weekly All 400–600。AFFiNE 案例：约 200 stars/day 第 5 天上榜，上榜后 300–500 stars/day | **极低**：16 stars 的仓库需要一天几十到上百 star，必须多渠道路径同一 48h 叠加 |
| **awesome-dsh-plugin** | `dsh plugin add` 可安装、描述与实际一致、分类正确、持续维护；PR 欢迎；会逐条核对源码 | 0 | 2–4h 写条目 + PR；维护 1h/月 | 列表 **24,227 stars / 7,858 forks**；它同时是 DSH `Plugins → Discover` 的 npm 索引源（`dsh-plugin-catalog`）。具体 UV 未查到 | **高**：这是 DSH 生态内最精准的“货架”，比 GitHub Trending 现实得多 |
| **r/LocalLLaMA** | 853,150 成员；1/10 自推规则；必须披露 affiliation；禁止低质/纯 LLM 生成内容；账号年龄 30 天（第三方数据） | 0 | 2 周养号 + 每帖 3h，约 15–20h | 未查到该 sub 的公开 UV；Prowlo 2026-09 抽样：Show & tell 占 7%，平均 1,270 分（样本可能有偏，仅作参考） | **中**：受众最匹配音频/本地 AI；但对营销极敏感 |
| **r/SideProject** | 786,890 成员；明确欢迎 self-promo；50 karma + 14 天账号（第三方数据）；要上下文，纯落地页会被删 | 0 | 2h/帖 | 顶部帖约 **1,000 uniques**；普通帖约 **200 uniques**（makers.page） | **中**：门槛低，但流量天花板也低 |
| **r/ClaudeAI** | 1,046,485 成员；50 karma + 30 天；只允许“用 Claude/为 Claude 做”的项目，免费可试、少营销、无 referral | 0 | 2 周养号 + 3h | 未查到公开 UV | **低**：`ear` 是 DSH Skill，不是 Claude 项目，定位不匹配 |
| **r/ChatGPTCoding** | 389,702 成员；自推只能在指定 thread，或通过 modmail 申请 sponsorship | 0 | 低 | 未查到 | **低**：主 feed 基本不能发 |
| **r/AI_Agents** | 408,449 成员；链接放评论、项目放 weekly thread；1/10 规则 | 0 | 2 周养号 + 2h | 未查到 | **中低**：有 weekly thread，但曝光有限 |
| **X / Twitter** | 0 followers = 没有 in-network；For You 依靠 Phoenix 检索、SimClusters、popular posts；有 new-author boost，但 out-of-network 有折扣；只保留 48h 内帖子 | 0（Premium 价格未查到） | 10h/周，持续 3 个月 | 未查到 0 粉冷启动的公开带量数据 | **低**：发推几乎没人看；唯一可行是去大账号评论区做高质量回复 |
| **TLDR AI** | 1.1M 订阅；广告制；未查到公开免费投稿入口 | 第三方推算 **$11k–16.5k/次**（$10–15/千订阅），官方不公开报价 | 1–2h 询价 | 41% 平均打开率；具体 UV 未查到 | **低**：个人项目买不起 |
| **Ben's Bites** | 118k–120k 订阅；单 slot 约 **$3,500**；Season 合作 **$75k–100k** | $3,500 起 | 1–2h | 40% 打开率；UV 未查到 | **低**：$3,500 对免费 Skill 不划算 |
| **Hacker Newsletter** | 60,000+ 订阅；人工从 HN 每周精选；未查到直接付费投放 | 0 | 0（前提是 HN 上首页） | 未查到按渠道 UV；本质是 HN 的二次分发 | **中**：是 Show HN 的衍生，不是独立渠道 |
| **Console.dev** | 30k+ 订阅；免费推荐工具；不接 sponsored review；要求 self-serve signup + 清晰文档 | 0 | 1–2h 邮件 | 未查到 UV | **中低**：编辑制，命中率看匹配 |
| **Changelog News** | 免费提交链接；赞助 **$1,500/周**；不收教程/商业产品（开源项目可试） | 0 或 $1,500/周 | 1h | 未查到 | **中低** |
| **The AI Report** | 400k+ 订阅、51% 打开；广告制，2027 档期 | 价格未公开 | 1h | UV 未查到 | **低**：面向管理者，不是开发者工具 |
| **LibHunt / AlternativeTo** | 免费提交/认领；自动索引 GitHub | 0 | 1–2h | 未查到公开 UV | **低中**：长期 SEO 外链，短期带量弱 |
| **Discord / Slack** | 各服务器规则未查到；OpenAI Discord 需通过官方帮助页申请访问 | 0 | 5h/周 | 未查到 | **低**：除非有明确 #show-your-project 频道，否则不建议作为主渠道 |

---

## 2. Show HN：可操作要点

### 2.1 规则（官方 + 社区共识）

- 官方：Show HN 只用于“你做的、别人能玩的东西”。博客、newsletter、落地页、waitlist、筹款页都不算；如果必须登录/付费才能用，要在正文说明。见 [Show HN Guidelines](https://news.ycombinator.com/showhn.html)。
- 一个产品基本只有一次 Show HN；小版本更新不算“substantive”。重复发会被当 duplicate 杀掉，通常要等约一年。
- 标题格式：`Show HN: Ear – turn audio into a queryable timeline for LLM agents`。不要形容词、不要“revolutionary/AI-powered platform”；标题是资格筛选，不是广告。发布后 2 小时内可编辑。
- 可以带链接；最好直接链 GitHub repo 或可运行 demo，不要链 landing page。
- 发布后作者必须在线。官方要求“be around to discuss”；社区共识是前 3–4 小时回复所有评论。
- 不要请人 upvote。HN 的 vote-ring 检测会直接让帖子停止排名，且没有申诉。也不要用 AI 生成评论（官方 guidelines 已明确 HN 是人与人的对话）。

### 2.2 时间：数据支持的最优窗口

14 年、188,085 条 Show HN 的分析（[Show HN by the Numbers](https://danfking.github.io/blog/2026/04/23/show-hn-by-the-numbers/)）：

| 时段（UTC） | 拿到 50+ 分的概率 |
|---|---|
| **周一 00:00（周日 16:00–17:00 PT）** | **10.8%** |
| 周日 02:00 | 9.8% |
| 周六 19:00 | 9.2% |
| 周四 06:00 | 2.6% |

对你在中国的实际意义：**周一 00:00 UTC = 北京时间周一 08:00**。这是少数“美国周日晚 + 中国周一早”都醒着的窗口，发完可以守 4 小时。另一个常见建议是 Tue–Thu 8–10am ET，但对应北京时间 21:00–23:00，且竞争更挤；数据上不如周日晚/周一凌晨。

### 2.3 上首页的必要条件

没有官方“首页概率”。可用的代理指标：

- 中位数 **2 分**；90 分位 **24 分**；99 分位 **263 分**；**50+ 约 top 6%**。
- 排名公式（公开多年）：`score = (points - 1) / (hours + 2)^1.8`。前 60–90 分钟的 upvote 速度几乎决定一切。
- 社区观察（非官方）：前 30–60 分钟拿到 **10–30 个真实 upvote**，通常足以进入首页竞争；同样票数拖到 6 小时就无效。
- 评论数不预测 star（r≈0.10）；评论多但分数低会触发“overheated discussion”降权。不要制造争论。
- 账号：**发 Show HN 不需要 karma**。31 karma 才能 flag/vouch，501 才能 downvote 评论。新账号/零评论历史会被 anti-abuse 多看一眼；你的 2013 年账号年龄是优势，但最好提前 2–4 周在相关帖子里留下真实评论。
- “shadowban”：HN 没有公开的 shadowban 术语，实际表现是帖子变 `[dead]` 或被 `[flagged]`。在 profile 里开 `showdead` 才能看到；发完用无痕窗口检查是否在 /new 里。不要删帖重发。

### 2.4 实际带量

- 首页：广泛引用 **5k–30k uniques/24h**，但来源很弱、方差极大。一个真实上首页的 postmortem 只记录到 **~500 HN uniques、~6k pageviews**（[Indie Hackers](https://www.indiehackers.com/post/front-page-of-hn-the-full-postmortem-traffic-lessons-surprises-cbe9e0a7f6)）。
- 未上首页：10–50 分通常只有“几十次访问”（[LaunchBuff](https://launchbuff.com/blog/is-hacker-news-show-hn-worth-it)）；中位数 2 分基本等于没有。
- Star 转化：**约 1.4 GitHub stars / HN upvote**；**92% 的 star 在 48h 内完成**；HN 分数只能解释约 **8%** 的 star 方差。100 分 ≈ 100–150 stars，500 分 ≈ 500–700 stars。
- 竞争：2025 年 **28,302** 条 Show HN；2026 H1 **25,968** 条（约 142/天）。2026 H1 只有 **7.8%** 的帖子到 10+ 分（2024 H2 是 14.5%）。

### 2.5 对 `ear` 的具体建议

- 标题候选：`Show HN: Ear – turn audio into a queryable timeline for LLM agents`。不要写“offline”如果 basic 仍需 Qwen key。
- 第一条评论（约 200 词）：你是谁、为什么做、技术路径（Omni 粗时间轴 + BEATs 40ms refine + Qwen ASR）、最有趣的非显然点（40ms 事件 refine / 统一时钟）、**明确限制**（1 小时未实测、Qwen key、只做离线文件）、一个真问题（“你更想要逐字稿还是可查询的事件时间轴？”）。
- 必须有 60 秒 GIF/视频：`ear listen` 输入 → `hearing.md` 时间轴 → `ear digest` 查询。HN 大多数人不会装 Python 包。
- 先做无 key 可跑路径：`--no-asr --no-events --force-beats` 或预生成 sample 输出；否则“can't try without DASHSCOPE_API_KEY”会变成 top comment。
- 坑：不要在帖子里说“Please upvote”；不要把同一链接第二天再发；不要用 AI 写回复；不要在评论里和“为什么不用 Whisper”争论，直接给对比表。

---

## 3. Product Hunt：可操作要点

- **Featured 是生死线**：2026 年只有约 **10%** 的 launch 被 featured（2020–2023 是 60–98%）。未 featured 的 launch 即使有 300 upvote，也只有 **100–500 visitors**。
- 排名要素：vote quality（账号历史）、前 4 小时 velocity、评论深度、maker 回复速度。Product of the Day 约 **450–1,200** 质量加权 upvote；周四可能 900+，周日 450 也可能拿第一。
- 不能直接求 upvote。合规说法：“We just launched on Product Hunt. If you have used it, I'd love your honest take in the comments.” 用“评论”替代“投票”。
- 素材：240×240 GIF 缩略图、1270×760 画廊至少 4 张、60–90 秒 demo、60 字符以内 tagline（动词 + 对象 + 结果）。
- 时间：12:01 AM PT 上线（北京时间 16:01），9am–9pm PT 全程回复（北京时间次日 01:00–09:00），对中国个人开发者是硬成本。
- 带量：top3 5k–15k visitors / 100–400 signups；4–10 名 1k–3k / 30–100；11–30 名 300–700 / 10–30；未 featured 100–500 / 1–15。60% 流量在 day 0，48h 后基本结束；转化 1–5%；调查中只有约 11% 的创始人愿意再发一次。
- 对 `ear`：不建议第一站。PH 受众偏“逛产品”，不是“装 CLI 的开发者”；且没有邮件列表/社群时，前 4 小时无法启动。等 `ear` 有一批真实用户和 demo 视频后再考虑。

---

## 4. GitHub Trending：实际机制与门槛

### 4.1 机制

- GitHub 不公开 Trending 算法；官方社区讨论也只确认“综合近期 star/fork/浏览等信号”，没有公式。见 [GitHub Community #163970](https://github.com/orgs/community/discussions/163970)。
- 可观察到的核心：**24–48 小时 star 增速**，不是总 star 数；分 daily / weekly / monthly；可按语言筛选；另有 spoken language 筛选（含 Chinese）。
- 中文榜存在，但受众主要是中文用户，与“海外宣发”目标相反；未查到中文榜的公开 star 门槛。

### 4.2 门槛（第三方估算，非官方）

来自 AFFiNE 联创的复盘（[dev.to](https://dev.to/iris1031/how-to-get-on-github-trending-the-algorithm-the-tactics-and-the-real-data-o5b)）：

| 榜单 | Daily 估算 | Weekly 估算 |
|---|---|---|
| All Languages | **80–150 stars/day** | 400–600/week |
| Python | **50–100/day** | 250–400/week |
| TypeScript | 40–80/day | 200–350/week |
| Go / Rust | 30–60/day | 150–250/week |
| JavaScript | 60–120/day | 300–500/week |

- AFFiNE 案例：day 5 约 **200+ stars/day** 首次上 All Languages；上榜后自然增长 **300–500 stars/day**；5 个月上榜 28 次。
- 对 `ear`：16 stars 的仓库要在一天内拿 50–100 stars（Python 榜）才有现实机会。单靠一条 HN 不够；需要 HN + Reddit + awesome 列表 + X 在同一 48h 叠加。
- 不要买 star。GitHub 会按账号年龄/活跃度打折，star-history 上也很明显。

### 4.3 README / demo 对转化的影响

- 一项对 10,000 个 README 的分析（[dev.to](https://dev.to/0012303/i-analyzed-10000-github-readmes-the-top-repos-all-do-this-596n)）：10K+ stars 仓库 **89%** 有截图/GIF；100–1K 是 45%；<10 stars 只有 12%。一行安装命令的比例是 94% / 67% / 34%。
- 这是**相关性，不是因果**；不能换算成“加 GIF 提升 X%”。但方向明确：hero GIF、一句话价值、5 行内 quick start、明确 license，是转化前提。
- `ear` README 已经有架构图、实测数字（5 分钟 22.5s、13× 实时）、限制，这比大多数 16-star 仓库强；缺的是**顶部 10 秒 demo** 和**无 key 可跑路径**。

### 4.4 `#dsh` / `dsh-plugin` topic 的真实作用

- 它们是真实且极度拥挤的 topic：`dsh-plugin` **29,615** 个仓库，其中 **27,729** 个 ≤10 stars；`dsh` **16,968** 个。
- Topic 的作用是**分类和搜索信号**，不是分发。Topic 页面按热度/star 排序，16-star 仓库不会出现在任何人的视野里。
- 正确用法：`dsh-plugin` + `dsh` + `deepseek-harness` + `audio` / `speech-to-text` / `llm` 作为元数据；真正的曝光靠 curated index。
- **最高杠杆的 GitHub 动作：给 `awesome-dsh-plugin` 提 PR**。它 24,227 stars、7,858 forks，并且是 DSH `Plugins → Discover` 的 npm 索引源（`https://cdn.jsdelivr.net/npm/dsh-plugin-catalog/index.json`）；收录标准是“`dsh plugin add` 能装、描述属实、分类正确、持续维护”，有 **Voice & Audio** 分类，和 `ear` 完美匹配。见 [awesome-dsh-plugin](https://github.com/awesome-dsh-plugin/awesome-dsh-plugin)。
- 次选：`0xsline/awesome-deepseek-harness`（1,344 stars）、`hashgraph-online/awesome-ai-plugins`（1,022 stars）。
- 提醒：列表明确说“收录≠安全审计”；你也要在 README 里写清第三方代码风险。

---

## 5. Reddit：分版规则与内容形式

### 5.1 各版现状（2026 年中第三方抓取，规则会变，发前重读）

| 子版 | 成员 | 自推规则 | 对 `ear` 的判断 |
|---|---|---|---|
| r/LocalLLaMA | 853,150 | 1/10 规则；披露 affiliation；禁低质/纯 LLM 文案；30 天账号 | **最匹配**：本地音频、Whisper 替代、时间轴 |
| r/ClaudeAI | 1,046,485 | 50 karma + 30 天；只允许“用 Claude/为 Claude 做”的项目，免费可试、少营销、无 referral | 不匹配（DSH 不是 Claude） |
| r/ChatGPTCoding | 389,702 | 自推只能在指定 thread，或 modmail 申请 sponsorship | 主 feed 不能发 |
| r/AI_Agents | 408,449 | 链接放评论；项目放 weekly thread；1/10 | 可试 weekly thread，曝光有限 |
| r/SideProject | 786,890 | 明确欢迎；50 karma + 14 天；要上下文 | 门槛最低，流量天花板 ~1k uniques |
| r/opensource | 389,972 | 未查到明确自推规则；promo tolerance 未评估 | 先观察，别首发 |

Reddit 站级规则：90/10（90% 社区参与、10% 自推）；2026 年对 49 个 founder 子版的规则分析：**39% 完全禁止自推、22% 只允许 9:1、37% 个案审批、只有 1 个（r/SideProject）明确欢迎**。见 [makers.page](https://makers.page/blog/launch-on-reddit-without-getting-banned) 和 [RedShip](https://redship.io/blog/reddit-self-promotion-rules)。

### 5.2 什么内容能被接受

- 有效：`I built X because I hit Y. Here's what broke, what I'd do differently, and a demo.` 先问题、再方案、再限制、最后链接；开头就披露“I built this”。
- 无效：标题像 press release、正文只有 landing page、链接在标题 + 正文重复 3 次、跨 5 个版同一天发同一段文字。
- 图片/视频帖在 feed 里比纯链接帖更容易被看到；但 `ear` 的核心是 CLI 输出，建议“终端录屏 GIF + 一段 hearing.md 截图”。
- 发完守 3 小时，回复每条评论；作者消失的帖子 20 分钟内就会沉。

### 5.3 实际带量

- r/SideProject 顶部帖约 **1,000 uniques**，普通帖约 **200 uniques**。
- r/LocalLLaMA 的公开 UV 未查到；它的体量更大、匹配度更高，但负面情绪也更强（Prowlo 给的 sentiment 是 negative，仅作参考）。
- 转化通常好于 PH：读完了 4 段问题描述再点进来的人，比在 PH 上随手点 upvote 的人更精准。

### 5.4 坑

- 新账号直接发 = 最容易被 AutoMod/spam filter 吃；先花 2 周在目标版真实评论，攒 comment karma（不是 link karma）。
- 同一天跨版发同一内容 = 最明显的 spam 信号；一个版、一天、一帖。
- 被删先判断：几秒内删 = AutoMod；20 分钟后带理由 = 人；只有你能看到 = shadowban/spam filter。用无痕窗口验证。
- 不要在评论里 DM 每个回复者；不要用第二个账号 upvote；不要用短链。

---

## 6. X / Twitter：0 粉冷启动

- 机制（X 官方开源算法，2026-08 更新）：For You = in-network（你关注的人）+ out-of-network（Phoenix 向量检索、SimClusters、popular posts）。0 followers 意味着没有 in-network，只能靠 out-of-network 检索；新账号有 **new-author boost**，但 out-of-network 本身有折扣，且只保留 48 小时内的帖子。见 [xai-org/x-algorithm](https://github.com/xai-org/x-algorithm)。
- 模型预测的是 favorite / reply / repost / quote / share / click / dwell / video view / follow / negative 等概率的加权和；**reply、dwell、video view** 权重高，report/block 是负权重。
- 0 粉能做的：去 10–20 个相关大账号（如 @simonw、@karpathy、@_akhaliq、@huggingface、@swyx、@HamelHusain、@deepseek_ai）的评论区，用“补充一个具体实现/数据”的方式回复，而不是 “check out my project”。你的回复会出现在他们的 thread 里，这是唯一稳定的冷启动曝光。
- 内容形式：60 秒 screen recording + 一条具体结论（“5 分钟音频，22.5 秒出 40ms 事件时间轴”）> 纯文字 thread > 链接。
- 未查到 0 粉账号发 launch tweet 的公开带量数据；不要把 X 当第一周的流量来源，它是 3 个月维度的复利渠道。
- 坑：不要一次 @ 一堆大账号；不要每条推都带链接；不要买粉；Premium 的价格/是否值得开，未查到 2026 年官方价格页，暂不建议先买。

---

## 7. Newsletter / 聚合站

| 渠道 | 订阅/打开 | 投稿方式 | 费用 | 判断 |
|---|---|---|---|---|
| TLDR AI | 1.1M / 41% | 广告询价；未查到免费投稿入口 | 第三方推算 $11k–16.5k/次 | 不投 |
| Ben's Bites | 118k–120k / 40% | 单 slot 在线预订；Season 合作邮件 | $3,500/slot；Season $75k–100k | 不投（除非有收入） |
| Hacker Newsletter | 60k+ | 从 HN 每周精选，无独立投稿 | 0 | 先把 HN 做好 |
| Console.dev | 30k+ | hello@console.dev 推荐；不接 sponsored review | 0 | 值得试，编辑制 |
| Changelog News | 未查到 | /news/submit；开源项目可试 | 0 或 $1,500/周赞助 | 值得试 |
| The AI Report | 400k+ / 51% | 广告；2027 档期 | 未公开 | 受众是管理者，不匹配 |
| Product Hunt newsletter | 未查到 | 只有 featured 产品会进 | 0 | 取决于 PH featured |
| LibHunt | 未查到 | 免费提交/认领 | 0 | 做外链，不指望量 |
| AlternativeTo | 未查到 | 免费提交 | 0 | 同上 |
| Awesome lists | 看列表 | PR | 0 | **优先 awesome-dsh-plugin** |

- 所有“实际 UV”都未查到公开按渠道数据；只拿到订阅数和打开率。不要相信“发一次 newsletter 带几千 UV”的说法，除非对方给后台截图。
- 投稿 pitch 模板：1 句是什么 + 1 句为什么现在值得写 + 1 个可验证的数字 + 链接 + 是否免费/open source。不要附件，不要超过 150 词。
- 坑：付费 newsletter 对免费开源 Skill 基本不可能回本；编辑制渠道命中率低，但成本只有 1–2 小时，值得广撒 5–10 家。

---

## 8. Discord / Slack

- 未查到 Anthropic、OpenAI、DeepSeek、LangChain 等官方服务器当前允许自推的明确频道和规则；OpenAI 的 Discord 需要通过官方帮助页申请访问。各服务器普遍有 `#show-your-work` / `#community-projects` 类频道，但是否允许链接、是否只看不改，必须进服务器读规则。
- 实际效果未查到公开数据。对个人开发者，Discord 更适合“找 5 个真实用户聊需求”，不适合作为曝光渠道。
- 如果要做：先加入 r/AI_Agents 的 Discord（其 sidebar 有 invite），或 DSH 相关社区；观察 3 天，只在有人问“音频/时间轴/转写”时回答，不主动发链接。

---

## 9. 30 天执行顺序（建议）

**第 0 周：修转化，不发帖**
1. 录 60 秒 GIF：`ear listen` → `hearing.md` 时间轴 → `ear digest` 查询。
2. 提供无 key 可跑路径（sample 输出或 `--no-asr`），README 顶部写清“本地层不需要 key；Omni/ASR 需要 DASHSCOPE_API_KEY”。
3. 把“离线”改成准确表述：`local-first`，并列出哪些组件在本地、哪些在云端。
4. 加一张对比表：Whisper / 普通转写 vs `ear` 的结构化时间轴 + 事件 + 音乐。

**第 1 周：铺货架**
5. 给 `awesome-dsh-plugin` 提 PR（Voice & Audio 分类），条目写“install command + 一句话 + 真实限制”。
6. 补 topics：`dsh-plugin`、`dsh`、`deepseek-harness`、`audio`、`speech-to-text`、`llm`、`developer-tools`。
7. 开始每天 30 分钟在 HN / r/LocalLLaMA 评论（不发自己的链接）。

**第 2 周：准备首发**
8. 写 Show HN 标题 + 第一条评论（200 词，含限制）。
9. 邮件 pitch Console.dev、Changelog News（各 1 封，150 词内）。
10. 准备 Reddit 两个版本：r/LocalLLaMA 技术版、r/SideProject 故事版；不要同一天发。

**第 3 周：Show HN**
11. 周一 08:00 北京时间（周一 00:00 UTC）发 Show HN；守到 12:00。
12. 当天不发 Reddit；只在 X 发一条 demo 视频 + 数据。
13. 根据 HN 评论修 README/限制，第二天再回复一轮。

**第 4 周：Reddit + 二次分发**
14. 周二/周三发 r/LocalLLaMA（Show & tell 风格）；隔 2 天发 r/SideProject。
15. 拿 HN/Reddit 的真实反馈，再 pitch 一轮 newsletter（带“上周 HN 首页/xx 分”的社会证明）。
16. PH 暂缓；等有 100+ 邮件列表或真实用户再考虑。

**预算**：¥0–300（域名/分析工具可选）。不建议买 TLDR/Ben's Bites；$3,500 的 Ben's Bites slot 对一个免费 Skill 是负 ROI。

---

## 10. 未查到 / 低置信度清单

- HN 首页的精确概率、官方流量区间：未查到；只有分数分布和零散 postmortem。
- HN 前 30–60 分钟“10–30 upvote”的门槛：社区观察，不是官方规则。
- Reddit 各 sub 的公开 UV：未查到；只有 r/SideProject 的 ~1k/~200 uniques。
- X 0 粉账号的 launch 带量、X Premium 2026 价格：未查到。
- TLDR 官方报价：不公开；$11k–16.5k 是第三方按 CPM 推算。
- AI Tool Report 的投稿/价格：未查到（本报告查的是 The AI Report）。
- GitHub Trending 官方算法与精确 star 门槛：未公开；表中是第三方估算。
- `dsh` / `dsh-plugin` topic 带来的实际 referral UV：未查到。
- Discord/Slack 各服务器的自推规则、成员数、实际效果：未查到。
- LibHunt / AlternativeTo 的实际 UV：未查到。

---

## 11. 主要来源

- HN 官方规则：[Show HN](https://news.ycombinator.com/showhn.html)、[Guidelines](https://news.ycombinator.com/newsguidelines.html)、[FAQ](https://news.ycombinator.com/newsfaq.html)
- HN 数据分析：[Show HN by the Numbers (2026-04)](https://danfking.github.io/blog/2026/04/23/show-hn-by-the-numbers/)、[Show HN 竞争加剧 (2026-10)](https://dev.to/pennyforgehq/your-odds-of-getting-any-traction-on-show-hn-have-fallen-by-a-third-your-odds-of-getting-real-28eb)、[HN 发布指南](https://makers.page/blog/launch-on-hacker-news-show-hn)、[最佳时间](https://blog.alcazarsec.com/tech/posts/best-time-to-post-on-hacker-news)
- HN 带量案例：[Indie Hackers postmortem](https://www.indiehackers.com/post/front-page-of-hn-the-full-postmortem-traffic-lessons-surprises-cbe9e0a7f6)、[LaunchBuff](https://launchbuff.com/blog/is-hacker-news-show-hn-worth-it)
- Product Hunt：[makers.page 2026 指南](https://makers.page/blog/how-to-launch-on-product-hunt)
- GitHub Trending：[AFFiNE 复盘](https://dev.to/iris1031/how-to-get-on-github-trending-the-algorithm-the-tactics-and-the-real-data-o5b)、[GitHub Community #163970](https://github.com/orgs/community/discussions/163970)、[Topics 文档](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)
- DSH 生态：[awesome-dsh-plugin](https://github.com/awesome-dsh-plugin/awesome-dsh-plugin)、[dsh-plugin topic](https://github.com/topics/dsh-plugin)
- README 数据：[10,000 READMEs](https://dev.to/0012303/i-analyzed-10000-github-readmes-the-top-repos-all-do-this-596n)
- Reddit：[r/LocalLLaMA 分析](https://reddifier.com/free-subreddit-analysis-tool/r/LocalLLaMA)、[Prowlo stats](https://prowlo.com/tools/subreddit-stats/localllama)、[Reddit 自推规则](https://redship.io/blog/reddit-self-promotion-rules)、[Reddit 发布指南](https://makers.page/blog/launch-on-reddit-without-getting-banned)
- X：[x-algorithm](https://github.com/xai-org/x-algorithm)
- Newsletter：[TLDR AI](https://tldr.tech/ai)、[TLDR 广告](https://advertise.tldr.tech/)、[TLDR 价格推算](https://sponsorships.ai/blog/tldr-advertising-cost)、[Ben's Bites](https://www.bensbites.com/)、[Ben's Bites 合作](https://partner.bensbites.com/)、[Hacker Newsletter](https://hackernewsletter.com/)、[The AI Report](https://www.theaireport.ai/)、[DevHunt 67 渠道表](https://devhunt.org/promote)
