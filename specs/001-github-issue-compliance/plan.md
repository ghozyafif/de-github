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

**v1.0 PoC (Background Agent Read-Only)**: Automated GitHub Project compliance agent that runs in background mode, checks 15 sampled issues (5 per status) against 7 defined rules, and outputs a comprehensive JSON report to terminal. Uses company Agentic AI platform with Claude Sonnet 4, MCP integration for GitHub Projects v2, and self-contained Python GLLM Plugin tools (no imports, all utilities inline). **No file storage or write operations** - terminal output only.

**v2.0 Full (Write-Capable)**: [FUTURE] Extends v1 with automated comment posting and scheduled execution capabilities.

## Technical Context

**Language/Version**: Python 3.11+ (GLLM Plugin), Claude Sonnet 4 (Orchestrator)
**Primary Dependencies**: GLLM Plugin Framework, BOSA MCP GitHub connector, Claude Sonnet 4 model
**Storage**: No storage - terminal JSON output only
**MCP Provider**: BOSA (https://api.bosa.id/github/mcp)  
**Testing**: pytest with fixtures for rule evaluation, MCP mock integration tests  
**Target Platform**: Company Agentic AI Platform (cloud-hosted)
**Project Type**: single - agent tools with orchestrator pattern  
**Performance Goals**: Process 15 sampled issues (5 per status), complete agent workflow within 2 minutes, optimize for minimal MCP calls
**Constraints**: <720s total agent timeout, <100MB memory per execution, Asia/Jakarta timezone, exponential backoff rate limiting  
**Scale/Scope**: Single GitHub Project monitoring, 7 compliance rules, on-demand execution (v1.0 PoC)

## Technical Implementation Details

### Timezone Handling (Asia/Jakarta UTC+7)

```python
# Using zoneinfo (Python 3.9+) or pytz fallback
from zoneinfo import ZoneInfo
from datetime import datetime

def to_jakarta_timezone(iso_string: str) -> datetime:
    """Convert ISO 8601 string to Asia/Jakarta timezone"""
    dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    return dt.astimezone(ZoneInfo('Asia/Jakarta'))

def calculate_days_difference(start_date: datetime, end_date: datetime) -> int:
    """Calculate calendar days difference in Jakarta timezone"""
    return (end_date.date() - start_date.date()).days
```

### Bot Comment Filtering (Rule #7)

```python
# Bot detection patterns
BOT_PATTERNS = [
    r'.*\[bot\]$',  # GitHub bots ending with [bot]
    r'^(github-actions|dependabot|renovate|codecov)\[bot\]$',  # Common bots
    r'^(Automatically (closed|merged)|This (issue|PR) has been)',  # System messages
]

def is_bot_comment(username: str, body: str) -> bool:
    """Detect if comment is from bot/system"""
    import re
    # Check username patterns
    for pattern in BOT_PATTERNS:
        if re.match(pattern, username, re.IGNORECASE):
            return True
    # Check for emoji-only comments
    if re.match(r'^[\s\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+$', body):
        return True
    return False
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
- MCP calls: ~45 total (3 lists + 15 details + 15 comments)
- Background execution: Single run, no interaction

**Estimated Output**: 11 streamlined tasks for background agent implementation

## Platform Config

Copy-ready configuration block for the Agentic AI Platform agent creation form:

```yaml
Version: 1.0.0 (PoC - Read-Only)
Agent ID: github_issue_compliance_agent_v1
Display Name: GitHub Issue Compliance Agent (PoC)
Description: Agent that audits a GitHub Project for 7 compliance rules and generates read-only reports
Model: Claude Sonnet 4
Tools:
  - MCP: github_projects_v2 (read-only: lists, details, comments)
    Direct agent access to MCP connector functions:
      - github_list_project_items(organization, project_number, status_filters)
      - github_get_issue_handler(owner, repo, issue_number)
      - github_list_issues_comments(owner, repo, issue_number)

  - GLLM Python Plugin Tools (self-contained, no imports):
      - github_merge_tool(mcp_list_payload_results) [existing]
      - github_formatter_tool(issues, project_number) [existing]
      - github_compliance_evaluator_tool(issues, comments_by_issue)
      - github_report_generator_tool(evaluation_results)
Timeout (seconds): 720
Chat History Limit: 20
System Instructions: |
  You are a GitHub Project compliance monitoring agent (v1.0 PoC - Read-Only). Your role is to:
  1. Check GitHub Project issues for compliance with 7 defined rules
  2. Generate summary reports of violations
  3. Respond to queries about compliance status
  4. Export reports to various formats (JSON/CSV/Markdown)

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
    "rule_6_due_soon_warning": 4,
    "rule_7_no_recent_updates": 2
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
