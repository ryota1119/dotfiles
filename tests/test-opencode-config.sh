#!/bin/bash

set -euo pipefail

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test_root=$(mktemp -d "${TMPDIR:-/tmp}/test-opencode-config.XXXXXX")
trap 'rm -rf "$test_root"' EXIT

export HOME="$test_root/home"
export XDG_CONFIG_HOME="$test_root/xdg-config"
export OPENCODE_DISABLE_PROJECT_CONFIG=1
export CLIENT_ID="test-client-id"
export CLIENT_SECRET="test-client-secret"
export SOCIALDATA_API_KEY="test-socialdata-api-key"
mkdir -p "$HOME" "$XDG_CONFIG_HOME"
cp -R "$repo_root/dot_config/opencode" "$XDG_CONFIG_HOME/opencode"

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
if (actualNames.length !== 9) throw new Error(`Expected 9 MCPs, got ${actualNames.length}`)
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
