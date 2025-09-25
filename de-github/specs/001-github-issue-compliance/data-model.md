# Data Model: GitHub Issue Compliance Agent

## Core Entities

### GitHubIssue

Represents a GitHub Project issue with all fields required for compliance checking.

**Attributes**:

- `id: str` - GitHub Project item ID (PVTI\_\*)
- `type: str` - Always "ISSUE" for our scope
- `title: str` - Issue title
- `status: str` - From field_values["Status"]
- `assignees: List[str]` - From content.assignees array
- `incoming_date: Optional[datetime]` - From field_values["Incoming Date"]
- `due_date: Optional[datetime]` - From field_values["Due Date"]
- `pak_on_approval: Optional[str]` - From field_values["Pak On's Approval for Timeline"]
- `created_at: datetime` - Issue creation timestamp
- `updated_at: datetime` - Last modification timestamp
- `issue_number: int` - GitHub issue number
- `repository: str` - Repository name
- `url: str` - GitHub issue URL

**Validation Rules**:

- All dates converted to Asia/Jakarta timezone
- Status must be one of: "In Progress", "In Review", "Todo"
- Assignees array can be empty (triggers Rule #1)

### ComplianceRule

Represents one of the 7 compliance rules with evaluation logic.

**Attributes**:

- `rule_id: int` - Rule number (1-7)
- `name: str` - Rule display name
- `description: str` - Human-readable rule description
- `severity: str` - "high" for overdue, "medium" for missing metadata

**Rules Definition**:

1. **Empty Assignees** - `assignees` array is empty
2. **Empty Incoming Date** - `incoming_date` is null/missing
3. **Empty Due Date** - `due_date` is null/missing
4. **Empty Status** - `status` is null/empty/unrecognized
5. **Missing Pak On Approval (Overdue)** - `pak_on_approval` is empty AND `(today - incoming_date) > 7 days`
6. **Due Soon Warning** - `due_date` is within next 7 calendar days
7. **No Recent Updates** - No human comments in last 7 days

### ViolationReport

Represents the terminal JSON output with compliance violations for 15 sampled issues.

**Attributes**:

- `project_id: str` - GitHub Project identifier
- `execution_time: str` - Total execution time (e.g., "87 seconds")
- `check_timestamp: datetime` - When compliance check was performed
- `issues_sampled: int` - Number of issues analyzed (15)
- `issues_by_status: Dict[str, int]` - Count per status (5 each)
- `violations_by_rule: Dict[str, int]` - Count of violations per rule name
- `violation_details: List[Dict]` - Detailed violations with issue info
- `compliance_summary: Dict` - Compliant vs violating counts and rate

### Terminal Output

Represents the complete JSON output to terminal (no file storage).

**Format**: Single comprehensive JSON object printed to terminal

**Key Fields**:

- `execution_time` - Total runtime
- `project` - Project identifier
- `issues_sampled` - Always 15 (5 per status)
- `compliance_summary` - Overall compliance metrics
- `violations_by_rule` - Count per rule (rule_1 through rule_7)
- `violation_details` - Array of violating issues with full details
- `status` - "completed" or "partial" (on errors)

**No File Storage**: Agent outputs to terminal only, exits after display

## Relationships

- **GitHubIssue** → **ComplianceRule**: Many-to-Many (each issue evaluated against all 7 rules)
- **ViolationReport** → **GitHubIssue**: One-to-Many (report contains multiple issues)
- **IssueComment** → **GitHubIssue**: One-to-One (one consolidated comment per violating issue)
- **ComplianceRule** → **ViolationReport**: One-to-Many (each rule contributes to violation counts)

## Configuration Entities

### BotFilter

Configuration for filtering bot/system comments in Rule #7 evaluation.

**Attributes**:

- `bot_usernames: List[str]` - Known bot usernames to exclude
- `system_patterns: List[str]` - Comment patterns indicating system-generated content

**Default Bot List**:

- "github-actions[bot]"
- "dependabot[bot]"
- "renovate[bot]"
- "codecov[bot]"

**System Pattern Rules**:

- Comments matching regex: `^(Automatically (closed|merged)|This (issue|PR) has been)`
- Comments from users ending in `[bot]` (case-insensitive)
- Comments with only emoji reactions (no text content)

### IdempotencyConfig

Configuration for comment deduplication and hash generation.

**Attributes**:

- `hash_algorithm: str` - Default "sha256" for violation hashing
- `key_format: str` - Template "compliance-agent:{issue_id}:{hash}"
- `throttle_hours: int` - Minimum hours between duplicate detection

### ProjectConfig

Configuration for GitHub Project connection and field mapping.

**Attributes**:

- `project_identifier: str` - GitHub Project org/number or node_id
- `field_mappings: Dict[str, str]` - Custom field name mappings if different from defaults
- `timezone: str` - Default "Asia/Jakarta"
- `comment_throttle_hours: int` - Minimum hours between agent comments per issue (v2.0 feature)

## Test Fixture Requirements (15-Issue Dataset)

### Sample MCP Response Data

Test fixtures for exactly 15 issues (5 per status):

**github_list_project_items responses**:

- `github_list_project_items_in_progress_5.json` - 5 issues
- `github_list_project_items_in_review_5.json` - 5 issues
- `github_list_project_items_todo_5.json` - 5 issues
- Each with realistic field_values combinations

**github_get_issue_handler responses** (15 files):

- `github_get_issue_handler_[issue_number].json` for each issue
- Complete project_details structure
- Various field_values scenarios across 15 issues
- Mix of empty/populated assignees

**github_list_issues_comments responses** (15 files):

- `github_list_issues_comments_[issue_number].json` for each issue
- Mix of human and bot comments
- Various timestamps for Rule #7 testing
- Some with empty arrays (no comments)

### Timezone Test Cases

**Asia/Jakarta Conversion Scenarios**:

- ISO timestamps: "2025-09-24T08:00:00Z" → "2025-09-24T15:00:00+07:00"
- Date-only fields: "2025-09-24T00:00:00" → correct Jakarta date
- Edge cases: midnight boundaries, month transitions
- Invalid/null date handling

### 15-Issue Rule Coverage Distribution

**Planned distribution across 15 issues**:

1. **Empty Assignees**: 2 issues (issues #534, #540)
2. **Empty Incoming Date**: 1 issue (issue #536)
3. **Empty Due Date**: 3 issues (issues #537, #541, #545)
4. **Empty Status**: 0 issues (all have valid status)
5. **Missing Pak On Approval**: 1 issue overdue (issue #538)
6. **Due Soon Warning**: 4 issues (issues #535, #539, #542, #544)
7. **No Recent Updates**: 2 issues (issues #543, #546)
8. **Fully Compliant**: 3 issues (issues #547, #548, #549)

### Bot Filtering Test Patterns

**Bot Username Examples**:

- "github-actions[bot]"
- "dependabot[bot]"
- "renovate[bot]"
- "codecov[bot]"
- "user-bot" (should NOT be filtered)
- "bot-user" (should NOT be filtered)

**System Comment Body Patterns**:

- "Automatically closed by GitHub"
- "This issue has been automatically marked as stale"
- Emoji-only comments: "👍 🚀 ✅"
- Mixed content: "Thanks! 👍" (should NOT be filtered)
