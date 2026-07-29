# GitHub Stars Curator

A Codex skill for curating GitHub starred repositories into stable, meaningful GitHub Stars Lists.

The skill supports:

- fetching a starred-repository inventory with `gh`;
- downloading READMEs into a local review corpus;
- classifying repositories into a reusable taxonomy;
- auditing live GitHub list drift before writeback;
- planning and applying GitHub Stars List updates safely.

## Install

Clone this repository into your Codex skills directory:

```powershell
git clone https://github.com/Leexunhuan743/github-stars-curator.git "$env:USERPROFILE\.codex\skills\github-stars-curator"
```

Restart Codex or reload skills so the `github-stars-curator` skill is discovered.

## Requirements

- Python 3
- GitHub CLI (`gh`)
- authenticated `gh` session with a token scope that includes `user`
- PyYAML

Install PyYAML if needed:

```powershell
python -m pip install pyyaml
```

## Safety model

GitHub Stars Lists are updated through GitHub GraphQL mutations. Before writeback, this skill performs dry-run planning and can audit live cloud drift so local ledgers do not silently overwrite list edits made in the GitHub UI or another client.

See [SKILL.md](SKILL.md) for the agent-facing operating instructions.

---

# GitHub Stars Curator 中文说明

这是一个 Codex skill，用来把 GitHub starred repositories 整理成稳定、清晰、可长期维护的 GitHub Stars Lists。

它适合处理这些任务：

- 拉取你的 GitHub stars 清单；
- 下载所有 starred repo 的 README，形成本地语义审阅语料；
- 根据 README 和仓库元数据进行分类，而不是只靠关键词；
- 维护一套可复用 taxonomy；
- 在写回 GitHub 前审计云端列表漂移，避免本地旧 ledger 覆盖你在网页端手动改过的列表；
- 先生成 dry-run plan，再安全写回 GitHub Stars Lists。

## 安装

把仓库 clone 到 Codex skills 目录：

```powershell
git clone https://github.com/Leexunhuan743/github-stars-curator.git "$env:USERPROFILE\.codex\skills\github-stars-curator"
```

然后重启 Codex，或重新加载 skills，让 `github-stars-curator` 被发现。

## 依赖

- Python 3
- GitHub CLI：`gh`
- 已登录的 `gh` 账号
- GitHub token scope 需要包含 `user`
- PyYAML

如果缺少 PyYAML：

```powershell
python -m pip install pyyaml
```

## 安全模型

GitHub Stars Lists 的写回会通过 GitHub GraphQL mutation 完成。这个 skill 的核心原则是：先审阅、再计划、最后写回。

尤其重要的是云端漂移审计：

- 每次写回前都应该读取 GitHub 当前 live memberships；
- 不依赖用户主动说明是否在网页端手动改过列表；
- 如果本地 ledger 和云端状态不一致，要先合并云端修改，或使用只包含本次目标 repo 的窄增量 ledger；
- 不要直接用旧的完整 ledger 覆盖云端状态；
- 任何非预期 `listsToRemove` 都应该视为暂停检查信号。

详细的 agent 操作规程见 [SKILL.md](SKILL.md)。
