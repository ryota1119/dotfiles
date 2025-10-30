-- ファイルタイプ検出設定
-- .tfファイルをterraform filetypeにマッピング

vim.filetype.add({
  extension = {
    tf = "terraform",
    tfvars = "terraform",
    tfstate = "terraform",
  },
  pattern = {
    [".*%.tf%.backup"] = "terraform",
  },
})

