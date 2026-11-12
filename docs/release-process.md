# 发布流程：npm 有延迟，不要重复发包

> 2026-11-12 记录。以后遇到 npm 版本“看起来没发出去”，先按这里检查，不要立刻改版本重发。

## 1. 正常现象

- `npm publish` 返回 `+ agent-ear@x.y.z` 或 `202`，只代表 npm **已接收**；
- `npm view agent-ear version` 可能还会在**几分钟到十几分钟**内显示旧版本；
- `https://registry.npmjs.org/agent-ear` 的 `dist-tags.latest` 也可能滞后；
- **不要**因为 `npm view` 没变就 bump 版本重发，否则会制造 0.2.9/0.2.10 这种“已上传但未显示”的版本堆积。

## 2. 验证顺序

```bash
npm view agent-ear version
npm view agent-ear@<version> version dist.tarball bin
curl -s https://registry.npmjs.org/agent-ear | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d["dist-tags"], "<version>" in d["versions"])'
```

确认 `bin`：

```bash
npx -y --package=agent-ear@<version> agent-ear --help
```

## 3. 如果出现 staged publishing

npm 账号可能启用 **staged publishing**：

- `npm publish` 可能只把版本放进 **Staged Packages**；
- 需要维护者在 npmjs.com → Settings → Staged Packages 用 2FA **Approve**；
- 批准前，`latest` 不会指向新版本；
- 不要重复 `npm publish`，会得到 `E409 previously staged version`。

## 4. 发布后给种子用户的命令

固定版本，避免缓存/延迟：

```bash
npx -y agent-ear@<version> setup
```

## 5. 本次事实

- npm 0.2.9/0.2.10 都是延迟后出现的，不是没发出去；
- 0.2.10 最终成为 `latest`，`bin` 正常；
- 以后先等，再验证，再决定是否真的需要新版本。
