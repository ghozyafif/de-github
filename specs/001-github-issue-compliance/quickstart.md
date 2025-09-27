# Quickstart: GitHub Issue Compliance Agent

This guide walks through setting up and running the GitHub Issue Compliance Agent (v1.0 PoC) as a background process on the company Agentic AI platform. The agent samples 15 issues (5 per status) and outputs results to terminal only.

## Prerequisites

- Access to company Agentic AI Platform
- GitHub Projects v2 with MCP connector configured
- GitHub token with required scopes: `project:read`, `repo:read`, `read:org`

## Platform Configuration

### Agent Setup

1. Create new agent in Agentic AI Platform
2. Use the following configuration:

````yaml
Version: 1.0.0 (PoC - Read-Only)
Agent ID: github_issue_compliance_agent_v1
Display Name: GitHub Issue Compliance Agent (Background)
Description: Background agent that samples 15 issues (5 per status), checks 7 compliance rules, outputs JSON to terminal
Model: Claude Sonnet 4
Tools:
  - MCP: github_projects_v2 (read-only: project items, issue details, comments)
    Direct access: github_list_project_items, github_get_issue_handler, github_list_issues_comments
  - GLLM Python Plugin Tools (4 self-contained tools, no imports):
    - github_merge_tool [existing], github_formatter_tool [existing]
    - github_compliance_evaluator_tool (inline utilities), github_report_generator_tool (terminal output)
Timeout (seconds): 720
```### System Instructions

````

You are a GitHub Project compliance monitoring agent (v1.0 PoC - Background Mode). Your role is to:

1. Sample 15 issues (5 per status: In Progress, In Review, Todo)
2. Check sampled issues for compliance with 7 defined rules
3. Output comprehensive JSON report to terminal
4. Exit after single execution (no interaction)

IMPORTANT: v1.0 CONSTRAINTS:

- READ-ONLY access only - never modify issues or post comments
- On-demand execution only - no automated scheduling
- Single-agent architecture - direct MCP calls + GLLM Plugin tools

OPERATIONAL POLICY:

- Use Asia/Jakarta (UTC+7) timezone for all date calculations
- Exclude bot comments when checking "no updates in 7 days" rule
- Provide actionable violation descriptions in reports
- Support interactive queries about specific violations

COMPLIANCE RULES:

1. Empty assignees field
2. Empty incoming date field
3. Empty due date field
4. Empty status field
5. Empty "Pak On's Approval for Timeline" field AND more than 7 days from incoming date
6. Will be due in next 7 days (warning)
7. No human comments in last 7 days

GUARDRAILS:

- Never modify issue statuses or field values
- Never post comments or make any write operations
- Respect rate limits with exponential backoff
- Log all actions for audit purposes

````

## Environment Variables

**Important**: All credentials are already configured in the `.env` file at the project root. The agent will automatically load these credentials when needed.

### Using the .env File

```bash
# The .env file is already set up with all required credentials
# Location: /home/gh/Documents/GL/de-github/.env

# To view available credentials (without exposing values):
cat .env | grep -E "^[A-Z_]+=" | cut -d'=' -f1

# The agent automatically loads these using python-dotenv:
from dotenv import load_dotenv
load_dotenv()  # Loads all credentials from .env file
```

### Available Credentials in .env

```bash
# AIP Platform Configuration
AIP_API_URL="https://aip.obrol.id"           # Already configured
AIP_API_KEY="QKQ9S957PqQNLYqbir8qoBodm"      # Already configured (anonymized)
AIP_API_TIMEOUT=720                          # Already configured

# GitHub Configuration
GITHUB_ORGANIZATION="GDP-ADMIN"              # Already configured
GITHUB_PROJECT_ID=223                         # Already configured (numeric)

# BOSA MCP Configuration
BOSA_API_KEY_CLIENT="sk-client-xxxxx"        # Already configured (anonymized)
BOSA_BASE_URL="https://api.bosa.id"         # Already configured
BOSA_USER_IDENTIFIER="jamessaldo"            # Already configured
BOSA_USER_SECRET="sk-user-xxxxx"            # Already configured (anonymized)

# Operational Settings
TIMEZONE="Asia/Jakarta"
ISSUES_PER_STATUS=5
BOT_USERNAMES="github-actions[bot],dependabot[bot],renovate[bot],codecov[bot]"
OUTPUT_MODE="terminal_json"

# GDP Labs Authentication (for GLLM Plugin)
GCLOUD_PROJECT="gdp-labs"                    # Already configured

# v2.0 Future Features (not used in v1.0)
# COMMENT_THROTTLE_HOURS="24"
# SCHEDULED_EXECUTION="false"
# NOTIFICATION_CHANNELS=""
````

**Note**: Never commit the `.env` file to version control. It's already included in `.gitignore`.

## Agent Architecture & Integration

### How the Agent Works with AIP Platform

The GitHub Issue Compliance Agent uses a hybrid architecture combining AIP platform orchestration with GLLM Plugin tools:

1. **AIP Platform Layer** (Claude Sonnet 4):

   - Receives execution request via AIP CLI
   - Orchestrates the compliance checking workflow
   - Makes direct MCP calls to GitHub Projects v2
   - Outputs results to terminal and exits

2. **GLLM Plugin Tools Layer** (Python):

   - Implements business logic for compliance evaluation
   - Processes data from MCP responses
   - Generates formatted JSON for terminal output
   - Self-contained tools with inline utilities

3. **Integration Flow**:
   ```
   User Request → AIP Agent (Claude Sonnet 4)
       ↓
   MCP Calls → GitHub Projects v2 API
       ↓
   Raw Data → GLLM Plugin Tools
       ↓
   Processing → Compliance Evaluation
       ↓
   Reports → Terminal JSON Output → Exit
   ```

### GDP Labs Authentication Setup

Before using GLLM Plugin tools, you must authenticate with GDP Labs:

```bash
# Step 1: Install gcloud CLI
# Follow: https://cloud.google.com/sdk/docs/install

# Step 2: Authenticate with Google Cloud
gcloud auth login
gcloud auth application-default login

# Step 3: Configure Poetry for GDP Labs artifact repository
poetry config http-basic.gen-ai oauth2accesstoken "$(gcloud auth print-access-token)"

# Step 4: Verify authentication
poetry source show gen-ai
# Should display the GDP Labs repository URL without errors
```

**Important**: The authentication token expires after ~1 hour. Re-run Step 3 if you encounter 401 errors during package installation.

### BOSA MCP Integration

The agent uses BOSA's MCP connector for GitHub API access:

#### Local Testing Setup

Before registering with AIP, test BOSA MCP locally:

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Run inspector to explore BOSA GitHub functions
DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector
```

#### BOSA MCP Configuration

```python
# Configuration for BOSA GitHub MCP
from gllm_tools.mcp.client.client import MCPClient
import os
from dotenv import load_dotenv

load_dotenv()  # Load credentials from .env

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

client = MCPClient(servers)
```

#### Required Environment Variables for BOSA

```bash
# BOSA MCP Configuration (from .env)
BOSA_API_KEY_CLIENT="sk-client-xxxxx"   # BOSA client API key
BOSA_BASE_URL="https://api.bosa.id"     # BOSA API base URL
BOSA_USER_IDENTIFIER="username"         # Your BOSA username
BOSA_USER_SECRET="sk-user-xxxxx"        # BOSA user secret key

# GitHub Configuration
GITHUB_ORGANIZATION="GDP-ADMIN"         # Your GitHub org
GITHUB_PROJECT_ID=223                    # GitHub project number
```

#### Available BOSA GitHub Functions

- `github_list_project_items` - List project items by status
- `github_get_issue_handler` - Get detailed issue information
- `github_list_issues_comments` - Get issue comments

For detailed API contracts, see: https://api.bosa.id/docs#tag/Github

## Usage Examples

### Background Compliance Check

**Input** (via AIP CLI):

```bash
aip agents run <AGENT_ID> \
  --input '{
    "project_identifier": "GDP-ADMIN/223",
    "statuses": ["In Progress","In Review","Todo"],
    "issues_per_status": 5
  }' \
  --timeout 300
```

**Expected Flow**:

1. Agent calls MCP `github_list_project_items` 3 times (5 issues per status)
2. Agent calls MCP `github_get_issue_handler` and `github_list_issues_comments` for each of 15 issues
3. Agent uses GLLM Plugin `github_merge_tool` to combine responses
4. Agent uses GLLM Plugin `github_formatter_tool` to normalize data
5. Agent calls GLLM Plugin `github_compliance_evaluator_tool` (with inline utilities) for evaluation
6. Agent uses GLLM Plugin `github_report_generator_tool` to format terminal JSON
7. Agent outputs complete JSON report to terminal
8. Agent exits (background mode, no interaction)

**Sample Terminal Output**:

```json
{
  "execution_time": "72 seconds",
  "timestamp": "2025-09-24T15:30:00+07:00",
  "project": "GDP-ADMIN/223",
  "issues_sampled": 15,
  "compliance_summary": {
    "compliant_issues": 7,
    "violating_issues": 8,
    "compliance_rate": 0.467
  },
  "violations_by_rule": {
    "rule_1_empty_assignees": 2,
    "rule_2_empty_incoming_date": 1,
    "rule_3_empty_due_date": 3,
    "rule_4_empty_status": 0,
    "rule_5_missing_approval_overdue": 1,
    "rule_6_due_soon_warning": 4,
    "rule_7_no_recent_updates": 2
  },
  "high_priority_violations": [
    {
      "issue_number": 534,
      "title": "Web Search Contract",
      "url": "https://github.com/GDP-ADMIN/dummy-gl-sdk/issues/534",
      "violated_rules": [1, 5],
      "severity": "high"
    }
  ],
  "status": "completed"
}
```

### Query Specific Violations

**Input**:

```
Show me all issues that are missing Pak On's approval and are overdue.
```

**Expected Response**:

- Agent queries violations data
- Filters for Rule #5 violations
- Returns issue URLs and details

### Dry Run Mode

**Input**:

```
Run a compliance check in dry-run mode - don't post any comments.
```

**Expected Behavior**:

- All evaluation logic runs normally
- Comments are generated but not posted
- Report shows what would have been posted

## Testing Scenarios

### Scenario 1: New Violations (v1.0 Background Mode)

1. Create test issue with missing assignee
2. Run background agent for 15 issues
3. Verify Rule #1 violation appears in terminal JSON output
4. Verify complete violation details included
5. Confirm agent exits after output (no interaction)

### Scenario 2: Mixed Violations (v1.0 Read-Only)

1. Create issue violating Rules #1, #3, #7
2. Run compliance check
3. Verify all 3 violations appear in compliance report
4. Query agent about specific issue violations
5. Verify detailed violation explanations provided

### Scenario 3: Due Soon Warning (v1.0 Read-Only)

1. Create issue with due date in 5 days
2. Run compliance check
3. Verify Rule #6 warning appears in report with appropriate severity
4. Confirm warning tone in exported reports

## Troubleshooting

### No Terminal Output

- Check agent timeout setting (should be 300-720s)
- Verify MCP connector returns data for 15 issues
- Check GLLM Plugin tools are loaded correctly

### Incomplete JSON Output

- Verify all 15 issues fetched (5 per status)
- Check error handling in compliance evaluator
- Confirm terminal buffer size adequate

### Wrong Timezone in Reports

- Confirm `TIMEZONE="Asia/Jakarta"` in environment
- Check date parsing in `github_compliance_evaluator_tool` tool

### Bot Comments Being Counted

- Review `BOT_USERNAMES` configuration
- Add missing bot patterns to filter list
- Check comment author detection logic

## v2.0 Roadmap (Future Phases)

### Phase v2.0: Write Capabilities

- **Comment Posting**: Automated violation comments to issues
- **Idempotency**: Prevent duplicate comments with hash-based tracking
- **Assignee Tagging**: Direct mentions in violation comments
- **Comment Throttling**: Max 1 comment per issue per 24 hours

### Phase v2.1: Multi-Agent Architecture

- **Specialized Agents**: Fetcher, Auditor, Reporter, Notifier, Orchestrator
- **JSON Message Contracts**: Clean separation of concerns
- **Scalable Processing**: Parallel execution capabilities

### Phase v2.2: Advanced Features

- **Scheduled Execution**: Daily automated compliance checks
- **Webhook Integration**: Real-time issue change monitoring
- **Advanced Notifications**: Slack/Teams integration
- **Dashboard**: Web-based compliance monitoring interface## Monitoring

Key metrics to track:

- Issues checked per run
- Violations by rule type
- Comments posted vs. skipped (idempotency)
- API rate limit usage
- Rule evaluation performance

## Rollout Plan

**Phase 1: Dry Run Only**

- Set `DRY_RUN="true"`
- Run daily for 1 week
- Validate rule evaluation accuracy
- Review generated comment content

**Phase 2: Limited Live Comments**

- Set `DRY_RUN="false"`
- Whitelist specific assignees/teams for comments
- Monitor feedback and adjust messaging

**Phase 3: Full Deployment**

- Remove assignee whitelist
- Enable daily scheduled runs
- Add weekly summary reports to PM channels
