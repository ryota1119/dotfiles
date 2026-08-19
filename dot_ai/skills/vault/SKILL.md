---
name: vault
description: Access, search, save, ingest, research, or review the user's Obsidian Knowledge Vault from any working directory. The Vault goes by several names — Knowledge Vault, exocortex, Exocortex, エクソコルテックス, 第二の脳, second brain, vault — and all of them mean this one Vault. Use whenever the request touches it, or long-term knowledge in general: saving something for later, recalling what is known, filing a source, or auditing the Vault. Also triggers on: 「exocortexに保存」「第二の脳に保存」「Vaultに入れて」「exocortexを見て」「第二の脳から探して」.
---

# Knowledge Vault Gateway

This skill is a router only. It contains no knowledge-management logic.
The Vault's own `AGENTS.md` and `.ai/` directory are authoritative.

## 1. Resolve the Vault

Read the Vault root from the environment variable `KNOWLEDGE_VAULT`.

If it is unset, stop and ask the user for the Vault path. Never guess it and
never infer the Vault's structure from global assumptions.

## 2. Load the Vault's rules

Read `$KNOWLEDGE_VAULT/AGENTS.md` before doing anything else.
Treat it as authoritative and higher priority than this file.

**Never write to the Vault before loading the Vault's own rules and the
applicable workflow.**

## 3. Confirm writability, if the request writes

Reads need no check. Before the first write:

- Claude Code: the Vault must be an accessible directory. If it is outside the
  session's working directories, start the session with `--add-dir "$KNOWLEDGE_VAULT"`.
- Codex: writing outside the current workspace requires `workspace-write` plus the
  Vault registered in `sandbox_workspace_write.writable_roots` in
  `~/.codex/config.toml`, or launching with `--add-dir "$KNOWLEDGE_VAULT"`.

If a write fails with `Operation not permitted`, stop, report the required
startup configuration, and keep the content in the reply so it is not lost.
Do not write it somewhere else instead.

Note: outside the Vault, the host does **not** auto-load the Vault's `AGENTS.md`,
`.claude/skills/`, or `.agents/skills/`. Reading those files directly, as this
skill does, is the only path.

## 4. Classify the request and read the matching workflow

| Request | Workflow |
|---|---|
| search, ask, recall, "what do we know about…" | No skill. Follow the reading order in `AGENTS.md`. |
| save useful information from this session | `.ai/skills/vault-save/SKILL.md` |
| ingest source material (file, URL, inbox) | `.ai/skills/vault-ingest/SKILL.md` |
| research a topic not yet in the Vault | `.ai/skills/vault-research/SKILL.md` |
| review or audit Vault quality | `.ai/skills/vault-review/SKILL.md` |

Retrieval is a reading discipline, not a workflow: read `hot.md`, then `index.md`,
then search, then the relevant Knowledge, then its wikilinks, and Sources only when
a claim itself must be checked. Never load the whole Vault.

Paths are relative to `$KNOWLEDGE_VAULT`. If the workflow file does not exist yet,
say so and fall back to `AGENTS.md` alone rather than improvising a structure.

## 5. Follow it

Read the selected `SKILL.md` in full and follow it before performing any write.

## Prohibited from a global session

Without going through the workflow above:

- creating notes in `20_Knowledge/`
- rewriting `90_System/hot.md` or `90_System/index.md`
- converting a Source into Knowledge
- integrating or merging existing Knowledge
- changing the Vault's structure
