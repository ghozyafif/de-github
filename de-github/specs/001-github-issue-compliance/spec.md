# Feature Specification: GitHub Issue Compliance Agent

**Feature Branch**: `001-github-issue-compliance`  
**Created**: 2025-09-24  
**Status**: Ready for Planning  
**Version**: v1.0 (PoC - Read-Only) → v2.0 (Full - Write Capabilities)  
**Input**: User description: "GitHub Issue Compliance Agent - automated agent that can continuously check issue quality and remind responsible parties"

## Execution Flow (main)

```
1. Parse user description from Input
   → ✅ Feature description provided
2. Extract key concepts from description
   → ✅ Identified: actors (PM, Engineers, Compliance), actions (check, analyze, report, comment), data (GitHub issues), constraints (MCP integration, no direct edits)
3. For each unclear aspect:
   → ✅ Marked ambiguities with [NEEDS CLARIFICATION]
4. Fill User Scenarios & Testing section
   → ✅ Clear user flows identified
5. Generate Functional Requirements
   → ✅ Each requirement is testable
6. Identify Key Entities (if data involved)
   → ✅ Key entities identified
7. Run Review Checklist
   → ✅ No implementation details, focused on business value
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines

- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-09-24

- Q: What are the 7 compliance rules the agent should check? → A: 1. Empty assignees field, 2. Empty incoming date field, 3. Empty due date field, 4. Empty status field, 5. Empty "Pak On's Approval for Timeline" field and more than 7 days from the incoming date field, 6. Will be due in the next 7 days, 7. Has not had any updates based on issue comments for the last 7 days
- Q: What are the exact field names in the GitHub Project data structure? → A: assignees (from content), "Status", "Incoming Date", "Due Date", "Pak On's Approval for Timeline" (all from field_values array with exact case-sensitive names)
- Q: What are the exact status values that map to your three target states? → A: Exact match: "In Progress", "In Review", "Todo"
- Q: What timezone should be used for all date comparisons and "7 days" calculations? → A: Asia/Jakarta (UTC+7) for all date operations
- Q: What counts as a valid "update" to reset the 7-day timer for rule #7? → A: Any human comment (exclude bot/system comments)

## User Scenarios & Testing

### Primary User Story

**v1.0 PoC**: Project Managers and Engineers need automated monitoring of GitHub Project issue quality to ensure proper tracking and compliance. The agent runs as a background process, checks a sample of issues (5 per status) against defined compliance rules, and outputs a comprehensive JSON report to the terminal.

**v2.0 Full**: Building on v1, the system additionally posts automated violation comments to GitHub issues, tagging assignees directly for immediate notification and action.

### Acceptance Scenarios

#### v1.0 PoC Scenarios (Current Implementation)

1. **Given** a GitHub Project with issues in "In Progress", "In Review", and "Todo" statuses, **When** the background agent runs using Asia/Jakarta timezone, **Then** it checks 5 issues per status (15 total) and outputs a JSON report to terminal showing violations per rule
2. **Given** an issue that violates multiple compliance rules, **When** the agent processes violations, **Then** the terminal JSON output includes all violations with detailed descriptions and severity levels
3. **Given** an issue with no compliance violations, **When** the agent checks it, **Then** the issue appears in the compliant_issues section of the terminal output
4. **Given** a completed agent run, **When** the terminal output is displayed, **Then** it includes comprehensive violation details for all 15 sampled issues and exits

#### v2.0 Future Scenarios (NOT in current scope)

5. *[FUTURE]* **Given** violations are detected, **When** v2.0 is implemented, **Then** the agent will post comments to GitHub issues
6. *[FUTURE]* **Given** scheduled execution, **When** v2.0 is implemented, **Then** daily automated checks will run

### Edge Cases

- What happens when an issue has multiple assignees in content.assignees array (should mention all or just primary contact)?
- How does the system handle issues missing both "Incoming Date" and "Due Date" field_values?
- What occurs when "Pak On's Approval for Timeline" field is empty but issue is only 6 days old from incoming date in Asia/Jakarta timezone?
- How are issues handled where all comments are bot/system-generated with no human comments?
- What happens if closed issues are accidentally included in the query results?

## Requirements

### Functional Requirements

#### v1.0 PoC Requirements (Read-Only)

- **FR-001**: System MUST connect to a specific GitHub Project via MCP integration to access issue data
- **FR-002**: System MUST retrieve issues with status exactly matching "In Progress", "In Review", or "Todo" from the connected GitHub Project field_values["Status"]
- **FR-003**: System MUST analyze each retrieved issue against exactly 7 defined compliance rules using Asia/Jakarta (UTC+7) timezone for all date calculations: (1) Empty assignees field, (2) Empty incoming date field, (3) Empty due date field, (4) Empty status field, (5) Empty "Pak On's Approval for Timeline" field when more than 7 days from incoming date, (6) Will be due in next 7 days, (7) No human comments (excluding bot/system comments) for last 7 days
- **FR-004**: System MUST output a terminal-based JSON report showing violation counts for each of the 7 compliance rules
- **FR-005**: System MUST provide complete violation details in a single terminal output (background mode, no follow-up queries)
- **FR-009**: System MUST never modify issue statuses, field values, or metadata - only read access allowed (v1 constraint)
- **FR-010**: System MUST check issues on-demand and generate compliance reports with violation summaries
- **FR-011**: System MUST differentiate between violation severity levels with overdue items prioritized higher than missing metadata
- **FR-012**: System MUST provide comprehensive violation details in terminal JSON output (no file storage)

#### v2.0 Full Requirements (Write Capabilities) - Future Phase

- **FR-013**: System SHOULD post consolidated violation comments to GitHub issues tagging assignees (v2 feature)
- **FR-014**: System SHOULD use idempotency keys to prevent duplicate comments per issue (v2 feature)
- **FR-015**: System SHOULD implement daily scheduled execution with automated notifications (v2 feature)
- **FR-016**: System SHOULD support comment throttling (max 1 per issue per 24 hours) (v2 feature)

### Key Entities

- **GitHub Issue**: Represents a project task with fields including status (from field_values["Status"]), assignee (from content.assignees array), timeline dates (field_values["Incoming Date"], field_values["Due Date"]), approval fields (field_values["Pak On's Approval for Timeline"]), comments, and metadata required for compliance checking
- **Compliance Rule**: Represents one of 7 defined rules that issues must follow, with rule name, description, and violation detection logic
- **Violation Report**: Terminal JSON output containing violation counts per rule, issue details, and compliance metrics for 15 sampled issues

---

## Review & Acceptance Checklist

### Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities resolved
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---
