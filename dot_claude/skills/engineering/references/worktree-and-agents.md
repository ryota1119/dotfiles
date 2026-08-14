# worktreeとagentの原則（詳細）

大規模作業とagent利用が必要かどうかは、SKILL.md本体の「大規模作業とworktree」節の
基準で判定する。ここでは、利用が決まった後の具体的な原則を記載する。

## worktreeとagentの原則

- 配置先は原則として`<repo>/worktrees/<task-slug>`とする。
- **1 agent=1 branch=1 worktree**を運用原則とする。
- 複数agentに同じworktreeや同じファイル群を同時編集させない。
- 各agentには目的、対象範囲、受け入れ条件、対象外、検証方法を個別に渡す。
- 各agentはworktree内の適用可能な指示ファイルを読み、担当範囲だけを変更する。
- 依存する作業は無理に並列化せず、先行作業の完了後に開始する。
- agentの結果は実装担当が集約し、レビュー担当が統合前に確認できる形で報告する。

worktree作成とブランチ作成は、対象と名称を計画に明記して承認を得る。commit、merge、
rebase、cherry-pick、push、PR作成は別途承認を得る。worktreeの削除は、変更が保存・統合済み
であることを確認し、対象を提示して承認を得てから行う。

## 役割分離（Lead / Worker）

- **Lead（判断・分析、コードは書かない）**：依存関係の分析、worktree・agentの分担決定、
  layer間の統合ゲート、統合順序の判断を担う。
- **Worker（実装のみ）**：担当worktreeでの実装、自己レビュー、報告、後片付けを担う。

依存関係のないagent群は同じlayerとして並列実行し、依存があるagentは前のlayerの完了・
統合後に開始する。layer内は並列、layer間は直列とし、独立した作業だけを並列化する。
