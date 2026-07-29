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

