# GLLM Plugin Tool Contracts

This document defines custom business logic tools for the GitHub Issue Compliance Agent. These tools implement compliance checking, data processing, and reporting functionality using the GLLM Plugin framework.

**Version Scope**:

- **v1.0 (PoC)**: Read-only compliance evaluation and reporting
- **v2.0 (Future)**: Add write capabilities and advanced features

**Note**: MCP connector functions (`github_list_project_items`, `github_list_issues_comments`) are called directly by the agent and are not wrapped in GLLM Plugin tools.

## Development Setup with Poetry

### Installing Dependencies and Running Tests

All custom GLLM Plugin tools must be developed and tested using Poetry:

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install all dependencies including GLLM Plugin Framework
poetry install

# Activate Poetry shell for development
poetry shell

# Run tests for custom tools
poetry run pytest tests/

# Run specific test file
poetry run pytest tests/unit/test_compliance_evaluator.py

# Run tests with coverage
poetry run pytest --cov=src --cov-report=html

# Run linting and type checking
poetry run black src/ tests/
poetry run flake8 src/ tests/
poetry run mypy src/
```

### Loading Credentials from .env

All custom tools automatically load credentials from the `.env` file:

```python
import os
from dotenv import load_dotenv
from gllm_plugin.tools import tool_plugin
from langchain_core.tools import BaseTool

# Load credentials from .env file
load_dotenv()

@tool_plugin(version="1.0.0")
class GitHubComplianceEvaluatorTool(BaseTool):
    def _run(self, **kwargs):
        # Credentials are automatically available
        github_token = os.environ.get("GITHUB_TOKEN")
        bosa_api_key = os.environ.get("BOSA_API_KEY")
        timezone = os.environ.get("TIMEZONE", "Asia/Jakarta")

        # Use credentials for API calls
        # All credentials from .env are accessible via os.environ
```

### Testing Custom Tools with Poetry

```bash
# Create test file for custom tool
# tests/unit/test_my_custom_tool.py

import pytest
from unittest.mock import patch, MagicMock
from src.services.my_custom_tool import MyCustomTool

def test_custom_tool_execution():
    """Test custom tool with mocked credentials"""
    with patch.dict('os.environ', {
        'GITHUB_TOKEN': 'test-token',
        'BOSA_API_KEY': 'test-key',
        'TIMEZONE': 'Asia/Jakarta'
    }):
        tool = MyCustomTool()
        result = tool._run(test_input="data")
        assert result["success"] is True

# Run the test
poetry run pytest tests/unit/test_my_custom_tool.py -v
```

## Custom GLLM Plugin Tools

These tools implement business logic for compliance checking, following the existing pattern from the tools folder.

### github_merge_tool

**Description**: Merges multiple project item responses and deduplicates by repo+number (existing tool).

_This tool already exists in `/tools/github_issues_merge_tool_example.py` and follows the established pattern._

**Key Features**:

- Deduplicates issues by `repo#number` key
- Merges multiple MCP `github_list_project_items` responses
- Maintains deterministic ordering
- Returns structured merged data with counts

### github_formatter_tool

**Description**: Normalizes issue detail responses and formats them for compliance checking (existing tool).

_This tool already exists in `/tools/github_issues_formatter_tool_example.py` and follows the established pattern._

**Key Features**:

- Normalizes RAW `github_get_issue_handler` responses
- Extracts field values from project items
- Generates CSV output for analysis
- Handles multiple project associations per issue

### github_compliance_evaluator_tool

**Description**: Evaluates issues against all 7 compliance rules using Asia/Jakarta timezone.

**Input Parameters**:

```python
class ComplianceEvaluatorInput(BaseModel):
    issues: List[Dict[str, Any]] = Field(..., description="Normalized issue objects from formatter tool")
    bot_usernames: List[str] = Field(default=["dependabot", "github-actions"], description="Bot patterns to filter")
    current_date: str = Field(..., description="Current date in Asia/Jakarta timezone (YYYY-MM-DD)")
    project_number: int = Field(default=223, description="Project number for context")
```

**Implementation Pattern**:

```python
@tool_plugin(version="1.0.0")
class GitHubComplianceEvaluatorTool(BaseTool):
    name: str = "github_compliance_evaluator_tool"
    description: str = "Evaluate GitHub issues against 7 compliance rules"
    args_schema: type[BaseModel] = ComplianceEvaluatorInput

    def _run(self, issues: List[Dict], bot_usernames: List[str], current_date: str, **kwargs):
        # Parse current_date to Asia/Jakarta timezone
        # For each issue, evaluate all 7 rules:
        # Rule 1: Check assignees not empty
        # Rule 2: Check incoming_date not empty
        # Rule 3: Check due_date not empty
        # Rule 4: Check status in valid values
        # Rule 5: Check pak_on_approval for overdue issues
        # Rule 6: Check due in next 7 days
        # Rule 7: Check for human activity in last 7 days (requires comment analysis)
        # Return violation details per issue
```

**Rule Evaluation Logic**:

- **Rule #1**: `len(issue.assignees) == 0`
- **Rule #2**: `issue.incoming_date is None`
- **Rule #3**: `issue.due_date is None`
- **Rule #4**: `issue.status not in ["In Progress", "In Review", "Todo"]`
- **Rule #5**: `issue.pak_on_approval in [None, "", "Blank"] and issue.incoming_date is not None and (today - issue.incoming_date).days > 7`
- **Rule #6**: `issue.due_date is not None and 0 <= (issue.due_date - today).days <= 7`
- **Rule #7**: `no human comments in last 7 days (exclude bot_usernames)` - requires comment data from MCP

**Output**:

```python
{
  "success": bool,
  "evaluation_results": Dict[str, List[int]],  # Issue key → List of violated rule IDs
  "rule_details": Dict[str, Dict[int, str]],  # Issue key → {Rule ID → violation message}
  "summary": {
    "total_issues": int,
    "compliant_issues": int,
    "violation_count": int,
    "rules_breakdown": Dict[int, int]  # Rule ID → count of violations
  },
  "error": Optional[str]
}
```

### github_report_generator_tool

**Description**: Generates formatted compliance reports in multiple output formats.

**Input Parameters**:

```python
class ReportGeneratorInput(BaseModel):
    evaluation_results: Dict[str, List[int]] = Field(..., description="From compliance evaluator")
    issue_details: Dict[str, Dict] = Field(..., description="Issue metadata for report context")
    output_formats: List[str] = Field(default=["json", "markdown", "csv"], description="Export formats")
    include_issue_details: bool = Field(default=True, description="Include per-issue breakdown")
    project_info: Dict[str, Any] = Field(..., description="Project metadata (org, number, name)")
```

**Implementation Pattern**:

```python
@tool_plugin(version="1.0.0")
class GitHubReportGeneratorTool(BaseTool):
    name: str = "github_report_generator_tool"
    description: str = "Generate formatted compliance reports with multiple output formats"
    args_schema: type[BaseModel] = ReportGeneratorInput

    def _run(self, evaluation_results: Dict, issue_details: Dict, **kwargs):
        # Generate summary statistics
        # Create formatted outputs for each requested format:
        # - JSON: structured data for API consumption
        # - Markdown: human-readable report with tables
        # - CSV: spreadsheet-compatible format for analysis
        # Return formatted content strings
```

**Output**:

```python
{
  "success": bool,
  "reports": {
    "json": Optional[str],    # JSON formatted report
    "markdown": Optional[str], # Markdown formatted report
    "csv": Optional[str]      # CSV formatted report
  },
  "summary_stats": {
    "total_issues": int,
    "compliant_issues": int,
    "violation_count": int,
    "compliance_percentage": float,
    "rules_breakdown": Dict[int, int]
  },
  "error": Optional[str]
}
```

### github_artifact_exporter_tool

**Description**: Exports compliance reports to file system for external consumption.

**Input Parameters**:

```python
class ArtifactExporterInput(BaseModel):
    report_content: Dict[str, str] = Field(..., description="Generated reports from report generator")
    output_dir: str = Field(default="./compliance_reports", description="Output directory")
    timestamp_suffix: bool = Field(default=True, description="Include timestamp in filenames")
    project_info: Dict[str, Any] = Field(..., description="Project metadata for filename context")
```

**Implementation Pattern**:

```python
@tool_plugin(version="1.0.0")
class GitHubArtifactExporterTool(BaseTool):
    name: str = "github_artifact_exporter_tool"
    description: str = "Export compliance reports to filesystem with proper naming conventions"
    args_schema: type[BaseModel] = ArtifactExporterInput

    def _run(self, report_content: Dict[str, str], output_dir: str, **kwargs):
        # Create output directory if not exists
        # Generate timestamped filenames
        # Write reports to files
        # Return list of created file paths
```

**File Naming Convention**:

- `github_compliance_proj{project_number}_YYYY-MM-DD_HH-MM.json`
- `github_compliance_proj{project_number}_YYYY-MM-DD_HH-MM.md`
- `github_compliance_proj{project_number}_YYYY-MM-DD_HH-MM.csv`

**Output**:

```python
{
  "success": bool,
  "exported_files": List[str],  # List of created file paths
  "output_directory": str,  # Confirmed output directory
  "file_sizes": Dict[str, int],  # Filename → size in bytes
  "error": Optional[str]
}
```

## Tool Integration Flow

The GLLM Plugin tools work with MCP connector functions in the following sequence:

### v1.0 PoC (Read-Only)

1. **Data Collection Phase** (Agent direct MCP calls):

   - `github_list_project_items` (MCP) → Get project issues by status
   - `github_get_issue_handler` (MCP) → Get detailed issue information
   - `github_list_issues_comments` (MCP) → Get comment history for Rule #7

2. **Data Processing Phase** (GLLM Plugin tools):

   - `github_merge_tool` → Deduplicate and merge responses
   - `github_formatter_tool` → Normalize issue data

3. **Analysis Phase** (GLLM Plugin tools):

   - `github_compliance_evaluator_tool` → Evaluate all compliance rules

4. **Reporting Phase** (GLLM Plugin tools):
   - `github_report_generator_tool` → Generate formatted reports
   - `github_artifact_exporter_tool` → Export to filesystem

### v2.0 Future (Write-Capable)

5. **Notification Phase** (v2.0 addition):
   - `github_comment_poster_tool` → Post violation comments to issues
   - `github_idempotency_manager_tool` → Prevent duplicate comments
   - `github_mention_tagger_tool` → Tag assignees in violations

This design keeps MCP connector calls at the agent level while implementing business logic in custom GLLM Plugin tools, following the established patterns from the existing tools folder.
