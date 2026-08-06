# worktreeとagentの原則（詳細）

大規模作業とagent利用が必要かどうかは、SKILL.md本体の「大規模作業とagent」節の
基準で判定する。ここでは、利用が決まった後の具体的な原則を記載する。

## worktreeとagentの原則

- 配置先は原則として`<repo>/worktrees/<task-slug>`とする。
- 1つのagentにつき、1つのブランチと1つのworktreeを割り当てる。
- 複数agentに同じworktreeや同じファイル群を同時編集させない。
- 各agentには目的、対象範囲、受け入れ条件、対象外、検証方法を個別に渡す。
- 各agentはworktree内の`AGENTS.md`と`CLAUDE.md`を読み、担当範囲だけを変更する。
- 依存する作業は無理に並列化せず、先行作業の完了後に開始する。
- agentの結果はCodexが集約し、Claudeが統合前にレビューできる形で報告する。

worktree作成とブランチ作成は計画承認に含めてよいが、対象と名称を計画に明記する。
commit、merge、rebase、cherry-pick、push、PR作成は別途承認を得る。
worktreeの削除は、変更が保存・統合済みであることを確認し、対象を提示して承認を得てから行う。

## 役割分離（Team Lead / Worker）

[Findy Library — Agentic Workflow: Implement in parallel](https://lib.findy.co.jp/ai/agentic-workflow#implement-in-parallel)
の整理を借りると、この体制は次の役割分離に対応する。

- **Team Lead（判断・分析、コードは書かない）**：Claudeが担う。依存関係の分析、
  worktree・agentの分担決定、layer間のマージゲート、統合順序の判断。
- **Worker（実装のみ）**：Codexと実装agentが担う。担当worktreeでの実装、
  自己レビュー、報告、worktreeの後片付け。

依存関係のないagent群は同じlayerとして並列実行し、依存があるagentは前のlayerの
完了・統合後に開始する。この「layer内は並列、layer間は直列」という構造は、
既存の「独立した作業だけを並列化し、依存関係がある作業は順番に実行する」という
原則と同じものを指す。
