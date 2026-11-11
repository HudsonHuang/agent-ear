# 收录状态（2026-11-12）

| 渠道 | 状态 | 链接 / 下一步 |
|---|---|---|
| 1024Store | ✅ 已合并 | https://github.com/imsai-sh/awesome-deepseek-harness-plugins/pull/918 |
| dshbase | ⏳ 已提 issue | https://github.com/ylwl1997/dshbase/issues/324 |
| awesome-dsh-plugin | ⏳ 等满 1 天 | 入口文件已备：`submissions/awesome-dsh-plugin/HudsonHuang__agent-ear.yml`；仓库创建于 2026-11-11 06:30 UTC，满 1 天后提 PR |
| dshfind / dshmarket | ⏳ 等自动抓取 | 已打 `dsh-plugin` topic；每日同步，当前路由仍 404 |
| GitHub topics/description | ✅ 已补 | `agent-ear` repo |
| npm | ⚠️ 0.2.4 已发；0.2.5 等 2FA | `npm publish` 需要浏览器 OTP |
| PyPI | ✅ 0.2.5 | https://pypi.org/project/agent-ear/0.2.5/ |

## awesome-dsh-plugin PR 命令（满 1 天后）

```bash
# fork + clone
gh repo fork awesome-dsh-plugin/awesome-dsh-plugin --clone=true
cd awesome-dsh-plugin
cp /path/to/agent-ear/submissions/awesome-dsh-plugin/HudsonHuang__agent-ear.yml data/plugins/
npm ci
node scripts/generate-readme.mjs
git checkout -b add-agent-ear
git add data/plugins/HudsonHuang__agent-ear.yml README.md README.zh-CN.md
git commit -m 'Add agent-ear'
git push -u origin add-agent-ear
gh pr create --title 'Add agent-ear' --body '...'
```

注意：awesome-dsh-plugin 要求仓库创建满 1 天、commits ≥ 10、根包有非空 `dsh.bundle.patch`、描述与源码一致。
