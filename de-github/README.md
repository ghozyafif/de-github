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

## Compliance Rules

1. **Maximum Draft Duration**: Draft issues must be ready within 5 days
2. **Maximum Todo Duration**: Todo issues must start within 5 days
3. **Maximum In Progress Duration**: In Progress issues must complete within 8 days
4. **Maximum In Review Duration**: In Review issues must complete within 5 days
5. **Maximum Done Duration**: Done issues must be closed within 3 days
6. **Comment Frequency**: Active issues need comments every 3 days
7. **Bot Comments**: Bot/system comments don't count for activity

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