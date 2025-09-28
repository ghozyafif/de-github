# Implementation Plan: GitHub Issue Compliance Agent

**Branch**: `001-github-issue-compliance` | **Date**: 2025-09-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/home/gh/Documents/GL/de-github/specs/001-github-issue-compliance/spec.md`

## Execution Flow (/plan command scope)

```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:

- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

**v1.0 PoC (Background Agent Read-Only)**: Automated GitHub Project compliance background agent that runs in automated mode, checks 15 sampled issues (5 per status) against 6 defined rules, and outputs a comprehensive JSON report to terminal. Uses company Agentic AI platform with Claude Sonnet 4, MCP integration for GitHub Projects v2, and self-contained Python GLLM Plugin tools with modular SOLID-compliant architecture. Workflow: github_list_project_items (with pagination) → github_merge_tool → github_compliance_evaluator_tool → github_report_generator_tool. **No file storage or write operations** - terminal output only.

**v2.0 Full (Write-Capable)**: [FUTURE] Extends v1 with automated comment posting and scheduled execution capabilities.

## Technical Context

**Language/Version**: Python 3.11+ (GLLM Plugin), Claude Sonnet 4 (Orchestrator)
**Primary Dependencies**: GLLM Plugin Framework, BOSA MCP GitHub connector, Claude Sonnet 4 model
**Storage**: No storage - terminal JSON output only
**MCP Provider**: BOSA (https://api.bosa.id/github/mcp)  
**Testing**: pytest with fixtures for rule evaluation, MCP mock integration tests  
**Target Platform**: Company Agentic AI Platform (cloud-hosted)
**Project Type**: single - agent tools with orchestrator pattern  
**Performance Goals**: Process 15 sampled issues (5 per status), complete agent workflow within 2 minutes, optimize for minimal MCP calls with pagination handling
**Constraints**: <720s total agent timeout, <100MB memory per execution, Asia/Jakarta timezone, exponential backoff rate limiting  
**Scale/Scope**: Single GitHub Project monitoring, 6 compliance rules, on-demand execution (v1.0 PoC)

## Technical Implementation Details

### Modular Architecture Design (SOLID Compliance)

```
src/
├── utils/                    # Shared utilities (DRY principle)
│   ├── __init__.py
│   └── timezone_utils.py     # Asia/Jakarta timezone handling
├── services/                 # Business logic layer
│   ├── __init__.py
│   ├── compliance_rules/     # Individual rule implementations (SRP)
│   │   ├── __init__.py
│   │   ├── base_rule.py      # Rule interface (DIP)
│   │   ├── rule_empty_assignees.py
│   │   ├── rule_empty_dates.py
│   │   ├── rule_missing_approval.py
│   │   └── rule_overdue_warning.py
│   └── report_generator.py      # Terminal JSON formatting
└── cli/                     # Optional test orchestrator
    └── orchestrator.py
```

### Timezone Handling (Asia/Jakarta UTC+7)

```python
# src/utils/timezone_utils.py - Extracted for maintainability
from zoneinfo import ZoneInfo
from datetime import datetime
from typing import Optional

def to_jakarta_timezone(iso_string: str) -> Optional[datetime]:
    """Convert ISO 8601 string to Asia/Jakarta timezone

    Args:
        iso_string: ISO 8601 formatted date string

    Returns:
        datetime object in Asia/Jakarta timezone or None if invalid

    Example:
        >>> to_jakarta_timezone("2025-09-24T12:00:00Z")
        datetime(2025, 9, 24, 19, 0, tzinfo=ZoneInfo('Asia/Jakarta'))
    """
    try:
        if not iso_string:
            return None
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.astimezone(ZoneInfo('Asia/Jakarta'))
    except (ValueError, TypeError):
        return None

def calculate_days_difference(start_date: datetime, end_date: datetime) -> int:
    """Calculate calendar days difference in Jakarta timezone

    Args:
        start_date: Start date in Jakarta timezone
        end_date: End date in Jakarta timezone

    Returns:
        Number of calendar days between dates
    """
    return (end_date.date() - start_date.date()).days

def is_within_days(target_date: datetime, reference_date: datetime, days: int) -> bool:
    """Check if target_date is within specified days of reference_date"""
    return abs(calculate_days_difference(reference_date, target_date)) <= days
```

### SOLID Compliance Rule Architecture

```python
# src/services/compliance_rules/base_rule.py - Interface Segregation + Dependency Inversion
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ViolationResult:
    """Standardized violation result structure"""
    rule_number: int
    rule_name: str
    description: str
    severity: str  # 'high', 'medium', 'low'
    violated: bool
    details: Optional[Dict[str, Any]] = None

class ComplianceRule(ABC):
    """Base interface for all compliance rules (ISP principle)"""

    @property
    @abstractmethod
    def rule_number(self) -> int:
        """Unique rule identifier (1-7)"""
        pass

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Human-readable rule name"""
        pass

    @property
    @abstractmethod
    def severity(self) -> str:
        """Rule violation severity level"""
        pass

    @abstractmethod
    def evaluate(self, issue: Dict[str, Any], comments: List[Dict[str, Any]]) -> ViolationResult:
        """Evaluate rule against issue and comments

        Args:
            issue: GitHub issue object with content and field_values
            comments: List of issue comments

        Returns:
            ViolationResult indicating compliance status
        """
        pass

# src/services/compliance_rules/rule_empty_assignees.py - Single Responsibility
from .base_rule import ComplianceRule, ViolationResult

class EmptyAssigneesRule(ComplianceRule):
    """Rule 1: Check for empty assignees field"""

    @property
    def rule_number(self) -> int:
        return 1

    @property
    def rule_name(self) -> str:
        return "Empty assignees field"

    @property
    def severity(self) -> str:
        return "high"

    def evaluate(self, issue: Dict[str, Any], comments: List[Dict[str, Any]]) -> ViolationResult:
        """Check if issue has assignees in content.assignees array"""
        assignees = issue.get('content', {}).get('assignees', [])
        violated = not assignees or len(assignees) == 0

        return ViolationResult(
            rule_number=self.rule_number,
            rule_name=self.rule_name,
            description=self.rule_name,
            severity=self.severity,
            violated=violated,
            details={'assignees_count': len(assignees) if assignees else 0}
        )

# Additional rule implementations follow same pattern...
# Rules 2-6: empty_dates, missing_approval, overdue_warning, etc.
```

### Compliance Evaluator (Open/Closed Principle)

```python
# src/services/compliance_evaluator.py - Rule registry for extensibility
from typing import Dict, List, Any
from .compliance_rules import (
    EmptyAssigneesRule, EmptyDatesRule, MissingApprovalRule,
    OverdueWarningRule, NoRecentUpdatesRule
)
from ..utils.timezone_utils import to_jakarta_timezone
from ..utils.bot_detection import filter_human_comments

class ComplianceEvaluator:
    """Orchestrates compliance rule evaluation (OCP compliant)"""

    def __init__(self):
        # Rule registry - easily extensible for new rules
        self.rules = [
            EmptyAssigneesRule(),
            EmptyDatesRule(),
            MissingApprovalRule(),
            OverdueWarningRule()
            # 6 rules total - no comment-based rules
        ]

    def evaluate_issue_compliance(
        self,
        issue: Dict[str, Any]
    ) -> List[ViolationResult]:
        """Evaluate single issue against all registered rules

        Args:
            issue: GitHub issue object

        Returns:
            List of violation results from all rules
        """
        violations = []
        for rule in self.rules:
            try:
                result = rule.evaluate(issue)
                violations.append(result)
            except Exception as e:
                # Graceful degradation - log error but continue
                violations.append(ViolationResult(
                    rule_number=rule.rule_number,
                    rule_name=rule.rule_name,
                    description=f"Rule evaluation failed: {str(e)}",
                    severity="medium",
                    violated=False,
                    details={'error': str(e)}
                ))

        return violations

    def add_rule(self, rule: ComplianceRule) -> None:
        """Add new compliance rule (OCP - open for extension)"""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.rule_number)
```

### Error Handling and Rate Limiting

```python
# Exponential backoff for MCP calls
import time
import random

def exponential_backoff_retry(func, max_retries=3, base_delay=2):
    """Execute function with exponential backoff retry logic"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            time.sleep(min(delay, 60))  # Cap at 60 seconds

# Rate limit handling
class RateLimitHandler:
    def __init__(self, requests_per_minute=60):
        self.requests_per_minute = requests_per_minute
        self.last_request_time = 0

    def wait_if_needed(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 60.0 / self.requests_per_minute

        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)

        self.last_request_time = time.time()
```

### Field Value Extraction

```python
def extract_field_value(field_values: List[Dict], field_name: str) -> Optional[Any]:
    """Extract value from GitHub Project field_values array"""
    if not field_values:
        return None

    for field in field_values:
        if field.get('name') == field_name:  # Case-sensitive exact match
            return field.get('value')
    return None

# Required field mappings for compliance rules
FIELD_MAPPINGS = {
    'status': 'Status',
    'incoming_date': 'Incoming Date',
    'due_date': 'Due Date',
    'pak_on_approval': "Pak On's Approval for Timeline"
}
```

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

**Code Quality Excellence**:

- [x] All tool implementations will include type annotations and comprehensive docstrings
- [x] Defensive programming with explicit error handling planned
- [x] Lint checks (black, flake8, mypy) and 80% code coverage targets set

**Test-First Development (NON-NEGOTIABLE)**:

- [x] TDD workflow confirmed: Tests → Validation → Fail → Implement
- [x] Unit tests for all public methods planned
- [x] Integration tests for external API calls planned
- [x] Mocking strategy for external dependencies defined

**Prompt Engineering Best Practices**:

- [x] Tool descriptions are clear and specify exact input/output formats
- [x] Error messages will be actionable and context-aware
- [x] Prompt templates will be versioned and token-optimized

**Performance Requirements**:

- [x] Agent timeout limits (720 seconds) and retry logic planned
- [x] Memory usage limits (100MB per execution) considered
- [x] Agent completion targets (95% within timeout) defined
- [x] LLM efficiency optimization strategy planned

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)

```
# Background Agent Structure
src/
├── services/         # Self-contained GLLM Plugin tools
│   ├── compliance_evaluator.py  # All rules + inline utilities
│   └── report_generator.py      # Terminal JSON formatting
└── cli/             # Optional test orchestrator

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: [DEFAULT to Option 1 unless Technical Context indicates web/mobile app]

## Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:

   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:

   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts

_Prerequisites: research.md complete_

1. **Extract entities from feature spec** → `data-model.md`:

   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:

   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:

   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:

   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh copilot`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/\*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach

_This section describes what the /tasks command will do - DO NOT execute during /plan_

**Task Generation Strategy**:

- Load `.specify/templates/tasks-template.md` as base
- Generate 17 specific implementation tasks from Phase 1 design docs
- Follow TDD approach: tests before implementation
- Mark [P] for parallel execution (independent tasks)

**Concrete Task Sequence (v1.0 PoC)**:

### Phase 1: Foundation (3 tasks)

1. **[P] Project Structure Setup** - Create src/services/, tests/ for self-contained tools
2. **[P] Test Fixtures Creation** - 15-issue MCP JSON responses (5 per status)
3. **[P] Development Environment** - pytest config, GLLM Plugin setup

### Phase 2: Core Implementation (3 tasks)

4. **Compliance Evaluator Tool** - Single file with inline utilities, all 7 rules
5. **Report Generator Tool** - Terminal JSON output formatting only
6. **[P] Comprehensive Unit Tests** - Rule evaluation, edge cases, 15-issue dataset

### Phase 3: Integration (3 tasks)

7. **Background Agent Orchestration** - MCP calls → tool processing → terminal output
8. **Error Handling** - Inline retry logic, graceful failures
9. **End-to-End Integration Tests** - 15-issue workflow validation

### Phase 4: Deployment (2 tasks)

10. **Platform Configuration** - Background agent deployment
11. **Production Validation** - Live testing with 15-issue samples

**Ordering Strategy**:

- Critical path: Tasks 7, 11, 13 (core compliance logic)
- Parallel execution: Tasks 1-2-3, 5-6, 8-9-10
- Dependencies: 11 depends on 7, 13 depends on 11, 14 depends on 13

**Test Coverage Requirements**:

- Unit tests for each of 7 compliance rules (positive/negative cases)
- Timezone edge cases (midnight boundaries, DST transitions)
- Bot filtering patterns (various bot username formats)
- MCP response parsing (malformed data handling)
- Error recovery scenarios (rate limits, timeouts, network failures)

**Performance Benchmarks**:

- Agent workflow: 15 issues in <2 minutes (target: <90 seconds)
- Memory usage: <50MB total (target: <30MB)
- MCP calls: ~3-9 total (pagination dependent)
- Background execution: Single run, no interaction

**Estimated Output**: 11 streamlined tasks for background agent implementation

## Platform Config

Copy-ready configuration block for the Agentic AI Platform agent creation form:

```yaml
Version: 1.0.0 (PoC - Read-Only)
Agent ID: github_issue_compliance_agent_v1
Display Name: GitHub Issue Compliance Background Agent (PoC)
Description: Background agent that audits a GitHub Project for 7 compliance rules and generates read-only reports
Model: Claude Sonnet 4
Tools:
  - MCP: github_projects_v2 (read-only: lists with pagination)
    Direct agent access to MCP connector functions:
      - github_list_project_items(organization, project_number, status_filters, page)

  - GLLM Python Plugin Tools (modular SOLID-compliant architecture):
      - github_merge_tool(paginated_list_results) [combines paginated responses]
      - github_compliance_evaluator_tool(merged_issues) [evaluates 6 rules]
      - github_report_generator_tool(evaluation_results) [terminal JSON output]
Timeout (seconds): 720
Chat History Limit: 20
System Instructions: |
  You are a GitHub Project compliance monitoring background agent (v1.0 PoC - Read-Only). Your role is to:
  1. Check GitHub Project issues for compliance with 6 defined rules
  2. Generate summary reports of violations
  3. Respond to queries about compliance status
  4. Export reports to various formats (JSON/CSV/Markdown)

  IMPORTANT: v1.0 CONSTRAINTS:
  - READ-ONLY access only - never modify issues or post comments
  - On-demand execution only - no automated scheduling
  - Single-agent architecture - direct MCP calls + GLLM Plugin tools

  OPERATIONAL POLICY:
  - Use Asia/Jakarta (UTC+7) timezone for all date calculations
  - Handle pagination automatically when has_next=true in MCP responses
  - Provide actionable violation descriptions in reports
  - Support interactive queries about specific violations

  COMPLIANCE RULES:
  1. Empty assignees field (content.assignees array)
  2. Empty incoming date field (field_values["Incoming Date"])
  3. Empty due date field (field_values["Due Date"])
  4. Empty status field (field_values["Status"])
  5. Empty "Pak On's Approval for Timeline" field AND more than 7 days from incoming date
  6. Will be due in next 7 days (warning)

  GUARDRAILS:
  - Never modify issue statuses or field values
  - Never post comments or make any write operations
  - Respect rate limits with exponential backoff
  - Log all actions for audit purposes
```

## Terminal Output Schema

### JSON Report (Terminal Output Only)

```json
{
  "execution_time": "87 seconds",
  "generated_at": "2025-09-24T08:00:00+07:00",
  "project": "GDP-ADMIN/223",
  "issues_sampled": 15,
  "issues_by_status": {
    "In Progress": 5,
    "In Review": 5,
    "Todo": 5
  },
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
    "rule_6_due_soon_warning": 4
  },
  "violation_details": [
    {
      "issue_number": 534,
      "title": "Web Search Contract",
      "url": "https://github.com/GDP-ADMIN/dummy-gl-sdk/issues/534",
      "status": "In Progress",
      "assignees": [],
      "violated_rules": [1, 5],
      "rule_descriptions": [
        "Empty assignees field",
        "Missing Pak On's approval (overdue by 12 days)"
      ],
      "severity": "high"
    }
  ],
  "execution_status": "completed",
  "next_action": "Review high-priority violations above"
}
```

### Error Response Schema

```json
{
  "execution_time": "45 seconds",
  "generated_at": "2025-09-24T08:00:00+07:00",
  "project": "GDP-ADMIN/223",
  "execution_status": "partial_failure",
  "errors": [
    {
      "type": "mcp_timeout",
      "message": "Failed to fetch comments for issue #534 after 3 retries",
      "affected_issues": [534],
      "severity": "medium"
    }
  ],
  "issues_sampled": 12,
  "issues_failed": 3,
  "partial_results": {
    "compliance_summary": {
      "compliant_issues": 5,
      "violating_issues": 7,
      "compliance_rate": 0.417,
      "data_completeness": 0.8
    }
  },
  "next_action": "Retry failed issues or proceed with partial results"
}
```

## Multi-Agent Option (v2.0 Future Phase)

### Architecture Overview

**v1.0 Implementation**: Single agent with direct MCP calls + GLLM Plugin tools (current scope)

**v2.0 Upgrade Path**: The single-agent v1 design can be upgraded to 4 specialized agents with clean JSON contracts:

**Agent Roles**:

- **Fetcher**: MCP read operations (list_project_items, get_issue_comments)
- **Auditor**: Rule evaluation (R1-R7) - reuses v1 GLLM Plugin tools
- **Reporter**: File/console/chat output generation (extends v1 capabilities)
- **Notifier**: MCP write operations (NEW - comment posting)
- **Orchestrator**: Workflow coordination and user interaction

### Message Contracts (JSON Schemas) - v2.0

#### ReportRequest

```json
{
  "project_id": "string",
  "output_format": "json|markdown|csv|all",
  "rule_filter": ["R1", "R2"], // Optional
  "severity_filter": "high|medium|low" // Optional
}
```

#### IssuesEnvelope

```json
{
  "project_id": "string",
  "issues": ["GitHubIssue"],
  "fetched_at": "datetime",
  "total_count": "int"
}
```

#### ViolationFacts

```json
{
  "issue_id": "string",
  "violated_rules": ["int"],
  "rule_details": { "int": "string" },
  "severity": "high|medium|low",
  "evaluated_at": "datetime"
}
```

#### CommentRequest (v2.0 NEW)

```json
{
  "issue_id": "string",
  "violations": ["int"],
  "assignees": ["string"],
  "idempotency_key": "string",
  "dry_run": "bool"
}
```

#### ReportSummary

```json
{
  "project_id": "string",
  "total_issues": "int",
  "violations_by_rule": { "int": "int" },
  "compliance_rate": "float",
  "generated_at": "datetime"
}
```

### Permission Boundaries - v2.0

- **Fetcher**: `project:read` scope only
- **Auditor**: No GitHub access (pure computation) - reuses v1 tools
- **Reporter**: File system write for artifacts only
- **Notifier**: `write:issue_comment` scope (NEW in v2)
- **Orchestrator**: No direct GitHub access

### Upgrade Strategy

1. **v1.0**: Single agent → GLLM Plugin tools → reports (current implementation)
2. **v2.0**: Split into Fetcher → Auditor (reuse v1 tools) → Reporter → Notifier pipeline
3. **v2.1**: Add scheduled execution and advanced notification features
4. No changes to core compliance evaluation logic required

## Phase 3+: Future Implementation

_These phases are beyond the scope of the /plan command_

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking

_Fill ONLY if Constitution Check has violations that must be justified_

| Violation                  | Why Needed         | Simpler Alternative Rejected Because |
| -------------------------- | ------------------ | ------------------------------------ |
| [e.g., 4th project]        | [current need]     | [why 3 projects insufficient]        |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient]  |

## Progress Tracking

_This checklist is updated during execution flow_

**Phase Status**:

- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:

- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (None required)

---

_Based on de-github Agent Tools Constitution v1.0.0 - See `.specify/memory/constitution.md`_
