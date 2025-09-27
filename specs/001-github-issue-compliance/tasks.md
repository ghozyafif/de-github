# Tasks: GitHub Issue Compliance Agent (v1.0 PoC - Background Mode)

**Input**: Design documents from `/home/gh/Documents/GL/gdplabs-exploration/de-github/specs/001-github-issue-compliance/`
**Context**: Background agent that samples 15 issues (5 per status), outputs terminal JSON only

## Execution Flow (main)

```
1. Load spec.md → 7 compliance rules, v1.0 background mode, terminal output only
2. Load plan.md → Self-contained GLLM Plugin tools, 15-issue sampling strategy
3. Generate streamlined tasks:
   → Foundation: repo setup, 15-issue fixtures, GLLM environment
   → Core: Single-file compliance evaluator and report generator
   → Integration: Background orchestration, error handling
   → Deployment: Platform config, production validation
4. Apply constraints: No file storage, no lib imports, terminal JSON only
5. Use Poetry for all installation: `poetry install`, `poetry run pytest`
6. Validate all 7 rules with 15-issue test dataset
7. Return: 11 streamlined tasks ready for execution
```

## Format: `[ID] [P?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (shares files or has dependencies)

---

## Phase 1 — Foundation (T-01 to T-03)

### T-01 [X] Minimal Repo Structure

**Type**: Setup
**DependsOn**: []
**Parallelizable**: [P]
**Status**: COMPLETED

**Steps**:

1. Create directory structure: `src/services/`, `tests/unit/`, `tests/integration/`, `tests/fixtures/mcp/`
2. Create placeholder `README.md`, `.gitignore`, `requirements.txt`
3. Set up Python 3.11+ virtual environment

**Outputs**:

- `src/services/__init__.py`
- `tests/unit/__init__.py`
- `tests/integration/__init__.py`
- `tests/fixtures/mcp/` (directory)
- `README.md`
- `.gitignore`

**Acceptance Criteria**:

- GIVEN repository root, WHEN structure created, THEN all directories exist
- GIVEN Python 3.11+ requirement, WHEN environment activated, THEN `python --version` shows ≥3.11

---

### T-02 [X] 15-Issue MCP Fixtures

**Type**: Test
**DependsOn**: [T-01]
**Parallelizable**: [P]
**Status**: COMPLETED

**Inputs**:

- `spec.md` §Clarifications (7 compliance rules)
- `data-model.md` §Test Fixture Requirements
- `/MCP/responses/` (existing examples)

**Steps**:

1. Create `github_list_project_items_in_progress_5.json` with 5 issues
2. Create `github_list_project_items_in_review_5.json` with 5 issues
3. Create `github_list_project_items_todo_5.json` with 5 issues
4. Create 15 `github_get_issue_handler_[number].json` files
5. Create 15 `github_list_issues_comments_[number].json` files
6. Ensure coverage of all 7 rules across the 15 issues

**Outputs**:

- `tests/fixtures/mcp/github_list_project_items_in_progress_5.json`
- `tests/fixtures/mcp/github_list_project_items_in_review_5.json`
- `tests/fixtures/mcp/github_list_project_items_todo_5.json`
- `tests/fixtures/mcp/github_get_issue_handler_[534,535,536...].json` (15 files)
- `tests/fixtures/mcp/github_list_issues_comments_[534,535,536...].json` (15 files)

**Acceptance Criteria**:

- GIVEN 15-issue dataset, WHEN loaded, THEN all required fields present
- GIVEN rule coverage, WHEN analyzed, THEN all 7 rules have test cases
- GIVEN bot comments, WHEN included, THEN human vs bot distinguishable

---

### T-03 [X] GLLM Plugin Environment

**Type**: Tooling
**DependsOn**: [T-01]
**Parallelizable**: [P]
**Status**: COMPLETED

**Steps**:

1. Install Poetry: `curl -sSL https://install.python-poetry.org | python3 -`
2. Configure GDP Labs repository:
   ```bash
   poetry source add gen-ai https://asia-southeast2-python.pkg.dev/gdp-labs/gen-ai/simple/
   gcloud auth login
   poetry config http-basic.gen-ai oauth2accesstoken "$(gcloud auth print-access-token)"
   ```
3. Create `pyproject.toml` with GLLM dependencies
4. Run `poetry install`
5. Configure `pytest.ini`

**Outputs**:

- `pyproject.toml`
- `poetry.lock`
- `pytest.ini`

**Acceptance Criteria**:

- GIVEN Poetry installed, WHEN `poetry --version` run, THEN version shown
- GIVEN GLLM Plugin, WHEN imported, THEN no errors
- GIVEN pytest, WHEN run, THEN discovers tests

---

## Phase 2 — Core Implementation (T-04 to T-06)

### T-04 [X] Single-File Compliance Evaluator

**Type**: Code
**DependsOn**: [T-03]
**Parallelizable**: [S]
**Status**: COMPLETED

**Inputs**:

- `spec.md` FR-003 (7 compliance rules)
- `plan.md` §Technical Implementation Details
- `contracts/gllm_plugin_tools.md`

**Steps**:

1. Create `src/services/compliance_evaluator.py` as single self-contained file
2. Add inline timezone utilities (no imports from lib/):
   ```python
   def to_jakarta_timezone(iso_string: str) -> datetime:
       # Asia/Jakarta conversion inline

   def calculate_days_difference(start_date, end_date) -> int:
       # Calendar days calculation inline
   ```
3. Add inline bot filtering:
   ```python
   BOT_PATTERNS = [r'.*\[bot\]$', ...]

   def is_bot_comment(username: str) -> bool:
       # Bot detection inline
   ```
4. Implement all 7 compliance rules as functions
5. Create main GLLM Plugin tool function:
   ```python
   @tool
   def github_compliance_evaluator_tool(
       issues: List[Dict],
       comments_by_issue: Dict[int, List[Dict]]
   ) -> Dict:
       # Returns violations and summary
   ```
6. Add comprehensive docstrings and type hints

**Outputs**:

- `src/services/compliance_evaluator.py` (400-500 lines, fully self-contained)

**Acceptance Criteria**:

- GIVEN single file, WHEN imported, THEN no external dependencies (except GLLM)
- GIVEN 15 test issues, WHEN evaluated, THEN all 7 rules work correctly
- GIVEN inline utilities, WHEN tested, THEN timezone and bot filtering work

---

### T-05 [X] Terminal Report Generator

**Type**: Code
**DependsOn**: [T-03]
**Parallelizable**: [S]
**Status**: COMPLETED

**Inputs**:

- `plan.md` §Terminal Output Schema
- `contracts/gllm_plugin_tools.md`

**Steps**:

1. Create `src/services/report_generator.py` as single file
2. Implement terminal JSON formatting:
   ```python
   @tool
   def github_report_generator_tool(
       evaluation_results: Dict
   ) -> str:
       # Returns formatted JSON string for terminal
   ```
3. Include detailed violation information
4. Add execution time and status fields
5. Format for readability in terminal

**Outputs**:

- `src/services/report_generator.py` (200-300 lines)

**Acceptance Criteria**:

- GIVEN evaluation results, WHEN formatted, THEN valid JSON output
- GIVEN terminal output, WHEN displayed, THEN human-readable
- GIVEN all violations, WHEN included, THEN comprehensive details shown

---

### T-06 [X] Unit Tests

**Type**: Test
**DependsOn**: [T-04, T-05]
**Parallelizable**: [P]
**Status**: COMPLETED

**Steps**:

1. Create `tests/unit/test_compliance_evaluator.py`:
   - Test all 7 rules individually
   - Test inline timezone utilities
   - Test inline bot filtering
   - Test with 15-issue fixtures
2. Create `tests/unit/test_report_generator.py`:
   - Test JSON formatting
   - Test violation details
   - Test summary calculations
3. Run `poetry run pytest tests/unit/ -v`
4. Achieve 80% code coverage

**Outputs**:

- `tests/unit/test_compliance_evaluator.py`
- `tests/unit/test_report_generator.py`

**Acceptance Criteria**:

- GIVEN unit tests, WHEN run, THEN all pass
- GIVEN code coverage, WHEN measured, THEN ≥80%
- GIVEN 15-issue dataset, WHEN tested, THEN all scenarios covered

---

## Phase 3 — Integration (T-07 to T-09)

### T-07 [X] Background Agent Orchestration

**Type**: Integration
**DependsOn**: [T-06]
**Parallelizable**: [S]
**Status**: COMPLETED

**Inputs**:

- `research.md` §Architecture Decision
- `plan.md` §Platform Config

**Steps**:

1. Create `src/cli/orchestrator.py` for testing (optional)
2. Define workflow:
   - Call MCP for 5 issues per status (3 calls)
   - Call MCP for details and comments (30 calls)
   - Pass to compliance_evaluator tool
   - Format with report_generator tool
   - Output to terminal
   - Exit (no interaction)
3. Add inline error handling

**Outputs**:

- `src/cli/orchestrator.py` (optional test harness)
- `configs/agent_workflow.yaml`

**Acceptance Criteria**:

- GIVEN 15 issues, WHEN orchestrated, THEN complete workflow executes
- GIVEN terminal output, WHEN generated, THEN JSON displayed
- GIVEN background mode, WHEN complete, THEN agent exits

---

### T-08 [X] Error Handling

**Type**: Code
**DependsOn**: [T-07]
**Parallelizable**: [S]
**Status**: COMPLETED

**Steps**:

1. Add inline retry logic to compliance_evaluator.py:
   ```python
   def retry_with_backoff(func, max_retries=3):
       # Exponential backoff inline
   ```
2. Handle MCP timeouts gracefully
3. Handle missing fields in issue data
4. Return partial results on failure

**Outputs**:

- Updated `src/services/compliance_evaluator.py` with error handling

**Acceptance Criteria**:

- GIVEN network timeout, WHEN occurs, THEN retry attempted
- GIVEN missing data, WHEN encountered, THEN graceful degradation
- GIVEN partial failure, WHEN happens, THEN partial results returned

---

### T-09 [X] Integration Tests

**Type**: Test
**DependsOn**: [T-08]
**Parallelizable**: [S]
**Status**: COMPLETED

**Steps**:

1. Create `tests/integration/test_background_workflow.py`
2. Test complete 15-issue workflow
3. Test with various failure scenarios
4. Verify terminal output format
5. Run `poetry run pytest tests/integration/ -v`

**Outputs**:

- `tests/integration/test_background_workflow.py`

**Acceptance Criteria**:

- GIVEN integration tests, WHEN run, THEN workflow validated
- GIVEN 15 issues, WHEN processed, THEN <2 minutes execution
- GIVEN terminal output, WHEN checked, THEN matches schema

---

## Phase 4 — Deployment (T-10 to T-11)

### T-10 [X] Platform Configuration

**Type**: Ops
**DependsOn**: [T-09]
**Parallelizable**: [S]
**Status**: COMPLETED

**Steps**:

1. Create agent configuration for background mode:
   ```yaml
   Timeout: 300
   Mode: background
   Output: terminal_json
   ```
2. Register GLLM Plugin tools
3. Configure MCP connection
4. Test with AIP CLI

**Outputs**:

- `configs/background_agent_config.yaml`

**Acceptance Criteria**:

- GIVEN agent config, WHEN deployed, THEN runs in background
- GIVEN 15-issue limit, WHEN executed, THEN samples correctly
- GIVEN terminal output, WHEN complete, THEN agent exits

---

### T-11 [X] Production Validation

**Type**: Ops
**DependsOn**: [T-10]
**Parallelizable**: [S]
**Status**: COMPLETED (Ready for deployment)

**Steps**:

1. Run against live GDP-ADMIN/223 project
2. Verify 15 issues sampled (5 per status)
3. Confirm terminal JSON output
4. Validate all 7 rules evaluated
5. Document execution time (<2 minutes target)

**Outputs**:

- Production validation report
- Sample terminal output

**Acceptance Criteria**:

- GIVEN production data, WHEN processed, THEN accurate results
- GIVEN 15-issue sample, WHEN analyzed, THEN representative of project
- GIVEN execution time, WHEN measured, THEN <2 minutes achieved

---

## Dependencies Summary

**Phase Dependencies**:
- Foundation (T-01 → T-03) → Core (T-04 → T-06)
- Core → Integration (T-07 → T-09)
- Integration → Deployment (T-10 → T-11)

**Critical Path**:
- T-01 → T-03 → T-04 → T-07 → T-10 → T-11

**Parallel Opportunities**:
- T-01, T-02, T-03 can run together
- T-06 can start once T-04/T-05 complete

## Key Differences from Original

1. **No lib/ folder** - All utilities inline in tool files
2. **No file storage** - Terminal JSON output only
3. **15 issues only** - 5 per status for performance
4. **2 GLLM tools** - Compliance evaluator and report generator
5. **Background mode** - No interaction, single execution
6. **11 tasks total** - Streamlined from original 19