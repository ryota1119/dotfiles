#!/bin/bash

set -euo pipefail

if ! command -v opencode >/dev/null 2>&1; then
  printf '%s\n' "skip: opencode が見つからないため OpenCode config テストを実行しなかった（MCP定義とagent定義は未検証）"
  exit 0
fi

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test_root=$(mktemp -d "${TMPDIR:-/tmp}/test-opencode-config.XXXXXX")
trap 'rm -rf "$test_root"' EXIT

stub_bin="$test_root/stub-bin"
mkdir -p "$stub_bin"
cat >"$stub_bin/op" <<'EOF'
#!/bin/sh
# stub for the `op` binary that chezmoi's onepasswordRead calls
case "$1" in
  account)
    printf '[{"url":"my.1password.com","email":"test@example.com","user_uuid":"TESTUSER","account_uuid":"TESTACCOUNT"}]\n'
    exit 0 ;;
  signin) printf 'stub-session-token\n'; exit 0 ;;
esac
ref=""
for a in "$@"; do
  case "$a" in op://*) ref="$a" ;; esac
done
case "$ref" in
  *"X Developer Client Secret/username") printf 'test-client-id' ;;
  *"X Developer Client Secret/password") printf 'test-client-secret' ;;
  *"SocialData/api_key") printf 'test-socialdata-api-key' ;;
  *) printf 'unexpected op ref: %s\n' "$ref" >&2; exit 1 ;;
esac
EOF
chmod +x "$stub_bin/op"

CLIENT_ID=$("$stub_bin/op" read 'op://Personal/X Developer Client Secret/username')
CLIENT_SECRET=$("$stub_bin/op" read 'op://Personal/X Developer Client Secret/password')
SOCIALDATA_API_KEY=$("$stub_bin/op" read 'op://Personal/SocialData/api_key')

mkdir -p "$test_root/xdg-config/opencode"
PATH="$stub_bin:$PATH" chezmoi execute-template --source "$repo_root" \
  <"$repo_root/dot_config/opencode/private_opencode.jsonc.tmpl" \
  >"$test_root/xdg-config/opencode/opencode.jsonc"

export HOME="$test_root/home"
export XDG_CONFIG_HOME="$test_root/xdg-config"
export OPENCODE_DISABLE_PROJECT_CONFIG=1
mkdir -p "$HOME" "$XDG_CONFIG_HOME"
cp -R "$repo_root/dot_config/opencode/agent" "$XDG_CONFIG_HOME/opencode/agent"

config_output="$test_root/config.json"
opencode debug config >"$config_output"

node - "$config_output" "$HOME" "$CLIENT_ID" "$CLIENT_SECRET" "$SOCIALDATA_API_KEY" <<'NODE'
const fs = require("fs")
const config = JSON.parse(fs.readFileSync(process.argv[2], "utf8"))
const home = process.argv[3]
const clientId = process.argv[4]
const clientSecret = process.argv[5]
const socialdataApiKey = process.argv[6]

const expected = {
  "google-calendar": {
    type: "remote",
    url: "https://calendarmcp.googleapis.com/mcp/v1",
    enabled: true,
  },
  gmail: {
    type: "remote",
    url: "https://gmailmcp.googleapis.com/mcp/v1",
    enabled: true,
  },
  "google-drive": {
    type: "remote",
    url: "https://drivemcp.googleapis.com/mcp/v1",
    enabled: true,
  },
  playwright: {
    type: "local",
    command: ["npx", "@playwright/mcp@latest"],
    enabled: true,
  },
  openrouter: {
    type: "remote",
    url: "https://mcp.openrouter.ai/mcp",
    enabled: true,
  },
  xapi: {
    type: "local",
    command: ["npx", "-y", "@xdevplatform/xurl", "mcp", "https://api.x.com/mcp"],
    enabled: true,
    environment: {
      CLIENT_ID: clientId,
      CLIENT_SECRET: clientSecret,
    },
  },
  "hn-mcp": {
    type: "local",
    command: ["uv", "run", "--directory", `${home}/Workspace/repos/github.com/RayLabOrg/hn-mcp`, "hn-mcp"],
    enabled: true,
  },
  "qiita-mcp": {
    type: "local",
    command: ["uv", "run", "--directory", `${home}/Workspace/repos/github.com/RayLabOrg/qiita-mcp`, "qiita-mcp"],
    enabled: true,
  },
  "zenn-mcp": {
    type: "local",
    command: ["uv", "run", "--directory", `${home}/Workspace/repos/github.com/RayLabOrg/zenn-mcp`, "zenn-mcp"],
    enabled: true,
  },
  "socialdata-mcp": {
    type: "local",
    command: ["uv", "run", "--directory", `${home}/Workspace/repos/github.com/RayLabOrg/socialdata-mcp`, "socialdata-mcp"],
    enabled: true,
    environment: {
      SOCIALDATA_API_KEY: socialdataApiKey,
    },
  },
}

const actualNames = Object.keys(config.mcp ?? {}).sort()
const expectedNames = Object.keys(expected).sort()
if (Object.hasOwn(config.mcp ?? {}, "notion")) throw new Error("Notion MCP must not exist")
if (actualNames.length !== 10) throw new Error(`Expected 10 MCPs, got ${actualNames.length}`)
if (JSON.stringify(actualNames) !== JSON.stringify(expectedNames)) {
  throw new Error(`Unexpected MCP set: ${JSON.stringify(actualNames)}`)
}

for (const [name, expectedMcp] of Object.entries(expected)) {
  const mcp = config.mcp?.[name]
  if (!mcp) throw new Error(`Missing MCP: ${name}`)
  if (JSON.stringify(mcp) !== JSON.stringify(expectedMcp)) {
    throw new Error(`Unexpected MCP ${name}: ${JSON.stringify(mcp)}`)
  }
}
NODE

check_agent() {
  local name=$1
  local expected_provider=$2
  local expected_model=$3
  local output="$test_root/agent-$name.json"

  opencode debug agent "$name" >"$output"
  node - "$output" "$name" "$expected_provider" "$expected_model" <<'NODE'
const fs = require("fs")
const agent = JSON.parse(fs.readFileSync(process.argv[2], "utf8"))
const name = process.argv[3]
const expectedProvider = process.argv[4]
const expectedModel = process.argv[5]

if (agent.name !== name) throw new Error(`Unexpected agent name: ${agent.name}`)
if (agent.model?.providerID !== expectedProvider) {
  throw new Error(`Unexpected ${name} model provider: ${agent.model?.providerID}`)
}
if (agent.model?.modelID !== expectedModel) {
  throw new Error(`Unexpected ${name} model ID: ${agent.model?.modelID}`)
}
if (agent.mode !== "subagent") throw new Error(`Unexpected ${name} mode: ${agent.mode}`)

const editDenied = agent.permission?.some(
  (rule) => rule.permission === "edit" && rule.pattern === "*" && rule.action === "deny",
)
if (!editDenied) throw new Error(`${name} does not deny edit permission`)
NODE
}

check_agent repo-explorer openai gpt-5.6-luna
check_agent source-reader openai gpt-5.6-terra
check_agent status-collector openai gpt-5.6-luna

printf '%s\n' "OpenCode config tests passed"
