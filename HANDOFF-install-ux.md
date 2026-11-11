# 交接：install UX 修复（agent-ear v0.2.2 待发）

> 2026-11-11　分支 `fix/install-ux` 已合并进 `main`（merge commit `2792b8e`）。
> 起因：macOS 干净 HOME 验证，三个断点让用户「装完跑不起来」。

---

## 改了什么

| # | 文件 | 改动 |
|---|---|---|
| 1 | `skills/agent-ear/scripts/agent-ear` / `.cmd` / `.ps1` | 先探测 CLI，缺失时打印安装指引并 `exit 127`（原来直接 `exec: agent-ear: not found`） |
| 2 | `ear/setup.py` | `--non-interactive --skip-key` 现在真的跳过 Key（原来仍强制要 key）；`run()` 容忍空 key 并给出补配提示 |
| 3 | `ear/install.py` | 新增 `skill_health(installed, wrapper_ok, cli_present)` 与 `HEALTH_LABEL`；`list_skills()` 增加 `wrapper_ok` / `cli_present` / `health` |
| 4 | `ear/doctor.py` | skill 行不再是假的 OK，改为 `OK` / `-` / `BROKEN` / `NO-CLI` |
| 5 | `README.md` | 安装段顶部加「先装 CLI 再装 skill」的前置说明 |
| 6 | `ear/_data/skill/**` | `scripts/sync-skill.py` 同步后的包内副本 |
| 7 | `tests/test_install_ux.py` | 新增 12 条回归测试 |

测试：`41 passed`（原 29 + 新增 12）。

---

## 已在本机验证

在 `HOME=/tmp/earclean2` 的全新环境里，用本地构建的 wheel 走了一遍：

```
agent-ear setup --target claude --non-interactive --skip-key --skip-api-check
  → 跳过 Key 配置（--skip-key）。稍后可运行 `agent-ear setup` 补上
  → skill claude: OK /tmp/earclean2/.claude/skills/agent-ear
  → exit 0
```

CLI 不在 PATH 时：

```
agent-ear doctor
  → skill claude: NO-CLI (先装 CLI： uv tool install agent-ear) /tmp/.../claude/skills/agent-ear
```

模拟「只装了 skill」的用户：

```
./scripts/agent-ear doctor
  → agent-ear CLI not found on PATH.
  → This skill is a thin wrapper; install the CLI first:
  →   uv tool install agent-ear ...
  → exit 127
```

---

## 还没做（维护者接手）

1. **版本号**：改 `pyproject.toml` → `0.2.2`，`CHANGELOG.md` 加一条，`git tag v0.2.2`。
2. **重新发布**：`uv build` + 上传 PyPI（0.2.1 已发，不能覆盖）。
3. **重新同步 skill 包**：`python3 scripts/sync-skill.py`（若之后再改 `skills/`）。
4. **`_write_wrappers` 补一道守卫**（可选）：`ear/install.py` 里生成的 wrapper 写的是绝对路径，若用户之后 `uv tool uninstall`，报错会很原始。可以在生成内容里也加一条 `test -x` 提示。
5. **`install.sh` 复核**：README 首推的 curl|sh 脚本没被这次改动覆盖，需确认它走 CLI+setup 的正确顺序。
6. **Windows 未实测**：`.cmd` / `.ps1` 只做了静态修改，没有真机验证（本机是 macOS）。

---

## 给 dsh-moss-live 的口径

它是 npm 插件（`dsh plugin add`），没有「skill 依赖外部 CLI」这层，**不需要同款修复**。但如果后续把 voice 能力也做成 skill，要避免同样的「薄包装 + 不装依赖」结构。

---

## 一个建议

三个问题里 **1 和 3 是同一类**：包装层假装自己是独立可运行的，而诊断工具又替它圆谎。
以后凡是发「薄包装」，都要满足两条：**缺失依赖时能自己说清楚缺什么**，**doctor 不能只检查目录存在**。
