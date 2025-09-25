# GitHub Compliance Agent CLI Tools

This directory contains CLI tools for creating and managing the GitHub Issue Compliance Agent with BOSA MCP integration.

## Files Overview

- **`create_agent.py`** - Main script to create and configure the compliance agent
- **`orchestrator.py`** - Test harness for local workflow testing (uses fixtures)

## Prerequisites

1. **Install AIP CLI**:

   ```bash
   pipx install glaip-sdk
   ```

2. **Authenticate with GDP Labs**:

   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Set up environment variables**:
   ```bash
   cp ../.env.template .env
   # Edit .env with your actual credentials
   ```

## Quick Start

### 1. Create Agent with Default Configuration

```bash
python create_agent.py
```

### 2. Create Agent with Custom Configuration

```bash
python create_agent.py --config ../configs/agent_creation_config.json
```

### 3. Dry Run (See What Would Happen)

```bash
python create_agent.py --dry-run --debug
```

## Environment Variables Required

| Variable              | Description                     | Example                   |
| --------------------- | ------------------------------- | ------------------------- |
| `BOSA_API_KEY_CLIENT` | BOSA API key for authentication | `your-bosa-api-key`       |
| `BOSA_USER_SECRET`    | BOSA user secret token          | `your-bosa-user-secret`   |
| `AIP_API_URL`         | Your AIP platform instance URL  | `https://aip.example.com` |
| `AIP_API_KEY`         | Your AIP platform API key       | `your-aip-api-key`        |

## Usage Examples

### Create Agent (Standard)

```bash
python create_agent.py
```

**Output**:

- Creates BOSA GitHub MCP connection
- Creates GitHub compliance agent
- Links agent to MCP
- Validates configuration

### Test Run (Debug Mode)

```bash
python create_agent.py --debug --dry-run
```

**Output**:

- Shows all commands that would be executed
- Validates configuration without making changes
- Displays detailed logging

### Custom Configuration

```bash
python create_agent.py --config custom_config.json
```

**Example custom_config.json**:

```json
{
  "agent": {
    "name": "my-compliance-agent",
    "timeout": 900,
    "tools": ["github_compliance_evaluator_tool"]
  },
  "mcp": {
    "name": "my-github-mcp",
    "organization": "MY-ORG",
    "project_number": 456
  }
}
```

## Agent Capabilities

The created agent will have these capabilities:

### 🔍 **Compliance Checking**

- Evaluates 7 compliance rules on GitHub Project issues
- Processes up to 15 issues (5 per status: Todo, In Progress, In Review)
- Uses Asia/Jakarta timezone for date calculations
- Filters out bot comments appropriately

### 📊 **Reporting**

- Generates JSON reports with violation details
- Provides actionable recommendations
- Includes compliance rate calculations
- Exports to multiple formats

### 🛡️ **Read-Only Mode**

- Never modifies GitHub issues or comments
- Safe to run on production projects
- Respects rate limits with exponential backoff

## Compliance Rules

| Rule   | Description                               |
| ------ | ----------------------------------------- |
| **R1** | Issues must have assignees                |
| **R2** | Issues must have incoming date            |
| **R3** | Issues must have due date                 |
| **R4** | Issues must have valid status             |
| **R5** | Missing approval for issues >7 days old   |
| **R6** | Warning for issues due in next 7 days     |
| **R7** | Issues need human comments in last 7 days |

## Testing the Agent

After creation, test your agent:

```bash
# Basic test
aip agents run github-compliance-agent-v1 \
  --input "Check compliance for GDP-ADMIN/223"

# View agent details
aip agents get github-compliance-agent-v1

# Test MCP connection
aip mcps test-connection bosa-github-mcp
```

## Troubleshooting

### Common Issues

1. **AIP CLI not found**:

   ```bash
   pipx install glaip-sdk
   pipx ensurepath  # Restart terminal after this
   ```

2. **Authentication failed**:

   ```bash
   aip config list  # Check current config
   aip status       # Check connection
   ```

3. **BOSA credentials invalid**:

   - Verify credentials at https://api.bosa.id
   - Check environment variables: `echo $BOSA_API_KEY_CLIENT`

4. **MCP connection test fails**:
   ```bash
   aip mcps test-connection bosa-github-mcp --debug
   ```

### Debug Mode

Run with `--debug` flag to see detailed logging:

```bash
python create_agent.py --debug
```

This will show:

- All AIP CLI commands being executed
- MCP configuration details
- Agent creation parameters
- Validation steps

### Log Files

Check these locations for logs:

- Agent creator output: Console or `agent_creator.log`
- AIP CLI logs: `~/.aip/logs/`

## Integration with Existing Tools

The agent is designed to work with existing GLLM Plugin tools:

- `github_merge_tool` - Combines MCP response data
- `github_formatter_tool` - Formats issue data
- `github_compliance_evaluator_tool` - Core compliance checking
- `github_report_generator_tool` - Report generation

Make sure these tools are available in your AIP platform before creating the agent.

## Security Notes

- Never commit `.env` files with real credentials
- Use environment variables for sensitive configuration
- The agent operates in read-only mode for safety
- All API calls are logged for audit purposes

## Support

For issues:

1. Check the troubleshooting section above
2. Run with `--debug` flag for detailed output
3. Verify all environment variables are set correctly
4. Test AIP and BOSA connections independently
