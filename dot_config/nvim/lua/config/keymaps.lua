-- キーマップ設定

local keymap = vim.keymap.set
local opts = { noremap = true, silent = true }

-- リーダーキーは lazy.lua で設定済み（スペース）

-- ノーマルモード
-- より快適な上下移動（表示行単位で移動）
keymap("n", "j", "gj", opts)
keymap("n", "k", "gk", opts)

-- ウィンドウ間の移動
keymap("n", "<C-h>", "<C-w>h", opts)
keymap("n", "<C-j>", "<C-w>j", opts)
keymap("n", "<C-k>", "<C-w>k", opts)
keymap("n", "<C-l>", "<C-w>l", opts)

-- ウィンドウのリサイズ
keymap("n", "<C-Up>", ":resize +2<CR>", opts)
keymap("n", "<C-Down>", ":resize -2<CR>", opts)
keymap("n", "<C-Left>", ":vertical resize -2<CR>", opts)
keymap("n", "<C-Right>", ":vertical resize +2<CR>", opts)

-- バッファ移動
keymap("n", "<S-l>", ":bnext<CR>", opts)
keymap("n", "<S-h>", ":bprevious<CR>", opts)

-- インデント調整
keymap("v", "<", "<gv", opts)
keymap("v", ">", ">gv", opts)

-- 選択したテキストの移動
keymap("v", "J", ":m '>+1<CR>gv=gv", opts)
keymap("v", "K", ":m '<-2<CR>gv=gv", opts)

-- ビジュアルモードでペースト時にヤンクしない
keymap("v", "p", '"_dP', opts)

-- 検索結果のハイライトを消す
-- （<leader>h は gitsigns の hunk グループと競合するので <leader>nh へ移動）
keymap("n", "<leader>nh", ":nohlsearch<CR>", { noremap = true, silent = true, desc = "No Highlight" })

-- 保存と終了
keymap("n", "<leader>w", ":w<CR>", opts)
keymap("n", "<leader>q", ":q<CR>", opts)

-- 分割
keymap("n", "<leader>sv", ":vsplit<CR>", opts)
keymap("n", "<leader>sh", ":split<CR>", opts)

-- バッファを閉じる
keymap("n", "<leader>bd", ":bdelete<CR>", opts)

-- location list / quickfix の開閉状態を判定するヘルパー
local function is_loclist_open()
  for _, win in ipairs(vim.fn.getwininfo()) do
    if win.loclist == 1 then
      return true
    end
  end
  return false
end

local function is_qflist_open()
  for _, win in ipairs(vim.fn.getwininfo()) do
    if win.quickfix == 1 and win.loclist == 0 then
      return true
    end
  end
  return false
end

-- 診断（LSP Diagnostics）
-- <leader>e は neo-tree の <leader>ee / <leader>ef と競合して遅延が出るため
-- <leader>ce（Code Error）に移動
keymap("n", "<leader>ce", vim.diagnostic.open_float, { desc = "診断をフロートで表示" })
keymap("n", "[d", function()
  vim.diagnostic.jump({ count = -1, float = true })
end, { desc = "前の診断へ" })
keymap("n", "]d", function()
  vim.diagnostic.jump({ count = 1, float = true })
end, { desc = "次の診断へ" })

-- <leader>cd / cD は開いていれば閉じ、閉じていれば診断を入れ直して開く（トグル）
keymap("n", "<leader>cd", function()
  if is_loclist_open() then
    vim.cmd("lclose")
  else
    vim.diagnostic.setloclist()
  end
end, { desc = "診断一覧（location list）トグル" })

keymap("n", "<leader>cD", function()
  if is_qflist_open() then
    vim.cmd("cclose")
  else
    vim.diagnostic.setqflist()
  end
end, { desc = "診断一覧（quickfix）トグル" })

-- 汎用の location list / quickfix トグル（診断に限らない）
keymap("n", "<leader>xl", function()
  if is_loclist_open() then
    vim.cmd("lclose")
  else
    -- 中身が無いと E776 になるので pcall で保護
    local ok = pcall(vim.cmd, "lopen")
    if not ok then
      vim.notify("location list is empty", vim.log.levels.INFO)
    end
  end
end, { desc = "Location list トグル" })

keymap("n", "<leader>xq", function()
  if is_qflist_open() then
    vim.cmd("cclose")
  else
    vim.cmd("copen")
  end
end, { desc = "Quickfix トグル" })
