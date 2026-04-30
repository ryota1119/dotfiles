# Neovim Configuration

モダンで効率的なNeovim開発環境の設定です。lazy.nvimをベースに、LSP、補完、ファジーファインダー、Git統合などの機能を提供します。

## 📋 目次

- [必要要件](#必要要件)
- [インストール](#インストール)
- [構成](#構成)
- [プラグイン](#プラグイン)
- [キーマップ](#キーマップ)
- [LSP設定](#lsp設定)
- [カスタマイズ](#カスタマイズ)
- [トラブルシューティング](#トラブルシューティング)

## 🚀 必要要件

- **Neovim** >= 0.9.0
- **Git** >= 2.19.0
- **Node.js** >= 14.0（一部のLSPやフォーマッターで必要）
- **Python** >= 3.6（一部のLSPで必要）
- **Nerd Font**（アイコン表示に必要）推奨: [Hack Nerd Font](https://www.nerdfonts.com/)
- **ripgrep** (live grepに必要)
- **fd** (ファイル検索の高速化、オプション)
- **lazygit** (Git TUIに必要)

### macOS

```bash
brew install neovim git node python ripgrep fd lazygit
brew tap homebrew/cask-fonts
brew install --cask font-hack-nerd-font
```

### Ubuntu/Debian

```bash
sudo apt install neovim git nodejs npm python3 ripgrep fd-find
# lazygitは別途インストールが必要
```

## 📦 インストール

### 1. 既存の設定をバックアップ（必要な場合）

```bash
mv ~/.config/nvim ~/.config/nvim.backup
mv ~/.local/share/nvim ~/.local/share/nvim.backup
mv ~/.local/state/nvim ~/.local/state/nvim.backup
mv ~/.cache/nvim ~/.cache/nvim.backup
```

### 2. この設定をクローン（または既に配置済み）

```bash
git clone <your-repo-url> ~/.config/nvim
```

### 3. Neovimを起動

```bash
nvim
```

初回起動時、**lazy.nvim**が自動的にインストールされ、全てのプラグインがインストールされます。

## 📁 構成

```
~/.config/nvim/
├── init.lua                    # エントリーポイント
├── lua/
│   ├── config/
│   │   ├── options.lua         # エディタの基本設定
│   │   ├── keymaps.lua         # キーマップ設定
│   │   ├── autocmds.lua        # 自動コマンド
│   │   ├── lazy.lua            # lazy.nvimの初期化
│   │   └── lsp.lua             # LSPのグローバル設定
│   └── plugins/
│       ├── core/               # コアプラグイン
│       ├── editor/             # エディタ拡張
│       ├── git/                # Git統合
│       ├── lsp/                # LSP関連
│       ├── navigation/         # ナビゲーション
│       └── ui/                 # UI/テーマ
└── after/
    └── lsp/                    # 言語サーバー個別設定
```

## 🔌 プラグイン

### コア

| プラグイン | 説明 |
|-----------|------|
| [lazy.nvim](https://github.com/folke/lazy.nvim) | 高速なプラグインマネージャー |
| [plenary.nvim](https://github.com/nvim-lua/plenary.nvim) | Lua関数ライブラリ |
| [nvim-web-devicons](https://github.com/nvim-tree/nvim-web-devicons) | ファイルアイコン |

### エディタ拡張

| プラグイン | 説明 |
|-----------|------|
| [nvim-treesitter](https://github.com/nvim-treesitter/nvim-treesitter) | シンタックスハイライト・コード解析 |
| [nvim-autopairs](https://github.com/windwp/nvim-autopairs) | 括弧の自動閉じ |
| [indent-blankline](https://github.com/lukas-reineke/indent-blankline.nvim) | インデントガイド表示 |
| [which-key.nvim](https://github.com/folke/which-key.nvim) | キーマップヘルプ表示 |
| [markdown-preview.nvim](https://github.com/iamcco/markdown-preview.nvim) | Markdownプレビュー |
| [Comment.nvim](https://github.com/numToStr/Comment.nvim) | コメント操作 |
| [nvim-surround](https://github.com/kylechui/nvim-surround) | 括弧・引用符操作 |

### ナビゲーション

| プラグイン | 説明 |
|-----------|------|
| [telescope.nvim](https://github.com/nvim-telescope/telescope.nvim) | ファジーファインダー |
| [oil.nvim](https://github.com/stevearc/oil.nvim) | バッファベースのファイラー |

### LSP

| プラグイン | 説明 |
|-----------|------|
| [nvim-lspconfig](https://github.com/neovim/nvim-lspconfig) | LSP設定 |
| [mason.nvim](https://github.com/williamboman/mason.nvim) | LSP/DAP/Linterインストーラー |
| [mason-lspconfig.nvim](https://github.com/williamboman/mason-lspconfig.nvim) | masonとlspconfigの統合 |
| [mason-tool-installer.nvim](https://github.com/WhoIsSethDaniel/mason-tool-installer.nvim) | ツール自動インストール |
| [blink.cmp](https://github.com/saghen/blink.cmp) | 補完エンジン |
| [conform.nvim](https://github.com/stevearc/conform.nvim) | フォーマッター |

### Git

| プラグイン | 説明 |
|-----------|------|
| [gitsigns.nvim](https://github.com/lewis6991/gitsigns.nvim) | Git差分表示・操作 |
| [lazygit.nvim](https://github.com/kdheepak/lazygit.nvim) | LazyGit統合 |

### UI

| プラグイン | 説明 |
|-----------|------|
| [backpack.nvim](https://github.com/mitch1000/backpack.nvim) | カラースキーム |
| [lualine.nvim](https://github.com/nvim-lualine/lualine.nvim) | ステータスライン |
| [bufferline.nvim](https://github.com/akinsho/bufferline.nvim) | バッファライン |
| [noice.nvim](https://github.com/folke/noice.nvim) | コマンドライン・通知UI |

## ⌨️ キーマップ

> **リーダーキー**: `Space`

### 基本操作

| キー | モード | 説明 |
|------|--------|------|
| `<leader>w` | Normal | ファイル保存 |
| `<leader>q` | Normal | 終了 |
| `<leader>h` | Normal | 検索ハイライト解除 |
| `j` / `k` | Normal | 表示行単位で移動 |

### ウィンドウ操作

| キー | モード | 説明 |
|------|--------|------|
| `<C-h>` / `<C-j>` / `<C-k>` / `<C-l>` | Normal | ウィンドウ間移動 |
| `<C-Up>` / `<C-Down>` | Normal | ウィンドウの高さ変更 |
| `<C-Left>` / `<C-Right>` | Normal | ウィンドウの幅変更 |
| `<leader>sv` | Normal | 垂直分割 |
| `<leader>sh` | Normal | 水平分割 |

### バッファ操作

| キー | モード | 説明 |
|------|--------|------|
| `<S-h>` | Normal | 前のバッファ |
| `<S-l>` | Normal | 次のバッファ |
| `<leader>bd` | Normal | バッファを閉じる |

### 編集操作

| キー | モード | 説明 |
|------|--------|------|
| `<` / `>` | Visual | インデント調整（選択維持） |
| `J` / `K` | Visual | 選択行を上下移動 |
| `p` | Visual | ペースト（ヤンクを保持） |

### Telescope（ファイル検索）

| キー | モード | 説明 |
|------|--------|------|
| `<leader>ff` | Normal | ファイル検索 |
| `<leader>fg` | Normal | 文字列検索（grep） |
| `<leader>fb` | Normal | バッファ一覧 |
| `<leader>fh` | Normal | ヘルプタグ検索 |
| `<leader>fr` | Normal | 最近使用したファイル |
| `<leader>fc` | Normal | コマンド検索 |
| `<leader>fk` | Normal | キーマップ検索 |
| `<leader>fs` | Normal | 現在のバッファ内検索 |

#### Telescope内のキーマップ

| キー | モード | 説明 |
|------|--------|------|
| `<C-j>` / `<C-k>` | Insert | 選択移動 |
| `<CR>` | Insert/Normal | 選択して開く |
| `<C-x>` | Insert/Normal | 水平分割で開く |
| `<C-v>` | Insert/Normal | 垂直分割で開く |
| `<C-t>` | Insert/Normal | タブで開く |
| `<C-u>` / `<C-d>` | Insert/Normal | プレビュースクロール |
| `<Tab>` / `<S-Tab>` | Insert/Normal | 複数選択 |

### Oil（ファイラー）

| キー | モード | 説明 |
|------|--------|------|
| `-` | Normal | 親ディレクトリを開く |
| `<CR>` | Oil | ファイル/ディレクトリを開く |
| `<C-s>` | Oil | 垂直分割で開く |
| `<C-h>` | Oil | 水平分割で開く |
| `<C-p>` | Oil | プレビュー |
| `g.` | Oil | 隠しファイル表示切替 |
| `g?` | Oil | ヘルプ表示 |

### Git

| キー | モード | 説明 |
|------|--------|------|
| `<leader>lg` | Normal | LazyGit起動 |
| `]c` | Normal | 次の変更箇所 |
| `[c` | Normal | 前の変更箇所 |
| `<leader>hp` | Normal | ハンクをプレビュー |
| `<leader>hs` | Normal/Visual | ハンクをステージング |
| `<leader>hr` | Normal/Visual | ハンクをリセット |
| `<leader>hS` | Normal | バッファ全体をステージング |
| `<leader>hu` | Normal | ステージングを取り消し |
| `<leader>hb` | Normal | 行のブレイムを表示 |
| `<leader>tb` | Normal | 行ブレイム表示切替 |
| `<leader>hd` | Normal | 差分を表示 |

### コメント（Comment.nvim）

| キー | モード | 説明 |
|------|--------|------|
| `gcc` | Normal | 行コメント切り替え |
| `gc` + motion | Normal | 範囲をコメント（例: `gcap`で段落） |
| `gc` | Visual | 選択範囲をコメント |
| `gbc` | Normal | ブロックコメント切り替え |
| `gcO` | Normal | 上に新しいコメント行追加 |
| `gco` | Normal | 下に新しいコメント行追加 |
| `gcA` | Normal | 行末にコメント追加 |

### サラウンド（nvim-surround）

| キー | モード | 説明 |
|------|--------|------|
| `ys{motion}{char}` | Normal | 囲み文字を追加（例: `ysiw"`で単語を`""`で囲む） |
| `ds{char}` | Normal | 囲み文字を削除（例: `ds"`で`""`を削除） |
| `cs{old}{new}` | Normal | 囲み文字を変更（例: `cs"'`で`""`を`''`に変更） |
| `S{char}` | Visual | 選択範囲を囲む |

**使用例:**
- `ysiw"` → `word` を `"word"` に
- `yss)` → 行全体を `(...)` で囲む
- `ds"` → `"word"` から `"` を削除
- `cs"'` → `"word"` を `'word'` に変更
- `cs)]` → `(word)` を `[word]` に変更

### LSP

| キー | モード | 説明 |
|------|--------|------|
| `gd` | Normal | 定義へジャンプ |
| `gD` | Normal | 宣言へジャンプ |
| `gr` | Normal | 参照を表示 |
| `gi` | Normal | 実装へジャンプ |
| `K` | Normal | ホバー情報を表示 |
| `<C-k>` | Insert | シグネチャヘルプを表示 |
| `<leader>rn` | Normal | シンボルをリネーム |
| `<leader>ca` | Normal | コードアクションを表示 |
| `<leader>cf` | Normal/Visual | コードをフォーマット |
| `[d` | Normal | 前の診断へ |
| `]d` | Normal | 次の診断へ |
| `<leader>e` | Normal | 診断をフロートウィンドウで表示 |

### 補完（blink.cmp）

| キー | モード | 説明 |
|------|--------|------|
| `<CR>` | Insert | 補完を確定 |
| `<C-n>` | Insert | 次の候補 |
| `<C-p>` | Insert | 前の候補 |
| `<C-space>` | Insert | 補完メニューを表示 |
| `<C-e>` | Insert | 補完を閉じる |
| `<C-b>` / `<C-f>` | Insert | ドキュメントをスクロール |
| `<Tab>` | Insert | スニペット次のフィールド |
| `<S-Tab>` | Insert | スニペット前のフィールド |

### Which-key

| キー | モード | 説明 |
|------|--------|------|
| `<leader>?` | Normal | バッファ固有のキーマップを表示 |

リーダーキーを押すと、自動的に利用可能なキーマップが表示されます。

## 🛠️ LSP設定

### インストール済みLSP

自動的にインストールされるLSP:

- **lua_ls** - Lua
- **ruby_lsp** - Ruby
- **basedpyright** - Python (型チェック・補完)
- **ruff** - Python (lint・format・import 整理)
- **ts_ls** - TypeScript/JavaScript
- **terraformls** - Terraform

### 新しいLSPの追加

1. `lua/plugins/lsp/mason-lspconfig.lua`の`ensure_installed`に追加:

```lua
ensure_installed = {
  "lua_ls",
  "ruby_lsp",
  "basedpyright",
  "ruff",
  "ts_ls",
  "terraformls",
  "rust_analyzer",  -- 例: Rust
},
```

2. 必要に応じて`after/lsp/`に個別設定ファイルを作成

### フォーマッター

`conform.nvim`で自動フォーマットが設定されています。

**サポートされている言語:**
- Lua (stylua)
- Python (ruff: lint + format + import 整理を一本化)
- JavaScript/TypeScript (prettier)
- Ruby (rubocop)
- Go (goimports, gofmt)
- Rust (rustfmt)
- その他多数

**フォーマッター追加方法:**

`lua/plugins/lsp/conform.lua`を編集:

```lua
formatters_by_ft = {
  lua = { "stylua" },
  python = { "ruff_organize_imports", "ruff_format" },
  -- 新しい言語を追加
  rust = { "rustfmt" },
},
```

## 🎨 カスタマイズ

### カラースキームの変更

`lua/plugins/ui/colorscheme.lua`を編集:

```lua
return {
  'mitch1000/backpack.nvim',
  config = function ()
    require('backpack').setup({
      theme = "dark", -- dark, light, palette
      contrast = "high", -- medium, high, extreme
    })
  end,
}
```

または、別のカラースキームに変更:

```lua
return {
  "catppuccin/nvim",
  name = "catppuccin",
  priority = 1000,
  config = function()
    vim.cmd.colorscheme("catppuccin")
  end,
}
```

### エディタ設定の変更

`lua/config/options.lua`を編集して、お好みの設定に変更できます:

```lua
opt.number = true          -- 行番号表示
opt.relativenumber = true  -- 相対行番号（お好みで）
opt.tabstop = 4            -- タブ幅を4に変更
opt.shiftwidth = 4         -- インデント幅を4に変更
```

### キーマップの追加

`lua/config/keymaps.lua`にカスタムキーマップを追加:

```lua
keymap("n", "<leader>t", ":TestNearest<CR>", opts)
```

### プラグインの追加

`lua/plugins/`内の適切なディレクトリに新しいLuaファイルを作成:

```lua
-- lua/plugins/editor/new-plugin.lua
return {
  "author/plugin-name",
  event = "VeryLazy",
  config = function()
    require("plugin-name").setup()
  end,
}
```

Neovimを再起動すると、lazy.nvimが自動的に新しいプラグインをインストールします。

## 🎯 ターミナルからの便利な使い方

### Markdownプレビュー

ターミナルから直接Markdownファイルをプレビューするシェル関数を提供しています。

**セットアップ:**

`~/.zsh/functions.zsh`に以下の関数が追加されています。シェルを再読み込みしてください：

```bash
source ~/.zshrc
```

**使用可能な関数:**

#### 1. `mdp` - Markdownファイルをプレビュー

```bash
mdp README.md
```

指定したMarkdownファイルをNeovimで開き、自動的にプレビューを起動します。

#### 2. `mdp-fzf` - fzfでMarkdownファイルを選択してプレビュー

```bash
mdp-fzf
```

カレントディレクトリ以下のすべてのMarkdownファイルを検索し、fzfで選択してプレビューを開きます。
プレビューウィンドウでファイル内容を確認できます（`bat`が必要）。

#### 3. `mdnew` - 新しいMarkdownファイルを作成

```bash
mdnew note.md
# または拡張子なしでも自動的に.mdが追加されます
mdnew note
```

テンプレート付きの新しいMarkdownファイルを作成し、Neovimで開いてプレビューを起動します。

**必要なツール:**
- `fzf` - ファジーファインダー（`mdp-fzf`で使用）
- `bat` - シンタックスハイライト付きファイルビューアー（プレビューで使用、オプション）

```bash
brew install fzf bat
```

## 🐛 トラブルシューティング

### プラグインが正しく読み込まれない

```vim
:Lazy sync
:Lazy clean
:Lazy update
```

### LSPが動作しない

1. LSPがインストールされているか確認:
```vim
:Mason
```

2. LSP情報を確認:
```vim
:LspInfo
```

3. Mason経由で手動インストール:
```vim
:MasonInstall lua-language-server
```

### フォーマッターが動作しない

1. フォーマッターがインストールされているか確認:
```vim
:Mason
```

2. Conform情報を確認:
```vim
:ConformInfo
```

### ログの確認

```vim
:messages          " Neovimメッセージ
:checkhealth       " 健全性チェック
:checkhealth lazy  " lazy.nvimの健全性チェック
```

### キャッシュのクリア

```bash
rm -rf ~/.local/share/nvim
rm -rf ~/.local/state/nvim
rm -rf ~/.cache/nvim
```

その後、Neovimを再起動してプラグインを再インストールします。

## 📚 参考リンク

- [Neovim Documentation](https://neovim.io/doc/)
- [lazy.nvim](https://github.com/folke/lazy.nvim)
- [Mason.nvim](https://github.com/williamboman/mason.nvim)
- [nvim-lspconfig](https://github.com/neovim/nvim-lspconfig)
- [Telescope.nvim](https://github.com/nvim-telescope/telescope.nvim)

## 📝 ライセンス

MIT License

---

**Enjoy coding with Neovim! 🚀**
