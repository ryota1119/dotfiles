return {
  settings = {
    yaml = {
      schemas = {
        kubernetes = "*.k8s.yaml",
        ['http://json.schemastore.org/github-workflow'] = '.github/workflows/*',
        ['http://json.schemastore.org/github-action'] = '.github/action.{yml,yaml}',
        ['http://json.schemastore.org/ansible-stable-2.9'] = 'roles/tasks/*.{yml,yaml}',
        ['http://json.schemastore.org/ansible-playbook'] = 'playbook.{yml,yaml}',
      },
    }
  }
}