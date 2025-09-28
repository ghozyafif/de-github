#!/usr/bin/env python3
"""GitHub Issue Compliance Agent Creator.

Script to create and configure a single GitHub compliance agent using AIP CLI
with BOSA MCP integration for GitHub Projects v2 API access.

Usage:
    python create_agent.py [--config CONFIG_FILE] [--dry-run] [--debug]

Requirements:
    - aip CLI installed (pipx install glaip-sdk)
    - BOSA MCP credentials configured
    - GDP Labs authentication via gcloud
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()



@dataclass
class MCPConfig:
    """Configuration for BOSA GitHub MCP connection."""
    name: str = "bosa-github-mcp"
    url: str = "https://api.bosa.id/github/mcp"
    api_key_env: str = "BOSA_API_KEY_CLIENT"
    auth_token_env: str = "BOSA_USER_SECRET"
    organization: str = "GDP-ADMIN"
    project_number: int = 223
    functions: Optional[List[str]] = None
    rate_limit_per_minute: int = 60
    retry_max: int = 3
    backoff_base: int = 2

    def __post_init__(self):
        """Initialize default functions if not provided."""
        if self.functions is None:
            self.functions = [
                "github_list_project_items",
                "github_get_issue_handler",
                "github_list_issues_comments"
            ]

    def to_config_dict(self) -> Dict[str, Any]:
        """Convert to AIP MCP configuration format."""
        api_key = os.environ.get(self.api_key_env)
        auth_token = os.environ.get(self.auth_token_env)

        if not api_key:
            raise ValueError(f"Environment variable {self.api_key_env} not set")
        if not auth_token:
            raise ValueError(f"Environment variable {self.auth_token_env} not set")

        return {
            "url": self.url,
            "headers": {
                "X-Api-Key": api_key,
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            "organization": self.organization,
            "project_number": self.project_number,
            "functions": self.functions,
            "rate_limit": {
                "requests_per_minute": self.rate_limit_per_minute,
                "retry_max": self.retry_max,
                "backoff_base": self.backoff_base
            }
        }


@dataclass
class AgentConfig:
    """Configuration for GitHub compliance agent."""
    name: str = "github-compliance-agent-v1"
    display_name: str = "GitHub Issue Compliance Agent (v1.0 PoC)"
    instruction: str = ""
    model: str = "anthropic/claude-sonnet-4-0"
    timeout: int = 720
    tools: Optional[List[str]] = None
    mcps: Optional[List[str]] = None
    chat_history_limit: int = 20

    def __post_init__(self):
        """Initialize default instruction if not provided."""
        if not self.instruction:
            self.instruction = self._get_default_instruction()
        if self.tools is None:
            self.tools = [
                "github_merge_tool",
                "github_compliance_evaluator_tool",
                "github_report_generator_tool",
                "github_formatter_tool"
            ]
        if self.mcps is None:
            self.mcps = ["bosa-github-mcp"]

    def _get_default_instruction(self) -> str:
        """Get default comprehensive instruction for the agent."""
        return '''You are a GitHub Project compliance monitoring agent (v1.0 PoC - Read-Only). Your role is to:

**PRIMARY OBJECTIVES:**
1. Check GitHub Project issues for compliance with 7 defined rules
2. Generate comprehensive reports of violations with actionable details
3. Respond to queries about compliance status and specific violations
4. Export reports in multiple formats (JSON/CSV/Markdown)

**v1.0 CONSTRAINTS (READ-ONLY MODE):**
- READ-ONLY access only - never modify issues or post comments
- On-demand execution only - no automated scheduling
- Single-agent architecture with direct MCP calls + GLLM Plugin tools
- Process up to 15 sampled issues (5 per status: In Progress, In Review, Todo)
- Complete workflow within 720 seconds timeout
- Use Asia/Jakarta (UTC+7) timezone for all date calculations
- Output terminal JSON reports only (no file storage)

**AVAILABLE TOOLS & CAPABILITIES:**

*BOSA GitHub MCP Functions (for GitHub API access):*
- `github_list_project_items`: Retrieve project items/issues from GDP-ADMIN project #223
- `github_list_issues_comments`: Fetch comments for issues to check R7 compliance

*GLLM Plugin Tools (for processing and reporting):*
- `github_compliance_evaluator_tool`: Core compliance checking logic against the 7 rules
- `github_report_generator_tool`: Generate structured JSON/CSV/Markdown compliance reports
- `github_merge_tool`: Merge and consolidate data from multiple API calls
- `github_formatter_tool`: Format data for consistent output and presentation

**WORKFLOW - USE TOOLS IN THIS ORDER:**
1. Use `github_list_project_items` via BOSA MCP to get project issues
2. Use `github_list_issues_comments` via BOSA MCP to get comments for R7 evaluation
3. Use `github_merge_tool` to consolidate all retrieved data
4. Use `github_compliance_evaluator_tool` to evaluate against 7 rules
5. Use `github_report_generator_tool` to create final compliance report
6. Use `github_formatter_tool` for final output formatting if needed

**COMPLIANCE RULES TO EVALUATE:**
1. **R1**: Empty assignees field - Issues must have at least one assignee
2. **R2**: Empty incoming date field - All issues must have an incoming date set
3. **R3**: Empty due date field - All issues must have a due date specified
4. **R4**: Empty status field - Issues must have a valid status (In Progress, In Review, Todo)
5. **R5**: Missing "Pak On's Approval for Timeline" AND more than 7 days from incoming date
6. **R6**: Will be due in next 7 days (warning level - not critical but flagged)
7. **R7**: No human comments in last 7 days (excludes bot comments)

**OPERATIONAL PROCEDURES:**
- Use BOSA MCP connector for all GitHub API interactions (organization: GDP-ADMIN, project: #223)
- Apply exponential backoff for rate limiting (60 requests/minute max)
- Filter out bot comments when checking R7 (usernames ending in [bot], github-actions, dependabot, etc.)
- Calculate date differences using Jakarta timezone (UTC+7)
- Provide specific violation descriptions with issue numbers and URLs
- Include severity levels (high/medium/low) for prioritization
- Always use the custom tools - they contain specialized logic for this compliance workflow

**OUTPUT FORMAT:**
Generate structured JSON reports containing:
- Project information and sampling details
- Compliance summary with rates and totals
- Violations categorized by rule with detailed descriptions
- Execution metadata (timing, status, next actions)
- Human-readable violation explanations

**ERROR HANDLING:**
- Gracefully handle MCP timeouts and network errors
- Continue processing with partial data if some calls fail
- Log all errors with context for debugging
- Provide meaningful error messages in reports
- Use retry logic built into the custom tools

**GUARDRAILS:**
- Never attempt to modify issue statuses or field values
- Never post comments or make any write operations to GitHub
- Respect rate limits and implement proper backoff strategies
- Validate all input data before processing
- Log all API calls for audit purposes
- Always use the provided custom tools rather than trying to implement logic manually'''


class AgentCreator:
    """Creates and configures GitHub compliance agent with BOSA MCP."""

    def __init__(self, dry_run: bool = False, debug: bool = False):
        """Initialize AgentCreator with optional dry-run and debug modes."""
        self.dry_run = dry_run
        self.debug = debug
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def _run_command(self, cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run shell command with proper error handling."""
        self.logger.debug(f"Running command: {' '.join(cmd)}")

        if self.dry_run:
            self.logger.info(f"DRY RUN: Would execute: {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check
            )

            if result.stdout:
                self.logger.debug(f"Command output: {result.stdout}")
            if result.stderr and result.returncode != 0:
                self.logger.error(f"Command error: {result.stderr}")

            return result

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {e}")
            self.logger.error(f"stdout: {e.stdout}")
            self.logger.error(f"stderr: {e.stderr}")
            raise

    def check_prerequisites(self) -> bool: # noqa: PLR0911
        """Check if all prerequisites are met."""
        self.logger.info("🔍 Checking prerequisites...")

        # Check if aip CLI is installed
        try:
            result = self._run_command(['aip', '--version'], check=False)
            if result.returncode != 0:
                self.logger.error("❌ AIP CLI not found. Install with: pipx install glaip-sdk")
                return False
            self.logger.info(f"✅ AIP CLI found: {result.stdout.strip()}")
        except FileNotFoundError:
            self.logger.error("❌ AIP CLI not found. Install with: pipx install glaip-sdk")
            return False

        # Check AIP connection
        try:
            result = self._run_command(['aip', 'status'], check=False)
            if result.returncode != 0:
                self.logger.error("❌ Cannot connect to AIP. Check configuration.")
                self.logger.error("Run: aip config list")
                return False
            self.logger.info("✅ AIP connection verified")
        except Exception as e:
            self.logger.error(f"❌ AIP status check failed: {e}")
            return False

        # Check environment variables for BOSA MCP
        mcp_config = MCPConfig()
        try:
            api_key = os.environ.get(mcp_config.api_key_env)
            auth_token = os.environ.get(mcp_config.auth_token_env)

            if not api_key:
                self.logger.error(f"❌ Missing environment variable: {mcp_config.api_key_env}")
                return False
            if not auth_token:
                self.logger.error(f"❌ Missing environment variable: {mcp_config.auth_token_env}")
                return False

            self.logger.info("✅ BOSA MCP credentials found")
        except Exception as e:
            self.logger.error(f"❌ BOSA MCP credential check failed: {e}")
            return False

        return True

    def create_mcp_connection(self, mcp_config: MCPConfig) -> Optional[str]:
        """Create BOSA GitHub MCP connection."""
        self.logger.info(f"🔗 Creating MCP connection: {mcp_config.name}")

        # Check if MCP already exists
        try:
            result = self._run_command(['aip', 'mcps', 'get', mcp_config.name], check=False)
            if result.returncode == 0:
                self.logger.info(f"✅ MCP connection '{mcp_config.name}' already exists")
                return mcp_config.name
        except Exception:
            pass  # MCP doesn't exist, we'll create it

        # Create MCP configuration
        try:
            config_dict = mcp_config.to_config_dict()
            config_json = json.dumps(config_dict, indent=2)

            self.logger.debug(f"MCP config: {config_json}")

            # Create the MCP connection
            cmd = [
                'aip', 'mcps', 'create',
                '--name', mcp_config.name,
                '--transport', 'http',
                '--config', config_json
            ]

            result = self._run_command(cmd)

            if result.returncode == 0:
                self.logger.info(f"✅ MCP connection '{mcp_config.name}' created successfully")
                return mcp_config.name
            else:
                self.logger.error(f"❌ Failed to create MCP connection: {result.stderr}")
                return None

        except Exception as e:
            self.logger.error(f"❌ Error creating MCP connection: {e}")
            return None

    def test_mcp_connection(self, mcp_name: str) -> bool:
        """Test MCP connection."""
        self.logger.info(f"🧪 Testing MCP connection: {mcp_name}")

        try:
            result = self._run_command(['aip', 'mcps', 'test-connection', mcp_name], check=False)

            if result.returncode == 0:
                self.logger.info("✅ MCP connection test successful")
                return True
            else:
                self.logger.error(f"❌ MCP connection test failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error testing MCP connection: {e}")
            return False

    def create_agent(self, agent_config: AgentConfig, mcp_names: List[str]) -> Optional[str]:
        """Create GitHub compliance agent."""
        self.logger.info(f"🤖 Creating agent: {agent_config.name}")

        # Check if agent already exists
        try:
            result = self._run_command(['aip', 'agents', 'get', agent_config.name], check=False)
            if result.returncode == 0:
                self.logger.info(f"✅ Agent '{agent_config.name}' already exists")
                return agent_config.name
        except Exception:
            pass  # Agent doesn't exist, we'll create it

        try:
            # Build agent creation command
            cmd = [
                'aip', 'agents', 'create',
                '--name', agent_config.name,
                # '--model', agent_config.model,
                '--timeout', str(agent_config.timeout)
            ]

            # Add tools if specified
            if agent_config.tools:
                for tool in agent_config.tools:
                    cmd.extend(['--tools', tool])

            # Add MCPs if specified
            if mcp_names:
                for mcp in mcp_names:
                    cmd.extend(['--mcps', mcp])

            cmd.extend(['--instruction', agent_config.instruction])

            result = self._run_command(cmd)

            if result.returncode == 0:
                self.logger.info(f"✅ Agent '{agent_config.name}' created successfully")
                return agent_config.name
            else:
                self.logger.error(f"❌ Failed to create agent: {result.stderr}")
                return None

        except Exception as e:
            self.logger.error(f"❌ Error creating agent: {e}")
            return None

    def validate_agent(self, agent_name: str) -> bool:
        """Validate agent configuration."""
        self.logger.info(f"✅ Validating agent: {agent_name}")

        try:
            # Get agent details
            result = self._run_command(['aip', 'agents', 'get', agent_name, '--view', 'json'])

            if result.returncode != 0:
                self.logger.error(f"❌ Cannot get agent details: {result.stderr}")
                return False

            try:
                agent_data = json.loads(result.stdout)
                self.logger.debug(f"Agent details: {json.dumps(agent_data, indent=2)}")

                # Validate key fields
                if not agent_data.get('name'):
                    self.logger.error("❌ Agent missing name field")
                    return False

                if not agent_data.get('instruction'):
                    self.logger.error("❌ Agent missing instruction field")
                    return False

                self.logger.info("✅ Agent validation passed")
                return True

            except json.JSONDecodeError as e:
                self.logger.error(f"❌ Invalid JSON response: {e}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error validating agent: {e}")
            return False

    def create_tools(self, tools_dir: str = "tools") -> List[str]:
        """Create tools from Python files in tools directory."""
        self.logger.info(f"🔧 Creating tools from directory: {tools_dir}")

        tools_path = Path(tools_dir)
        if not tools_path.exists():
            self.logger.error(f"❌ Tools directory not found: {tools_dir}")
            return []

        created_tools = []

        # Get all Python files in tools directory
        tool_files = list(tools_path.glob("*.py"))

        for tool_file in tool_files:
            tool_name = tool_file.stem  # Remove .py extension
            self.logger.info(f"📦 Processing tool: {tool_name}")

            # Check if tool already exists
            try:
                result = self._run_command(['aip', 'tools', 'get', tool_name], check=False)
                if result.returncode == 0:
                    self.logger.info(f"✅ Tool '{tool_name}' already exists")
                    created_tools.append(tool_name)
                    continue
            except Exception:
                pass  # Tool doesn't exist, we'll create it

            try:
                # Create tool from file
                cmd = [
                    'aip', 'tools', 'create',
                    '--file', str(tool_file),
                    '--name', tool_name,
                    '--description', f"GitHub compliance tool: {tool_name}",
                    '--tags', "github,compliance,validation"
                ]

                result = self._run_command(cmd)

                if result.returncode == 0:
                    self.logger.info(f"✅ Tool '{tool_name}' created successfully")
                    created_tools.append(tool_name)
                else:
                    self.logger.error(f"❌ Failed to create tool '{tool_name}': {result.stderr}")

            except Exception as e:
                self.logger.error(f"❌ Error creating tool '{tool_name}': {e}")

        self.logger.info(f"📋 Created/verified {len(created_tools)} tools: {', '.join(created_tools)}")
        return created_tools

    def create_complete_setup(self, config_file: Optional[str] = None) -> bool: # noqa: PLR0911
        """Create complete agent setup with MCP registration."""
        self.logger.info("🚀 Starting complete agent setup...")

        # Load configuration
        if config_file and Path(config_file).exists():
            self.logger.info(f"📁 Loading configuration from: {config_file}")
            with open(config_file, 'r') as f:
                config_data = json.load(f)

            mcp_config = MCPConfig(**config_data.get('mcp', {}))
            agent_config = AgentConfig(**config_data.get('agent', {}))
        else:
            self.logger.info("📋 Using default configuration")
            mcp_config = MCPConfig()
            agent_config = AgentConfig()

        # Step 1: Check prerequisites
        if not self.check_prerequisites():
            self.logger.error("❌ Prerequisites check failed")
            return False

        # Step 2: Create tools from tools directory
        created_tools = self.create_tools()
        if not created_tools:
            self.logger.error("❌ No tools were created successfully")
            return False

        # Verify that all required tools were created
        required_tools = agent_config.tools or []
        missing_tools = set(required_tools) - set(created_tools)
        if missing_tools:
            self.logger.error(f"❌ Missing required tools: {', '.join(missing_tools)}")
            return False

        # Step 3: Create MCP connection
        mcp_name = self.create_mcp_connection(mcp_config)
        if not mcp_name:
            self.logger.error("❌ MCP connection creation failed")
            return False

        # Step 4: Test MCP connection (optional)
        # if not self.test_mcp_connection(mcp_name):
        #     self.logger.error("❌ MCP connection test failed")
        #     return False

        # Step 5: Create agent with tools and MCP
        agent_name = self.create_agent(agent_config, [mcp_name])
        if not agent_name:
            self.logger.error("❌ Agent creation failed")
            return False

        # Step 6: Validate agent
        if not self.validate_agent(agent_name):
            self.logger.error("❌ Agent validation failed")
            return False

        # Success!
        self.logger.info("🎉 Agent setup completed successfully!")
        self.logger.info(f"Agent name: {agent_name}")
        self.logger.info(f"MCP connection: {mcp_name}")
        self.logger.info(f"Tools created: {', '.join(created_tools)}")
        self.logger.info("")
        self.logger.info("Next steps:")
        self.logger.info(f"1. Test agent: aip agents run {agent_name} --input 'Check compliance for GDP-ADMIN/223'")
        self.logger.info(f"2. View agent details: aip agents get {agent_name}")
        self.logger.info(f"3. Test MCP: aip mcps test-connection {mcp_name}")
        self.logger.info("4. List tools: aip tools list")

        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create GitHub compliance agent with BOSA MCP integration"
    )
    parser.add_argument(
        '--config',
        help='Configuration file path (JSON format)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    # Create agent creator
    creator = AgentCreator(dry_run=args.dry_run, debug=args.debug)

    # Run complete setup
    success = creator.create_complete_setup(args.config)

    if success:
        print("\n✅ GitHub compliance agent setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Agent setup failed. Check logs above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
