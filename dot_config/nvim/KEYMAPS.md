# Neovim Keymap 一覧

このドキュメントは、Neovim設定におけるkeymapの整理結果をまとめたものです。

## 📋 整理方針

### keymaps.lua に記述すべきもの

- 基本的なVim/Neovim操作（保存、終了、検索など）
- プラグインに依存しないグローバルな設定
- システムクリップボード連携
- 視覚モードでの選択範囲移動

### 各プラグインファイルに記述すべきもの

- そのプラグイン固有の機能に関するkeymap
- プラグインの`config`関数や`keys`オプション内で定義

---

## 🎯 グローバルキーマップ (lua/config/keymaps.lua)

### 基本操作

| キー | モード | 説明 |
|------|--------|------|
| `<leader>w` | Normal | ファイルを保存 |
| `<leader>q` | Normal | ウィンドウを閉じる |
| `<leader>Q` | Normal | すべてを強制終了 |

### 検索

| キー | モード | 説明 |
|------|--------|------|
| `n` | Normal | 次の検索結果（画面中央に表示） |
| `N` | Normal | 前の検索結果（画面中央に表示） |
| `*` | Normal | カーソル下の単語を検索（画面中央に表示） |
| `#` | Normal | カーソル下の単語を逆検索（画面中央に表示） |
| `<leader>h` | Normal | 検索ハイライトをクリア |

### 編集

| キー | モード | 説明 |
|------|--------|------|
| `<A-Up>` | Visual | 選択範囲を上に移動 |
| `<A-Down>` | Visual | 選択範囲を下に移動 |

### システムクリップボード

| キー | モード | 説明 |
|------|--------|------|
| `y` | Normal/Visual | システムクリップボードにヤンク |
| `Y` | Normal | 行末までシステムクリップボードにヤンク |
| `p` | Normal/Visual | システムクリップボードからペースト |
| `P` | Normal/Visual | システムクリップボードからカーソル前にペースト |

### LSP

| キー | モード | 説明 |
|------|--------|------|
| `<C-Space>` | Insert | LSP補完の手動トリガー |

---

## 🔌 プラグイン別キーマップ

### 📁 Telescope (lua/plugins/core/telescope.lua)

| キー | モード | 説明 |
|------|--------|------|
| `<leader>ff` | Normal | ファイル検索 |
| `<leader>fg` | Normal | 文字列検索（grep） |
| `<leader>fb` | Normal | バッファ一覧 |
| `<leader>fh` | Normal | ヘルプタグ検索 |

### 🌲 Neo-tree (lua/plugins/ui/neo-tree.lua)

| キー | モード | 説明 |
|------|--------|------|
| `<leader>ee` | Normal | Neo-treeを左に開く |
| `<leader>ef` | Normal | Neo-treeをフロートで開く |
| `<leader>et` | Normal | Neo-treeをトグル |
| `<leader>ec` | Normal | Neo-treeを閉じる |

### 📑 Barbar (lua/plugins/ui/barbar.lua)

#### バッファ移動

| キー | モード | 説明 |
|------|--------|------|
| `<A-,>` | Normal | 前のバッファへ |
| `<A-.>` | Normal | 次のバッファへ |
| `<A-1>` ~ `<A-9>` | Normal | 番号でバッファへ移動 |
| `<A-0>` | Normal | 最後のバッファへ |

#### バッファ操作

| キー | モード | 説明 |
|------|--------|------|
| `<A-<>` | Normal | バッファを前に移動 |
| `<A->>` | Normal | バッファを次に移動 |
| `<A-p>` | Normal | バッファをピン留め/解除 |
| `<A-c>` | Normal | バッファを閉じる |
| `<C-p>` | Normal | バッファピッカー |
| `<C-s-p>` | Normal | バッファピッカー（削除） |

#### バッファソート

| キー | モード | 説明 |
|------|--------|------|
| `<Space>bb` | Normal | バッファ番号順 |
| `<Space>bn` | Normal | 名前順 |
| `<Space>bd` | Normal | ディレクトリ順 |
| `<Space>bl` | Normal | 言語順 |
| `<Space>bw` | Normal | ウィンドウ番号順 |

### 🔀 Git (Gitsigns) (lua/plugins/git/gitsigns.lua)

| キー | モード | 説明 |
|------|--------|------|
| `]c` | Normal | 次のhunkへ |
| `[c` | Normal | 前のhunkへ |
| `<leader>hs` | Normal/Visual | hunkをステージ |
| `<leader>hr` | Normal/Visual | hunkをリセット |
| `<leader>hS` | Normal | バッファ全体をステージ |
| `<leader>hR` | Normal | バッファ全体をリセット |
| `<leader>hp` | Normal | hunkをプレビュー |
| `<leader>hi` | Normal | hunkをインラインプレビュー |
| `<leader>hb` | Normal | blame行を表示 |
| `<leader>hd` | Normal | diff表示 |
| `<leader>hD` | Normal | diff表示（HEAD） |
| `<leader>hq` | Normal | quickfixリストに追加 |
| `<leader>hQ` | Normal | すべてのhunkをquickfixリストに追加 |
| `<leader>tb` | Normal | blame行の表示トグル |
| `<leader>tw` | Normal | word diffトグル |
| `ih` | Operator/Visual | hunk選択（textobject） |

### 🦥 LazyGit (lua/plugins/git/lazygit.lua)

| キー | モード | 説明 |
|------|--------|------|
| `<leader>gg` | Normal | LazyGitを開く |
| `<leader>gF` | Normal | LazyGit（現在のファイル） |

### 🖥️ ToggleTerm (lua/plugins/ui/toggleterm.lua)

| キー | モード | 説明 |
|------|--------|------|
| `<C-\>` | Normal | ターミナルトグル |
| `<esc>` | Terminal | ターミナルモードを抜ける |
| `jk` | Terminal | ターミナルモードを抜ける |
| `<C-h/j/k/l>` | Terminal | ウィンドウ移動 |
| `<C-w>` | Terminal | ウィンドウコマンド |

### 🪟 Tmux Navigator (lua/plugins/ui/vim-tmux-navigator.lua)

| キー | モード | 説明 |
|------|--------|------|
| `<C-h>` | Normal | 左のペインへ |
| `<C-j>` | Normal | 下のペインへ |
| `<C-k>` | Normal | 上のペインへ |
| `<C-l>` | Normal | 右のペインへ |
| `<leader>tp` | Normal | 前のペインへ |

### 🔍 Trouble (lua/plugins/coding/trouble.lua)

| キー | モード | 説明 |
|------|--------|------|
| `<leader>xx` | Normal | 診断一覧トグル |
| `<leader>xX` | Normal | バッファ診断一覧トグル |
| `<leader>cs` | Normal | シンボル一覧 |
| `<leader>cl` | Normal | LSP定義/参照一覧 |
| `<leader>xL` | Normal | ロケーションリスト |
| `<leader>xQ` | Normal | Quickfixリスト |

### 🌳 Treesitter (lua/plugins/coding/treesitter.lua)

| キー | モード | 説明 |
|------|--------|------|
| `<leader>ts` | Normal | Treesitterアップデート |
| `<leader>th` | Normal | Treesitterハイライトトグル |
| `<CR>` | Visual | ノード選択開始/拡大 |
| `<TAB>` | Visual | スコープ拡大 |
| `<S-CR>` | Visual | ノード縮小 |

### 🔧 LSP (lua/lsp/init.lua)

| キー | モード | 説明 |
|------|--------|------|
| `gd` | Normal | 定義へジャンプ |
| `gD` | Normal | 宣言へジャンプ |
| `gi` | Normal | 実装へジャンプ |
| `gr` | Normal | 参照一覧 |
| `K` | Normal | ホバー情報表示 |
| `<leader>cf` | Normal | コードフォーマット |
| `<leader>cd` | Normal | 診断情報表示 |
| `[d` | Normal | 前の診断へ |
| `]d` | Normal | 次の診断へ |

### 📐 WinResizer (lua/plugins/ui/winresizer.lua)

| キー | モード | 説明 |
|------|--------|------|
| `<C-e>` | Normal | ウィンドウリサイズモード開始 |

### ❓ Which-key (lua/plugins/ui/which-key.lua)

| キー | モード | 説明 |
|------|--------|------|
| `<leader>` | Normal | キーマップナビゲーション表示（300ms後に自動表示） |
| `<leader>?` | Normal | バッファローカルキーマップ表示 |

#### グループ定義

- `<leader>f`: 🔍 Find (Telescope)
- `<leader>e`: 📁 Explorer (Neo-tree)
- `<leader>g`: 🔀 Git
- `<leader>h`: 📝 Git Hunks (Gitsigns)
- `<leader>x`: 🔧 Trouble/Diagnostics
- `<leader>c`: 💻 Code/LSP
- `<leader>t`: ⚙️ Toggle/Treesitter/Tmux
- `<Space>b`: 📑 Buffer Order

---

## ✅ 整理内容

### 🔧 第1回整理（初回）

#### 解消した重複・衝突

1. **LazyGit起動のkeymap重複**
   - ❌ 削除: `gitsigns.lua`の`<leader>gg`, `<leader>gF`
   - ✅ 保持: `lazygit.lua`の`<leader>gg`, `<leader>gF`

2. **`<C-\>`キーの衝突**
   - ✅ 優先: `toggleterm.lua`の`<C-\>`（ターミナルトグル）
   - ✅ 変更: `vim-tmux-navigator.lua`の`<C-\>` → `<leader>tp`

3. **Treesitterのkeymap配置**
   - ❌ 削除: `keymaps.lua`の`<leader>ts`, `<leader>th`
   - ✅ 移動: `treesitter.lua`に移動

### 🔍 第2回整理（全体スキャン）

#### 解消した重複・衝突

1. **🚨 `<leader>f`の重大な衝突**
   - ✅ 変更: LSPフォーマット `<leader>f` → `<leader>cf` (Code Format)
   - ✅ 保持: Telescopeグループ `<leader>f*` (Find)

2. **診断表示のキー変更**
   - ✅ 変更: `<leader>d` → `<leader>cd` (Code Diagnostic)
   - これにより`<leader>c`グループに統合

#### 追加した改善

3. **descriptionの追加**
   - ✅ `barbar.lua`: 全24個のkeymapにdescriptionを追加
   - ✅ `gitsigns.lua`: 全18個のkeymapにdescriptionを追加
   - ✅ `keymaps.lua`: 全13個のkeymapにdescriptionを追加
   - ✅ `lsp/init.lua`: 全9個のkeymapにdescriptionを追加

4. **which-key.nvimの設定充実**
   - グループ定義を追加（絵文字付き）
   - 自動ポップアップ表示（300ms）
   - モダンなUI設定

### コメントの追加（第1回）

- `keymaps.lua`: 役割を明確化し、セクション分けを追加
- 各プラグインファイル: keymap設定箇所に明確なコメントを追加

### 最終確認結果（第2回）

✅ **重複・衝突: ゼロ**
✅ **description不足: ゼロ**
✅ **不適切な配置: ゼロ**
✅ **Linterエラー: ゼロ**

全84個のkeymapが適切に整理され、すべてにdescriptionが付与されました。

---

## 📝 メンテナンスガイドライン

### 新しいkeymapを追加する際のルール

1. **プラグイン固有の機能**
   - 各プラグインファイルの`config`関数内または`keys`オプションに記述

2. **グローバルな操作**
   - `lua/config/keymaps.lua`に記述
   - プラグインに依存しない基本的なVim/Neovim操作のみ

3. **LSP関連**
   - `lua/lsp/init.lua`の`on_attach`関数内に記述

4. **重複チェック**
   - 新しいkeymapを追加する前に、既存のkeymapと重複していないか確認
   - `which-key`（`<leader>?`）で現在のkeymapを確認可能

### コーディング規約

- `desc`オプションを付けて、keymapの説明を記述する
- セクションごとにコメントで区切る
- 関連するkeymapはグループ化する
