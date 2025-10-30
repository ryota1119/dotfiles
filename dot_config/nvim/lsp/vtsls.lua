return {
  settings = {
    vtsls = {
      enableMoveToFileCodeAction = true,
      autoUseWorkspaceTsdk = true,
      experimental = {
        completion = {
          enableServerSideFuzzyMatch = true,
        },
      },
    },
    typescript = {
      preferences = {
        includePackageJsonAutoImports = 'auto',
        allowIncompleteCompletions = true,
        allowRenameShorthandProperties = true,
        allowTextChangesInNewFiles = true,
        disableLineTextInReferences = true,
        generateReturnInDocTemplate = true,
        includeCompletionsForImportStatements = true,
        includeCompletionsForModuleExports = true,
        includeCompletionsWithClassMemberSnippets = true,
        includeCompletionsWithObjectLiteralMethodSnippets = true,
        includeCompletionsWithSnippetText = true,
        jsxAttributeCompletionStyle = 'auto',
        providePrefixAndSuffixTextForRename = true,
        provideRefactorNotApplicableReason = true,
        quotePreference = 'auto',
        useAliasesForRenames = false,
        useLabelDetailsInCompletionEntries = true,
      },
      suggest = {
        autoImports = true,
        completeFunctionCalls = true,
        includeCompletionsForImportStatements = true,
        includeCompletionsWithClassMemberSnippets = true,
        includeCompletionsWithObjectLiteralMethodSnippets = true,
        includeCompletionsWithSnippetText = true,
        jsxAttributeCompletionStyle = 'auto',
        useLabelDetailsInCompletionEntries = true,
      },
      updateImportsOnFileMove = {
        enabled = 'always',
      },
      inlayHints = {
        enumMemberValues = {
          enabled = false,
        },
        functionLikeReturnTypes = {
          enabled = true,
        },
        parameterNames = {
          enabled = 'all',
        },
        parameterTypes = {
          enabled = true,
        },
        propertyDeclarationTypes = {
          enabled = true,
        },
        variableTypes = {
          enabled = false,
        },
      },
    },
  },
}