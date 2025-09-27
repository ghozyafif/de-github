# GitHub Issue Compliance Agent

Automated GitHub Project compliance agent that checks issues against defined rules and outputs JSON reports.

## Version 1.0 PoC - Background Agent (Read-Only)

This agent runs in background mode, checks 15 sampled issues (5 per status) against 7 compliance rules, and outputs a comprehensive JSON report to terminal.

## Features

- Automated compliance checking against 7 defined rules
- Issue sampling (5 per status: Todo, In Progress, In Review)
- Terminal JSON output with detailed violation reporting
- Asia/Jakarta timezone support
- Bot comment filtering
- No file storage - terminal output only

## Requirements

- Python 3.11+
- Poetry package manager
- Access to GDP Labs GLLM Plugin repository
- BOSA MCP GitHub connector credentials

## Quick Start

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Configure GDP Labs repository
poetry source add gen-ai https://asia-southeast2-python.pkg.dev/gdp-labs/gen-ai/simple/
gcloud auth login
poetry config http-basic.gen-ai oauth2accesstoken "$(gcloud auth print-access-token)"

# Install dependencies
poetry install

# Run tests
poetry run pytest tests/ -v
```

## Project Structure

```
├── src/
│   ├── services/
│   │   ├── compliance_evaluator.py  # Main compliance checking logic
│   │   └── report_generator.py      # JSON report formatter
│   └── cli/
│       └── orchestrator.py           # Optional test harness
├── tests/
│   ├── unit/                        # Unit tests
│   ├── integration/                 # Integration tests
│   └── fixtures/
│       └── mcp/                     # MCP response fixtures
├── configs/
│   ├── agent_workflow.yaml          # Agent workflow configuration
│   └── background_agent_config.yaml # Platform configuration
└── pyproject.toml                   # Poetry dependencies
```

## 7 Compliance Rules

1. **Empty Assignees**: Issue has no assignees in content.assignees array
2. **Empty Incoming Date**: Missing "Incoming Date" field in field_values
3. **Empty Due Date**: Missing "Due Date" field in field_values
4. **Empty Status**: Missing or invalid "Status" field in field_values
5. **Missing Pak On Approval (Overdue)**: "Pak On's Approval for Timeline" field empty AND more than 7 days since incoming date
6. **Due Soon Warning**: Issue will be due within next 7 days (using Asia/Jakarta timezone)
7. **No Recent Updates**: No human comments (excluding bot/system comments) in last 7 days

## Usage

The agent runs in background mode and outputs JSON to terminal:

```bash
# Run the agent (when deployed to platform)
python -m src.cli.orchestrator
```

## Testing

```bash
# Run all tests
poetry run pytest tests/ -v

# Run unit tests only
poetry run pytest tests/unit/ -v

# Run integration tests
poetry run pytest tests/integration/ -v

# Check coverage
poetry run pytest --cov=src tests/ -v
```

## Performance

- Target execution time: <2 minutes
- Memory usage: <100MB per execution
- MCP calls: ~33 total (optimized for minimal calls)
