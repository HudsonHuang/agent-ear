# Omni → 40ms AED 事件 refine（第一轮）

- 样本：5 个 score，34 个被 refine 的事件
- 标签分布：{'Laughter': 34}

| 指标 | start 位移 | end 位移 |
|---|---:|---:|
| median | +1520ms | -20ms |
| mean | +1225ms | -69ms |
| abs mean | 1274ms | 505ms |

## 解读

- Omni 的 onset 系统性偏早（median +1.5s），BEATs 把它推后；offset 基本对齐（median -20ms）。
- 这不是准确率；没有人工 onset/offset gold。它证明级联链路能改时间，且只在 Omni 提名的事件上改。
- refine 目前只覆盖 BEATs 447 类里能映射的标签（主要是 Laughter）；`bird chirping` / `spray hiss` 这类开放标签仍是 `omni-coarse`。
- 下一步：人工标 20 条 onset/offset 做真误差；补 Omni label → AudioSet 映射；映射不到时保留粗时间。

| 来源 | label | omni start→refined | omni end→refined |
|---|---|---|---|
| precise60 | Laughter | 7000→7240 | 9000→7960 |
| precise60 | Laughter | 9000→8880 | 11000→11200 |
| precise60 | Laughter | 18000→19840 | 20000→20000 |
| precise60 | Laughter | 22000→21280 | 24000→23680 |
| refine_sample300 | Laughter | 7000→8880 | 11000→11200 |
| refine_sample300 | Laughter | 15000→15480 | 17000→17560 |
| refine_sample300 | Laughter | 21000→21280 | 23000→23680 |
| refine_sample300 | Laughter | 30000→31520 | 32000→31960 |
| refine_sample300 | Laughter | 45000→47320 | 49000→47640 |
| refine_sample300 | Laughter | 56000→57600 | 59000→58720 |
| refine_sample300 | Laughter | 67000→68880 | 71000→71200 |
| refine_sample300 | Laughter | 75000→75480 | 77000→77560 |
| refine_sample300 | Laughter | 81000→81280 | 83000→83680 |
| refine_sample300 | Laughter | 90000→91520 | 92000→91960 |
| refine_sample300 | Laughter | 105000→107320 | 109000→107640 |
| refine_sample300 | Laughter | 116000→117600 | 119000→118720 |
| refine_sample300 | Laughter | 127000→128880 | 131000→131200 |
| refine_sample300 | Laughter | 135000→135480 | 137000→137560 |
| refine_sample300 | Laughter | 141000→141280 | 143000→143680 |
| refine_sample300 | Laughter | 150000→151520 | 152000→151960 |
| refine_sample300 | Laughter | 165000→167320 | 169000→167640 |
| refine_sample300 | Laughter | 176000→177600 | 179000→178720 |
| refine_sample300 | Laughter | 187000→188880 | 191000→191200 |
| refine_sample300 | Laughter | 195000→195480 | 197000→197560 |
| refine_sample300 | Laughter | 201000→201280 | 203000→203680 |
| refine_sample300 | Laughter | 210000→211520 | 212000→211960 |
| refine_sample300 | Laughter | 225000→227320 | 229000→227640 |
| refine_sample300 | Laughter | 236000→237600 | 239000→238720 |
| refine_sample300 | Laughter | 247000→248880 | 251000→251200 |
| refine_sample300 | Laughter | 255000→255480 | 257000→257560 |
| refine_sample300 | Laughter | 261000→261280 | 263000→263680 |
| refine_sample300 | Laughter | 270000→271520 | 272000→271960 |
| refine_sample300 | Laughter | 285000→287320 | 289000→287640 |
| refine_sample300 | Laughter | 296000→297600 | 299000→298720 |
