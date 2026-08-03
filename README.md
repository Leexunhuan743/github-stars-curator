# GitHub Stars Curator

[**English**](#en) · [**中文**](#cn)

---

<a id="en"></a>

# GitHub Stars Curator

An agent skill (Codex, Claude Code, and other SKILL.md-compatible agents) that organizes the GitHub repositories you starred into stable, clear, long-term-maintainable lists.

## Features

- **Inventory refresh** — fetch the full starred-repo inventory and compute a delta (`newStars` / `removedStars`) against the previous snapshot.
- **README corpus** — download every repo's README into a local semantic review corpus with per-repo metadata stubs.
- **Classification** — an agent reads the READMEs (not just descriptions) and assigns repos to a reusable taxonomy; scripted recording with list-name validation.
- **General-purpose taxonomy** — a bundled 23-bucket taxonomy (personal software, AI/agent tooling, self-hosted services, developer infrastructure, and a fallback), extendable per workspace. A 500-repo probe and a 300-repo random sample both confirm ~90%+ reasonable placement of classifiable repos.
- **Bucket overload review** — when a bucket exceeds ~10% of the total star count (floor 30), the agent analyzes its contents, proposes concrete splits, and asks before creating new lists (recorded in the workspace taxonomy only).
- **Cloud drift audit** — read live GitHub list memberships before any writeback; live state wins when it differs from the local ledger.
- **Safe writeback** — offline plan → online plan (review `planHash`) → apply with an approved plan; unmanaged lists are preserved by default, and deleting any list requires explicit user approval.

## Install

Clone this repository into your agent's skills directory:

```powershell
# Codex (Windows)
git clone https://github.com/Leexunhuan743/github-stars-curator.git "$env:USERPROFILE\.codex\skills\github-stars-curator"

# Claude Code
git clone https://github.com/Leexunhuan743/github-stars-curator.git "$env:USERPROFILE\.claude\skills\github-stars-curator"

# macOS / Linux (any SKILL.md-compatible agent)
git clone https://github.com/Leexunhuan743/github-stars-curator.git ~/.claude/skills/github-stars-curator
```

The skill's five scripts are plain Python + `gh` and run anywhere; `SKILL.md` follows the shared skill format, so agents that load SKILL.md skills (Claude Code, Cursor, Windsurf, and similar) can use it. `agents/openai.yaml` is Codex-specific interface metadata and is ignored by other agents.

Restart or reload your agent so the `github-stars-curator` skill is discovered.

## Requirements

- Python 3
- GitHub CLI (`gh`)
- authenticated `gh` session with a token scope that includes `user`
- PyYAML

Install PyYAML if needed:

```powershell
python -m pip install pyyaml
```

## Quick start

```powershell
# 1. refresh the inventory and delta
python scripts/fetch_star_inventory.py --out-dir "<workspace>"

# 2. fetch READMEs (incremental: --only-new-from "<workspace>/github-stars-delta.json")
python scripts/fetch_readmes.py --inventory "<workspace>/github-stars.json" --out-dir "<workspace>/star-readmes"

# 3. (agent) read READMEs, classify, record with:
python scripts/write_classification.py --classifications records.json --out-dir "<workspace>" --ledger-name incremental-20260802-ledger

# 4. validate locally, then review the online plan
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/complete-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>" --offline-plan
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/complete-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>"

# 5. apply the reviewed plan
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/complete-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>" --apply --approved-plan "<workspace>/github-stars-sync-plan.json"
```

## Scripts

- `fetch_star_inventory.py` — fetch stars and compute the delta (`github-stars.json`, `github-stars-delta.json`, `github-stars-summary.json`).
- `fetch_readmes.py` — download READMEs into `star-readmes/raw/` and merge per-repo metadata stubs.
- `write_classification.py` — record agent classifications into meta files and emit a ledger; validates list names against the taxonomy; `--merge-into-full` merges a narrow ledger back into the full record with a snapshot.
- `audit_cloud_drift.py` — read-only live-vs-ledger drift audit before writeback; exit code 0 = no drift, non-zero = reconcile.
- `apply_user_lists.py` — offline plan / online plan / apply (creates missing lists in taxonomy order, updates descriptions and memberships, writes an audit journal).

## Taxonomy

The bundled `references/taxonomy-template.yaml` defines 23 buckets: downloaders, cloud-drive-transfer-sync, clipboard-tools, media-players, agent-tools, ai-agents, dev-tools, terminal, windows-tools, desktop-apps, reading-notes, pdf-document-tools, references-guides, self-hosted, cloudflare-network-proxy, frameworks-libraries, data-ml-tools, game-3d-creative, design-assets, business-apps, web-scraping-data-collection, security-pentest-tools, everything-else.

A workspace can extend it by copying the template to `<workspace>/taxonomy.yaml` and adding lists there (e.g. `video-downloaders`, `agent-skills` were added this way after a bucket overload review). The 32-list GitHub cap is enforced at plan time.

## Safety model

- **Plan, review, then mutate.** Every writeback goes through offline plan → online plan (review `planHash`) → apply with `--approved-plan`; a tampered or stale plan is refused.
- **Live state is the newest fact.** Cloud drift is checked proactively before writeback; local ledgers never silently overwrite manual cloud edits.
- **Unmanaged lists are preserved by default.** Lists outside the loaded taxonomy are left alone; when they are discovered, the user is asked whether to delete them, and deletion happens only with explicit approval.
- **Unexpected removals stop the flow.** Any `listsToRemove` outside the current request is a pause-and-review signal.
- **Human checkpoints.** Bucket overload, taxonomy drift, single-repo new lists, and auth gaps all pause for review.

## Tests

```powershell
cd scripts
python -m pytest tests/ -q
```

28 tests cover meta merging, incremental corpus preservation, ledger validation, plan-hash integrity, drift audit semantics, and classification recording — all offline (GitHub calls are mocked).

See [SKILL.md](SKILL.md) for the agent-facing operating instructions.

---

<a id="cn"></a>

---

# GitHub Stars Curator 中文说明

这是一个 Agent 技能（兼容 Codex、Claude Code 等），用来把你 star/收藏 的 GitHub 仓库整理成稳定、清晰、可长期维护的列表。

## 功能

- **清单刷新**：拉取全部 star，计算与上次快照的增量（新增/移除）；
- **README 语料**：下载所有 repo 的 README 到本地，形成语义审阅语料；
- **分类**：agent 读 README（不是只看描述）把 repo 归入可复用 taxonomy，脚本化记录并校验列表名；
- **通用 taxonomy**：内置 23 桶（个人软件、AI/agent 工具、自托管服务、开发者基础设施、兜底桶），可按工作区扩展；500 个样本压力测试 + 300 个随机样本实测可判定仓库归位率 ~90%+；
- **桶超载审查**：某桶超过总 star 数约 10%（下限 30）时，agent 分析内容、提出拆分方案、询问后再建新列表（只记入工作区 taxonomy）；
- **云漂移审计**：写回前读取云端 live 成员关系，与本地 ledger 不一致时以 live 为准；
- **安全写回**：离线计划 → 在线计划（审阅 planHash）→ 凭批准计划 apply；unmanaged 列表默认保留，删除任何列表必须经用户明确同意。

## 安装

把仓库 clone 到你所用 agent 的 skills 目录：

```powershell
# Codex (Windows)
git clone https://github.com/Leexunhuan743/github-stars-curator.git "$env:USERPROFILE\.codex\skills\github-stars-curator"

# Claude Code
git clone https://github.com/Leexunhuan743/github-stars-curator.git "$env:USERPROFILE\.claude\skills\github-stars-curator"

# macOS / Linux（任何兼容 SKILL.md 的 agent）
git clone https://github.com/Leexunhuan743/github-stars-curator.git ~/.claude/skills/github-stars-curator
```

5 个脚本是纯 Python + `gh`，与平台无关；`SKILL.md` 采用通用 skill 格式，因此 Claude Code、Cursor、Windsurf 等加载 SKILL.md 的 agent 都能使用。`agents/openai.yaml` 是 Codex 特有的接口元数据，其他 agent 会忽略它。

重启或重新加载 agent，让 `github-stars-curator` 被发现。

## 依赖

- Python 3
- GitHub CLI：`gh`（已登录，token scope 含 `user`）
- PyYAML

```powershell
python -m pip install pyyaml
```

## 快速上手

```powershell
# 1. 刷新清单与增量
python scripts/fetch_star_inventory.py --out-dir "<workspace>"

# 2. 抓 README（增量用 --only-new-from "<workspace>/github-stars-delta.json"）
python scripts/fetch_readmes.py --inventory "<workspace>/github-stars.json" --out-dir "<workspace>/star-readmes"

# 3. （agent）读 README 分类后用脚本记录
python scripts/write_classification.py --classifications records.json --out-dir "<workspace>" --ledger-name incremental-20260802-ledger

# 4. 离线计划 → 在线计划（审阅 planHash）
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/complete-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>" --offline-plan
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/complete-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>"

# 5. 凭批准计划写回
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/complete-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>" --apply --approved-plan "<workspace>/github-stars-sync-plan.json"
```

## 脚本

- `fetch_star_inventory.py`：拉取清单并算增量（github-stars.json / delta / summary）；
- `fetch_readmes.py`：下载 README 语料并合并 meta 元数据；
- `write_classification.py`：记录分类到 meta 并生成 ledger，校验列表名；`--merge-into-full` 把窄增量合并回完整 ledger（先快照）；
- `audit_cloud_drift.py`：写回前只读漂移审计（exit 0 = 无漂移，非零 = 需协调）；
- `apply_user_lists.py`：离线/在线计划与 apply（按 taxonomy 顺序创建缺失列表、更新描述与成员、写审计 journal）。

## Taxonomy

内置 `references/taxonomy-template.yaml` 23 桶：downloaders、cloud-drive-transfer-sync、clipboard-tools、media-players、agent-tools、ai-agents、dev-tools、terminal、windows-tools、desktop-apps、reading-notes、pdf-document-tools、references-guides、self-hosted、cloudflare-network-proxy、frameworks-libraries、data-ml-tools、game-3d-creative、design-assets、business-apps、web-scraping-data-collection、security-pentest-tools、everything-else。

需要自定义时复制模板到 `<workspace>/taxonomy.yaml` 再添加（例如 `video-downloaders`、`agent-skills` 就是经桶超载审查后这样加的）。32 列表上限在计划阶段强制校验。

## 安全模型

- **先计划、再审阅、后写回**：离线计划 → 在线计划（审阅 planHash）→ 凭 `--approved-plan` apply；篡改或过期的计划会被拒绝；
- **live 状态是更新的事实**：写回前主动查云漂移，本地 ledger 绝不静默覆盖云端手动修改；
- **unmanaged 列表默认保留**：taxonomy 之外的云端列表不碰；发现时询问用户是否删除，删除仅凭明确同意；
- **意外移除即暂停**：请求之外的任何 `listsToRemove` 都是停止复查信号；
- **人工检查点**：桶超载、taxonomy 漂移、单 repo 新列表、鉴权不足都会暂停。

## 测试

```powershell
cd scripts
python -m pytest tests/ -q
```

28 个测试覆盖 meta 合并、增量语料保留、ledger 校验、planHash 完整性、漂移审计语义、分类记录——全部离线（GitHub 调用被 mock）。

详细的 agent 操作规程见 [SKILL.md](SKILL.md)。
