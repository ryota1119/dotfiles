# Neovim設定

このリポジトリは、Neovimの包括的な設定ファイルのコレクションです。モダンな開発環境を構築し、効率的なコーディング体験を提供します。

## 🚀 特徴

- **Lazy.nvim**による高速なプラグイン管理
- **LSP**による高度な言語サポート
- **Treesitter**による高速なシンタックスハイライト
- **Telescope**による強力なファジーファインダー
- **Neo-tree**によるファイルエクスプローラー
- **Lualine**による美しいステータスライン
- **Mason**によるツール管理

## 📁 ディレクトリ構造

```plaintext
lua/
├── config/           # 基本設定
│   ├── autocmds.lua # 自動コマンド
│   ├── keymaps.lua  # キーマッピング
│   ├── lazy.lua     # プラグイン管理
│   ├── lsp.lua      # LSP設定
│   └── options.lua  # Neovimオプション
└── plugins/          # プラグイン設定
    ├── core/         # コアプラグイン
    ├── ui/           # UI関連プラグイン
    ├── lsp/          # LSP関連プラグイン
    ├── coding/       # コーディング支援プラグイン
    ├── ai/           # AI関連プラグイン
    ├── git/          # Git関連プラグイン
    └── editor/       # エディタ機能プラグイン
```

## 🛠️ 主要プラグイン

### コア機能

- **lazy.nvim**: プラグイン管理
- **mason.nvim**: 言語サーバー・フォーマッター・リンターの管理
- **telescope.nvim**: ファジーファインダー

### UI/UX

- **tokyonight**: 美しいカラースキーム
- **lualine.nvim**: ステータスライン
- **neo-tree.nvim**: ファイルエクスプローラー
- **barbar.nvim**: タブバー
- **which-key.nvim**: キーバインド表示
- **dashboard-nvim**: スタートアップ画面

### LSP・開発支援

- **nvim-lspconfig**: LSP設定
- **lspsaga.nvim**: LSP UI拡張
- **mason-lspconfig**: MasonとLSPの統合
- **nvim-treesitter**: 高速シンタックス解析
- **trouble.nvim**: 診断情報表示
- **mason-null-ls**: フォーマッター・リンター統合

## ⌨️ 主要キーマッピング

### 基本操作

- `<leader>w`: ファイル保存
- `<leader>q`: ファイル終了
- `<leader>Q`: 強制終了

### ウィンドウ操作

- `<C-h/j/k/l>`: ウィンドウ間移動

### タブ操作

- `<leader>tn`: 新しいタブ
- `<leader>tc`: タブを閉じる
- `<leader>tl/th`: タブ間移動

### LSP操作

- `gd`: 定義にジャンプ
- `gr`: 参照を検索
- `gi`: 実装を検索
- `K`: ホバードキュメント
- `<leader>ca`: コードアクション
- `<leader>rn`: リネーム

### ファイル操作

- `<leader>e`: Neo-treeサイドバー切り替え
- `<leader>ef`: Neo-treeフロート切り替え

### 検索・診断

- `<leader>d`: ドキュメント診断
- `<leader>wd`: ワークスペース診断
- `<leader>h`: 検索ハイライト解除

## ⚙️ 設定オプション

### 基本設定

- 行番号表示
- マウスサポート
- クリップボード統合
- アンドゥ履歴保存

### インデント設定

- スペースによるインデント
- タブ幅: 2スペース
- スマートインデント

### 検索設定

- 大文字小文字を無視
- インクリメンタル検索
- 検索ハイライト

### パフォーマンス設定

- 遅延描画
- 更新間隔: 300ms

## 🚀 セットアップ

### 前提条件

- Neovim 0.9.0以上
- Git
- Node.js（一部のLSP用）

### インストール

1. リポジトリをクローン

```bash
git clone <repository-url> ~/.config/nvim
```

2. Neovimを起動

```bash
nvim
```

3. プラグインの自動インストールを待つ

### 初回起動時の注意

- 初回起動時はプラグインのダウンロードに時間がかかります
- Masonによるツールのインストールも自動で行われます

## 🔧 カスタマイズ

### プラグインの追加

`lua/plugins/`ディレクトリ内の適切なカテゴリに新しいプラグイン設定を追加してください。

### キーマッピングの変更

`lua/config/keymaps.lua`でキーマッピングをカスタマイズできます。

### オプションの変更

`lua/config/options.lua`でNeovimの基本オプションを変更できます。

## 📚 プラグイン別設定

### LSP設定

各言語のLSP設定は`lua/plugins/lsp/`ディレクトリ内で管理されています。

### カラースキーム

`lua/plugins/ui/colorscheme.lua`でカラースキームを変更できます。

### Treesitter

`lua/plugins/coding/treesitter.lua`でTreesitterの設定をカスタマイズできます。

## 🐛 トラブルシューティング

### プラグインが動作しない

1. `:Lazy sync`でプラグインを再同期
2. `:Lazy log`でエラーログを確認

### LSPが動作しない

1. Masonで言語サーバーがインストールされているか確認
2. `:Mason`でツールの状態を確認

### パフォーマンスの問題

1. 不要なプラグインを無効化
2. `:Lazy profile`でプラグインの読み込み時間を確認

## 🤝 貢献

この設定の改善提案やバグ報告は歓迎します。プルリクエストやイシューの作成をお気軽にお願いします。

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🙏 謝辞

この設定は以下の素晴らしいプラグインとその作者に支えられています：

- [folke/lazy.nvim](https://github.com/folke/lazy.nvim)
- [williamboman/mason.nvim](https://github.com/williamboman/mason.nvim)
- [nvim-telescope/telescope.nvim](https://github.com/nvim-telescope/telescope.nvim)
- [nvim-treesitter/nvim-treesitter](https://github.com/nvim-treesitter/nvim-treesitter)
- その他多くの素晴らしいプラグイン作者の方々

---

Happy coding with Neovim! 🎉
