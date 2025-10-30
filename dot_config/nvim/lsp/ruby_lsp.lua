return {
  settings = {
    rubyLsp = {
      formatter = "rubocop",
      linters = { "rubocop" },
      addonSettings = {
        ["Ruby LSP Rails"] = {
          enablePendingMigrationsPrompt = false,
        },
      },
    }
  }
}