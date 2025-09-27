# AIP CLI — Complete Reference & Runbook (GL AIP SDK)

> Comprehensive guide for installing, configuring, and using the **`aip`** CLI to manage agents, tools, and MCPs. Based on the official GL AIP SDK documentation.

## Quick Command Reference

| Category   | Command                    | Description           |
| ---------- | -------------------------- | --------------------- |
| **Setup**  | `aip status`               | Verify connection     |
|            | `aip --version`            | Show version          |
| **Agents** | `aip agents list`          | List all agents       |
|            | `aip agents create`        | Create new agent      |
|            | `aip agents run`           | Execute agent         |
|            | `aip agents get`           | Get agent details     |
|            | `aip agents update`        | Update agent          |
|            | `aip agents delete`        | Delete agent          |
| **Tools**  | `aip tools list`           | List all tools        |
|            | `aip tools create`         | Create/upload tool    |
|            | `aip tools get`            | Get tool details      |
|            | `aip tools update`         | Update tool           |
|            | `aip tools delete`         | Delete tool           |
| **MCPs**   | `aip mcps list`            | List MCP connections  |
|            | `aip mcps create`          | Create MCP connection |
|            | `aip mcps test-connection` | Test MCP connection   |
|            | `aip mcps get`             | Get MCP details       |
|            | `aip mcps update`          | Update MCP            |
|            | `aip mcps delete`          | Delete MCP            |
| **Config** | `aip config list`          | Show configuration    |
|            | `aip config set`           | Set config value      |

## 1) Prerequisites & Installation

- Python 3.10+
- gcloud CLI (for GDP Labs authentication)
- Install via **pipx** (recommended) or pip

```bash
# Prerequisites: Install gcloud CLI first
# Follow: https://cloud.google.com/sdk/docs/install

# Authenticate to GDP Labs (required for private packages)
gcloud auth login
gcloud auth application-default login

# Install GL AIP SDK CLI (recommended method)
pipx install glaip-sdk
# Note: Package name is 'glaip-sdk' for GL AI Agents Platform

# Alternative: Install via pip
pip install glaip-sdk

# Verify installation
aip --version
# Expected output: "AIP CLI version X.X.X"

# Enable debug mode for troubleshooting
aip --debug status
```

**Important Notes:**

- The package name is `glaip-sdk` for the GL AI Agents Platform CLI
- GDP Labs authentication via gcloud is required for accessing private GLLM packages
- If `aip` command isn't found after pipx install, run `pipx ensurepath` then restart your terminal

## 2) Configuration

### Environment Variables Setup

```bash
# macOS/Linux
export AIP_API_URL="https://your-aip-instance.com"
export AIP_API_KEY="your-api-key-here"

# Windows (PowerShell)
$env:AIP_API_URL="https://your-aip-instance.com"
$env:AIP_API_KEY="your-api-key-here"

# Windows (Command Prompt)
set AIP_API_URL=https://your-aip-instance.com
set AIP_API_KEY=your-api-key-here
```

### Interactive Configuration

```bash
# View current configuration
aip config list

# Set specific config value
aip config set api_url "https://new-aip-instance.com"
aip config set api_key "new-api-key"
```

**Config Precedence:** CLI config > environment variables > .env file > defaults
**Config Location:**

- Linux/macOS: `~/.aip/config.yaml`
- Windows: `%USERPROFILE%\.aip\config.yaml`

## 3) Connection Verification

```bash
# Check connection status
aip status
# Expected: "✅ Connected to AIP API"

# Debug connection issues
aip --debug status

# Show current configuration
aip config list
```

**Troubleshooting:**

- 401 Error: Invalid API key
- 404 Error: Incorrect API URL
- Connection refused: Check network/firewall settings

## 4) Agent Management Commands

### List Agents

```bash
# List all agents (default rich view)
aip agents list

# Different output formats
aip agents list --view json  # For scripting
aip agents list --view plain # Simple text
aip agents list --view md    # Markdown table
```

### Create Agent

```bash
# Basic agent creation
aip agents create \
  --name "compliance-agent" \
  --instruction "You help with GitHub issue compliance."

# Advanced agent with tools and timeout
aip agents create \
  --name "advanced-agent" \
  --instruction "Complex task handler" \
  --tools "tool-id-1,tool-id-2" \
  --agents "sub-agent-1,sub-agent-2" \
  --timeout 300
```

### Get Agent Details

```bash
# Get agent by ID or name
aip agents get <AGENT_ID>
aip agents get "agent-name"

# Select from multiple matches
aip agents get "agent" --select 2

# Output as JSON
aip agents get <AGENT_ID> --view json
```

### Run Agent

```bash
# Simple text input
aip agents run <AGENT_ID> \
  --input "Analyze this project"

# With file attachment
aip agents run <AGENT_ID> \
  --input "Process this data" \
  --file data.csv

# With chat history and custom timeout
aip agents run <AGENT_ID> \
  --input "Continue our discussion" \
  --chat-history "Previous conversation context" \
  --timeout 720 \
  --save output.md

# JSON input for complex parameters
aip agents run <AGENT_ID> \
  --input '{"task":"analyze","params":{"depth":3}}' \
  --view json
```

### Update Agent

```bash
# Update instruction
aip agents update <AGENT_ID> \
  --instruction "Updated instructions"

# Update multiple properties
aip agents update <AGENT_ID> \
  --name "new-name" \
  --instruction "New instructions" \
  --tools "tool-1,tool-2" \
  --timeout 180
```

### Delete Agent

```bash
# Delete with confirmation prompt
aip agents delete <AGENT_ID>

# Skip confirmation
aip agents delete <AGENT_ID> -y
aip agents delete <AGENT_ID> --yes
```

## 5) Tool Management (Python Functions)

### List Tools

```bash
# List all available tools
aip tools list

# Output formats
aip tools list --view json
aip tools list --view plain
aip tools list --view md
```

### Create/Upload Tool

```bash
# Upload Python tool file
aip tools create --file my_tool.py

# With metadata
aip tools create \
  --file compliance_toolkit.py \
  --name "compliance-toolkit" \
  --description "GitHub compliance checking tools" \
  --tags "github,compliance,validation"

# From directory (multiple tools)
aip tools create --file ./tools/
```

### Get Tool Details

```bash
# Get tool information
aip tools get <TOOL_ID>

# Get by name with selection
aip tools get "toolkit" --select 1

# JSON output for parsing
aip tools get <TOOL_ID> --view json
```

### Update Tool

```bash
# Update description
aip tools update <TOOL_ID> \
  --description "Enhanced compliance toolkit"

# Update multiple properties
aip tools update <TOOL_ID> \
  --name "new-toolkit-name" \
  --description "Updated description" \
  --tags "new,tags,here"

# Replace tool code
aip tools update <TOOL_ID> \
  --file updated_tool.py
```

### Delete Tool

```bash
# Delete with confirmation
aip tools delete <TOOL_ID>

# Skip confirmation
aip tools delete <TOOL_ID> -y
```

## 6) MCP Management (Model Context Protocol)

### List MCPs

```bash
# List all MCP connections
aip mcps list

# Different output formats
aip mcps list --view json
aip mcps list --view plain
aip mcps list --view md
```

### Create MCP Connection (BOSA Only)

```bash
# We use BOSA MCP exclusively for GitHub integration
# No need to configure direct GitHub API connections

# Create BOSA GitHub MCP connection
aip mcps create \
  --name "bosa-github-mcp" \
  --transport "http" \
  --config '{
    "url": "https://api.bosa.id/github/mcp",
    "headers": {
      "X-Api-Key": "${BOSA_API_KEY_CLIENT}",
      "Authorization": "Bearer ${BOSA_USER_SECRET}"
    },
    "functions": [
      "github_list_project_items",
      "github_get_issue_handler",
      "github_list_issues_comments"
    ]
  }'

# Alternative: From configuration file
cat > bosa-mcp-config.json << EOF
{
  "url": "https://api.bosa.id/github/mcp",
  "headers": {
    "X-Api-Key": "${BOSA_API_KEY_CLIENT}",
    "Authorization": "Bearer ${BOSA_USER_SECRET}"
  },
  "organization": "${GITHUB_ORGANIZATION}",
  "project_number": ${GITHUB_PROJECT_ID},
  "rate_limit": {
    "requests_per_minute": 60,
    "retry_max": 3,
    "backoff_base": 2
  }
}
EOF

aip mcps create \
  --name "bosa-github-mcp" \
  --transport "http" \
  --config "$(cat bosa-mcp-config.json)"
```

### Integrating BOSA MCP Servers

BOSA provides MCP connectors for GitHub and other services. For local testing and AIP integration:

#### Local Testing with BOSA MCP

```bash
# Step 1: Install MCP Inspector for local testing
npm install -g @modelcontextprotocol/inspector

# Step 2: Run MCP Inspector to explore BOSA GitHub connector
DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector

# Step 3: Test BOSA GitHub MCP locally with Python
```

```python
from gllm_tools.mcp.client.client import MCPClient
import os
from dotenv import load_dotenv

load_dotenv()  # Load credentials from .env

# Configure BOSA GitHub MCP
servers = {
    "github": {
        "transport": "streamable_http",
        "url": "https://api.bosa.id/github/mcp",
        "headers": {
            "X-Api-Key": os.environ["BOSA_API_KEY_CLIENT"],
            "Authorization": f"Bearer {os.environ['BOSA_USER_SECRET']}"
        }
    }
}

# Initialize MCP client
client = MCPClient(servers)

# Test GitHub functions
response = client.call_function(
    "github",
    "github_list_project_items",
    {
        "organization": "GDP-ADMIN",
        "project_number": 223,
        "statuses": ["In Progress", "In Review", "Todo"]
    }
)
```

#### Registering BOSA MCP in AIP

```bash
# Step 1: Create BOSA GitHub MCP connection
aip mcps create \
  --name "bosa-github-mcp" \
  --transport "http" \
  --config '{
    "url": "https://api.bosa.id/github/mcp",
    "headers": {
      "X-Api-Key": "${BOSA_API_KEY_CLIENT}",
      "Authorization": "Bearer ${BOSA_USER_SECRET}"
    },
    "functions": [
      "github_list_project_items",
      "github_get_issue_handler",
      "github_list_issues_comments"
    ]
  }'

# Step 2: Link BOSA MCP to your agent
aip agents update <AGENT_ID> \
  --mcps "bosa-github-mcp" \
  --mcp-permissions "read-only"
```

### Test MCP Connection

```bash
# Test existing MCP
aip mcps test-connection <MCP_ID>

# Test from config file before creating
aip mcps test-connection --from-file "github-mcp-config.json"

# Test with custom timeout
aip mcps test-connection <MCP_ID> --timeout 30
```

### Get MCP Details

```bash
# Get MCP information
aip mcps get <MCP_ID>

# Get by name
aip mcps get "github-mcp"

# JSON output
aip mcps get <MCP_ID> --view json
```

### Update MCP

```bash
# Update configuration
aip mcps update <MCP_ID> \
  --config '{"url":"https://new-mcp.example.com"}'

# Update from file
aip mcps update <MCP_ID> \
  --config "$(cat updated-config.json)"

# Update name and transport
aip mcps update <MCP_ID> \
  --name "updated-mcp" \
  --transport "websocket"
```

### Delete MCP

```bash
# Delete with confirmation
aip mcps delete <MCP_ID>

# Skip confirmation
aip mcps delete <MCP_ID> -y
```

## 7) Practical Examples

### GitHub Compliance Agent (Read-Only)

```bash
# Basic compliance check
aip agents run <AGENT_ID> \
  --input '{
    "project_identifier": "ORG/PROJECT_NUMBER",
    "statuses": ["In Progress","In Review","Todo"],
    "timezone": "Asia/Jakarta",
    "bot_ignores": ["dependabot","github-actions"],
    "output_format": ["md","csv","json"],
    "dry_run": true
  }' \
  --view json \
  --save compliance_report.json

# With file attachment for batch processing
aip agents run <AGENT_ID> \
  --input "Process these projects" \
  --file project_list.csv \
  --timeout 720 \
  --save batch_results.md
```

### Multi-Agent Workflow

```bash
# Create parent agent with sub-agents
aip agents create \
  --name "orchestrator" \
  --instruction "Coordinate compliance checks" \
  --agents "analyzer-agent,reporter-agent" \
  --timeout 900

# Run with complex input
aip agents run orchestrator \
  --input '{"mode":"full","targets":["project1","project2"]}' \
  --view rich
```

### Tool Integration Example

```bash
# Upload compliance toolkit
aip tools create \
  --file compliance_toolkit.py \
  --name "compliance-tools" \
  --description "GitHub issue validation tools"

# Create agent using the tool
aip agents create \
  --name "validator-agent" \
  --instruction "Validate GitHub issues using compliance tools" \
  --tools "compliance-tools"

# Run validation
aip agents run validator-agent \
  --input "Validate all open issues" \
  --save validation_report.md
```

## 8) Output Formats & Scripting

### View Options

All read operations support multiple output formats:

| Format  | Use Case        | Description                                  |
| ------- | --------------- | -------------------------------------------- |
| `rich`  | Interactive CLI | Colored, formatted terminal output (default) |
| `plain` | Simple scripts  | Plain text, no formatting                    |
| `json`  | Automation      | Structured data for parsing                  |
| `md`    | Documentation   | Markdown formatted tables/lists              |

### Scripting Examples

```bash
# Get agent ID for automation
AGENT_ID=$(aip agents list --view json | jq -r '.agents[0].id')

# Run agent and extract results
RESULT=$(aip agents run $AGENT_ID \
  --input "Test" \
  --view json | jq -r '.output')

# Batch process multiple agents
for agent in $(aip agents list --view json | jq -r '.agents[].id'); do
  echo "Processing agent: $agent"
  aip agents run $agent --input "Health check" --view plain
done

# Save formatted report
aip agents run <AGENT_ID> \
  --input "Generate report" \
  --view md \
  --save report_$(date +%Y%m%d).md
```

## 9) Troubleshooting & Debugging

### Debug Mode

```bash
# Enable debug for any command
aip --debug agents list
aip --debug agents run <AGENT_ID> --input "test"
aip --debug mcps test-connection <MCP_ID>
```

### Common Issues & Solutions

| Error              | Cause            | Solution                                        |
| ------------------ | ---------------- | ----------------------------------------------- |
| 401 Unauthorized   | Invalid API key  | Check `AIP_API_KEY` with `aip config list`      |
| 404 Not Found      | Wrong API URL    | Verify `AIP_API_URL` points to correct instance |
| Connection refused | Network/firewall | Check network settings, proxy configuration     |
| Timeout            | Slow operation   | Increase `--timeout` value                      |
| Invalid JSON       | Malformed input  | Validate JSON with `jq` or online validator     |

### Diagnostic Commands

```bash
# Check configuration
aip config list

# Test connection
aip status

# Verbose output
aip --debug status

# Check CLI version
aip --version

# Verify environment
echo $AIP_API_URL
echo $AIP_API_KEY

# Test with minimal agent
aip agents create --name "test" --instruction "Test agent"
aip agents run test --input "Hello"
aip agents delete test -y
```

## 10) Cleanup & Maintenance

### Regular Cleanup

```bash
# List all resources
aip agents list
aip tools list
aip mcps list

# Delete test agents
aip agents delete test-agent-1 -y
aip agents delete test-agent-2 -y

# Batch delete (with confirmation)
for agent in $(aip agents list --view json | jq -r '.agents[] | select(.name | startswith("test-")) | .id'); do
  echo "Deleting: $agent"
  aip agents delete $agent
done

# Clean up unused tools
aip tools delete <TOOL_ID> -y

# Remove broken MCP connections
aip mcps delete <MCP_ID> -y
```

### Best Practices

1. **Naming Convention**: Use prefixes for test resources (e.g., `test-`, `dev-`, `prod-`)
2. **Regular Audits**: Schedule weekly cleanup of test resources
3. **Save Configurations**: Export important agent configs before deletion
4. **Version Control**: Store agent instructions and tool code in git
5. **Documentation**: Keep README with agent purposes and dependencies

```bash
# Export agent configuration
aip agents get <AGENT_ID> --view json > agent_backup.json

# Export all agents
for agent in $(aip agents list --view json | jq -r '.agents[].id'); do
  aip agents get $agent --view json > "backup_${agent}.json"
done
```

## Additional Resources

- Official Documentation: [GL AIP SDK Docs](https://gdplabs.gitbook.io/ai-agents-platform/)
- CLI Reference: [CLI Commands](https://gdplabs.gitbook.io/ai-agents-platform/gl-aip-sdk/reference/cli-commands)
- Support: Contact your AIP administrator or check the platform status page
