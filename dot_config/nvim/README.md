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
- **Nerd Font**（アイコン表示用、推奨）

### Nerd Font のインストール

アイコンを正しく表示するには、Nerd Font のインストールが推奨されます。

#### おすすめの Nerd Font

| フォント名 | 特徴 | Homebrew コマンド |
|----------|------|------------------|
| **JetBrains Mono Nerd Font** ⭐ | モダンで視認性が高い。JetBrains 製IDEで使用されている。最も人気が高い。 | `brew install --cask font-jetbrains-mono-nerd-font` |
| **Fira Code Nerd Font** | リガチャ（合字）機能が充実。読みやすい。 | `brew install --cask font-fira-code-nerd-font` |
| **Hack Nerd Font** | シンプルで読みやすい。プログラミング専用に設計。 | `brew install --cask font-hack-nerd-font` |
| **MesloLGS Nerd Font** | Powerlevel10k で使用される。ターミナル向けに最適化。 | `brew install --cask font-meslo-lg-nerd-font` |
| **Caskaydia Cove Nerd Font** | Cascadia Code の派生。Windows Terminal で使用。 | `brew install --cask font-caskaydia-cove-nerd-font` |
| **Iosevka Nerd Font** | スペース効率が良い。コンパクトで情報量が多い。 | `brew install --cask font-iosevka-nerd-font` |

**推奨**: 
- **初心者**: JetBrains Mono または Fira Code（視認性が高い）
- **省スペース重視**: Iosevka（小さい画面でも見やすい）
- **ターミナル特化**: MesloLGS（Powerlevel10k ユーザーに人気）

#### macOS でのインストール

1. Homebrew を使用する場合：

```bash
brew tap homebrew/cask-fonts
# お好みのフォントをインストール（例：JetBrains Mono）
brew install --cask font-jetbrains-mono-nerd-font
```

2. 手動インストールの場合：

[Nerd Fonts の公式サイト](https://www.nerdfonts.com/font-downloads)からフォントをダウンロードしてインストール

#### ターミナルでのフォント設定

**iTerm2** の場合：
1. Preferences → Profiles → Text → Font
2. Nerd Font を選択（例: `JetBrainsMono Nerd Font`）

**macOS 標準ターミナル** の場合：
1. Preferences → Profiles → Text → Font
2. Nerd Font を選択

**Alacritty** の場合：
`~/.config/alacritty/alacritty.toml` に以下を追加：

```toml
[font]
normal = { family = "JetBrainsMono Nerd Font", style = "Regular" }
# または
# normal = { family = "FiraCode Nerd Font", style = "Regular" }
```

**Kitty** の場合：
`~/.config/kitty/kitty.conf` に以下を追加：

```conf
font_family JetBrainsMono Nerd Font
# または
# font_family FiraCode Nerd Font
```

> **注意**: Nerd Font をインストールしない場合でも、フォールバック設定により基本的な文字アイコンが表示されます（例: `L` for Lua, `M` for Markdown など）。

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

### アイコンが `?` と表示される

1. **Nerd Font がインストールされているか確認**
   - システムフォント一覧に Nerd Font が表示されているか確認
2. **ターミナルのフォント設定を確認**
   - ターミナルの設定で Nerd Font が選択されているか確認
3. **ターミナルを再起動**
   - フォントを変更した後は、ターミナルを再起動してください
4. **フォールバック設定**
   - Nerd Font が利用できない場合、基本的な文字アイコン（`L`、`M`、`J` など）が表示されます

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
