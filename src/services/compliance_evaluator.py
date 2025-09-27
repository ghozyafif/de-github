#!/usr/bin/env python3
"""
GitHub Issue Compliance Evaluator Tool

Self-contained GLLM Plugin tool that evaluates GitHub issues against 7 compliance rules.
All utilities are inline - no external library imports except standard library.
Uses Asia/Jakarta timezone for all date operations.
Includes error handling and retry logic for robustness.
"""

import json
import random
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

# Bot patterns for filtering (Rule #7)
BOT_PATTERNS = [
    r'.*\[bot\]$',  # GitHub bots ending with [bot]
    r'^(github-actions|dependabot|renovate|codecov)\[bot\]$',  # Common bots
    r'^bot-',  # Bots starting with bot-
    r'^automated-',  # Automated accounts
]

# System comment patterns
SYSTEM_MESSAGE_PATTERNS = [
    r'^This (issue|PR) has been',
    r'^Automatically (closed|merged)',
    r'^Closing this (issue|PR)',
    r'^Merged #\d+',
]


class Severity(Enum):
    """Violation severity levels"""
    HIGH = "high"      # Overdue items
    MEDIUM = "medium"  # Missing metadata
    LOW = "low"        # Warnings


@dataclass
class ComplianceViolation:
    """Represents a single compliance violation"""
    rule_id: int
    rule_name: str
    severity: Severity
    issue_number: int
    issue_title: str
    issue_url: str
    violation_details: str
    assignees: List[str] = field(default_factory=list)
    repository: str = ""


def to_jakarta_timezone(iso_string: Optional[str]) -> Optional[datetime]:
    """
    Convert ISO 8601 string to Asia/Jakarta timezone (UTC+7)
    Handles various ISO formats including Z notation and +HH:MM offsets
    """
    if not iso_string:
        return None

    try:
        # Handle Z notation
        if iso_string.endswith('Z'):
            iso_string = iso_string.replace('Z', '+00:00')

        # Parse the datetime
        if 'T' in iso_string:
            # Full datetime with time
            dt = datetime.fromisoformat(iso_string)
        else:
            # Date only - assume start of day
            dt = datetime.fromisoformat(iso_string + 'T00:00:00+00:00')

        # Convert to Jakarta timezone (UTC+7)
        jakarta_offset = timezone(timedelta(hours=7))
        return dt.astimezone(jakarta_offset)
    except (ValueError, AttributeError) as e:
        print(f"Warning: Could not parse date '{iso_string}': {e}")
        return None


def calculate_days_difference(start_date: Optional[datetime], end_date: datetime) -> Optional[int]:
    """
    Calculate calendar days difference in Jakarta timezone
    Returns None if start_date is None
    """
    if not start_date:
        return None

    # Ensure both dates are in the same timezone
    if start_date.tzinfo != end_date.tzinfo:
        # Convert to Jakarta timezone
        jakarta_offset = timezone(timedelta(hours=7))
        start_date = start_date.astimezone(jakarta_offset)
        end_date = end_date.astimezone(jakarta_offset)

    # Calculate calendar days (date only, ignoring time)
    return (end_date.date() - start_date.date()).days


def is_bot_comment(username: str, body: str = "") -> bool:
    """
    Detect if comment is from bot/system
    Checks both username patterns and message content
    """
    if not username:
        return False

    # Check username patterns
    for pattern in BOT_PATTERNS:
        if re.match(pattern, username, re.IGNORECASE):
            return True

    # Check for emoji-only comments (often reactions from bots)
    if body and re.match(r'^[\s\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+$', body):
        return True

    # Check for system messages
    for pattern in SYSTEM_MESSAGE_PATTERNS:
        if re.match(pattern, body, re.IGNORECASE):
            return True

    return False


def extract_field_value(field_values: List[Dict], field_name: str) -> Optional[Any]:
    """Extract a specific field value from the field_values array"""
    for field in field_values:
        if field.get("name") == field_name:
            return field.get("value")
    return None


def check_rule_1_empty_assignees(issue: Dict) -> Optional[ComplianceViolation]:
    """Rule 1: Check if assignees field is empty"""
    assignees = issue.get("content", {}).get("assignees", [])

    if not assignees or len(assignees) == 0:
        return ComplianceViolation(
            rule_id=1,
            rule_name="Empty Assignees",
            severity=Severity.MEDIUM,
            issue_number=issue.get("content", {}).get("number", 0),
            issue_title=issue.get("title", ""),
            issue_url=issue.get("content", {}).get("url", ""),
            violation_details="Issue has no assignees",
            repository=issue.get("content", {}).get("repository", "")
        )
    return None


def check_rule_2_empty_incoming_date(issue: Dict) -> Optional[ComplianceViolation]:
    """Rule 2: Check if incoming date field is empty"""
    incoming_date = extract_field_value(issue.get("field_values", []), "Incoming Date")

    if not incoming_date:
        return ComplianceViolation(
            rule_id=2,
            rule_name="Empty Incoming Date",
            severity=Severity.MEDIUM,
            issue_number=issue.get("content", {}).get("number", 0),
            issue_title=issue.get("title", ""),
            issue_url=issue.get("content", {}).get("url", ""),
            violation_details="Missing 'Incoming Date' field",
            assignees=issue.get("content", {}).get("assignees", []),
            repository=issue.get("content", {}).get("repository", "")
        )
    return None


def check_rule_3_empty_due_date(issue: Dict) -> Optional[ComplianceViolation]:
    """Rule 3: Check if due date field is empty"""
    due_date = extract_field_value(issue.get("field_values", []), "Due Date")

    if not due_date:
        return ComplianceViolation(
            rule_id=3,
            rule_name="Empty Due Date",
            severity=Severity.MEDIUM,
            issue_number=issue.get("content", {}).get("number", 0),
            issue_title=issue.get("title", ""),
            issue_url=issue.get("content", {}).get("url", ""),
            violation_details="Missing 'Due Date' field",
            assignees=issue.get("content", {}).get("assignees", []),
            repository=issue.get("content", {}).get("repository", "")
        )
    return None


def check_rule_4_empty_status(issue: Dict) -> Optional[ComplianceViolation]:
    """Rule 4: Check if status field is empty or unrecognized"""
    status = extract_field_value(issue.get("field_values", []), "Status")
    valid_statuses = ["Todo", "In Progress", "In Review", "Done", "Blocked", "Draft"]

    if not status or status not in valid_statuses:
        return ComplianceViolation(
            rule_id=4,
            rule_name="Empty Status",
            severity=Severity.MEDIUM,
            issue_number=issue.get("content", {}).get("number", 0),
            issue_title=issue.get("title", ""),
            issue_url=issue.get("content", {}).get("url", ""),
            violation_details=f"Invalid or missing status: '{status or 'None'}'",
            assignees=issue.get("content", {}).get("assignees", []),
            repository=issue.get("content", {}).get("repository", "")
        )
    return None


def check_rule_5_missing_approval_overdue(issue: Dict, current_date: datetime) -> Optional[ComplianceViolation]:
    """Rule 5: Check if Pak On's Approval is missing and issue is >7 days old"""
    approval = extract_field_value(issue.get("field_values", []), "Pak On's Approval for Timeline")
    incoming_date_str = extract_field_value(issue.get("field_values", []), "Incoming Date")

    if not approval and incoming_date_str:
        incoming_date = to_jakarta_timezone(incoming_date_str)
        if incoming_date:
            days_since_incoming = calculate_days_difference(incoming_date, current_date)
            if days_since_incoming and days_since_incoming > 7:
                return ComplianceViolation(
                    rule_id=5,
                    rule_name="Missing Pak On Approval (Overdue)",
                    severity=Severity.HIGH,
                    issue_number=issue.get("content", {}).get("number", 0),
                    issue_title=issue.get("title", ""),
                    issue_url=issue.get("content", {}).get("url", ""),
                    violation_details=f"Missing approval, {days_since_incoming} days since incoming date",
                    assignees=issue.get("content", {}).get("assignees", []),
                    repository=issue.get("content", {}).get("repository", "")
                )
    return None


def check_rule_6_due_soon(issue: Dict, current_date: datetime) -> Optional[ComplianceViolation]:
    """Rule 6: Check if issue is due within next 7 days"""
    due_date_str = extract_field_value(issue.get("field_values", []), "Due Date")

    if due_date_str:
        due_date = to_jakarta_timezone(due_date_str)
        if due_date:
            days_until_due = calculate_days_difference(current_date, due_date)
            if days_until_due is not None and 0 <= days_until_due <= 7:
                return ComplianceViolation(
                    rule_id=6,
                    rule_name="Due Soon Warning",
                    severity=Severity.HIGH if days_until_due <= 3 else Severity.MEDIUM,
                    issue_number=issue.get("content", {}).get("number", 0),
                    issue_title=issue.get("title", ""),
                    issue_url=issue.get("content", {}).get("url", ""),
                    violation_details=f"Due in {days_until_due} days",
                    assignees=issue.get("content", {}).get("assignees", []),
                    repository=issue.get("content", {}).get("repository", "")
                )
    return None


def check_rule_7_no_recent_updates(issue: Dict, comments: List[Dict], current_date: datetime) -> Optional[ComplianceViolation]:
    """Rule 7: Check if issue has no human comments in last 7 days"""
    if not comments:
        # No comments at all
        return ComplianceViolation(
            rule_id=7,
            rule_name="No Recent Updates",
            severity=Severity.MEDIUM,
            issue_number=issue.get("content", {}).get("number", 0),
            issue_title=issue.get("title", ""),
            issue_url=issue.get("content", {}).get("url", ""),
            violation_details="No comments on this issue",
            assignees=issue.get("content", {}).get("assignees", []),
            repository=issue.get("content", {}).get("repository", "")
        )

    # Find most recent human comment
    most_recent_human_comment = None
    for comment in comments:
        user = comment.get("user", {})
        username = user.get("login", "")
        body = comment.get("body", "")

        if not is_bot_comment(username, body):
            comment_date_str = comment.get("created_at")
            if comment_date_str:
                comment_date = to_jakarta_timezone(comment_date_str)
                if comment_date:
                    if not most_recent_human_comment or comment_date > most_recent_human_comment:
                        most_recent_human_comment = comment_date

    if not most_recent_human_comment:
        # Only bot comments
        return ComplianceViolation(
            rule_id=7,
            rule_name="No Recent Updates",
            severity=Severity.MEDIUM,
            issue_number=issue.get("content", {}).get("number", 0),
            issue_title=issue.get("title", ""),
            issue_url=issue.get("content", {}).get("url", ""),
            violation_details="Only bot/system comments found",
            assignees=issue.get("content", {}).get("assignees", []),
            repository=issue.get("content", {}).get("repository", "")
        )

    # Check if most recent human comment is >7 days old
    days_since_comment = calculate_days_difference(most_recent_human_comment, current_date)
    if days_since_comment and days_since_comment > 7:
        return ComplianceViolation(
            rule_id=7,
            rule_name="No Recent Updates",
            severity=Severity.MEDIUM,
            issue_number=issue.get("content", {}).get("number", 0),
            issue_title=issue.get("title", ""),
            issue_url=issue.get("content", {}).get("url", ""),
            violation_details=f"No human comments for {days_since_comment} days",
            assignees=issue.get("content", {}).get("assignees", []),
            repository=issue.get("content", {}).get("repository", "")
        )

    return None


def retry_with_backoff(func: Callable, max_retries: int = 3, initial_delay: float = 1.0) -> Any:
    """
    Retry a function with exponential backoff

    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds

    Returns:
        Function result or raises last exception
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                # Add jitter to prevent thundering herd
                jittered_delay = delay * (1 + random.random() * 0.1)
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {jittered_delay:.2f}s...")
                time.sleep(jittered_delay)
                delay *= 2  # Exponential backoff
            else:
                print(f"All {max_retries + 1} attempts failed. Last error: {e}")

    raise last_exception


def safe_extract_field(issue: Dict, field_path: str, default: Any = None) -> Any:
    """
    Safely extract a field from nested dictionary

    Args:
        issue: Issue dictionary
        field_path: Dot-separated path (e.g., "content.number")
        default: Default value if field not found

    Returns:
        Field value or default
    """
    try:
        parts = field_path.split(".")
        value = issue
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
                if value is None:
                    return default
            else:
                return default
        return value
    except (KeyError, TypeError, AttributeError):
        return default


def process_issue_with_error_handling(
    issue: Dict,
    comments: List[Dict],
    current_date: datetime,
    issue_index: int,
    total_issues: int
) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Process a single issue with comprehensive error handling

    Returns:
        Tuple of (violations, compliant_issue_info or None)
    """
    issue_violations = []
    issue_number = safe_extract_field(issue, "content.number", f"unknown_{issue_index}")
    issue_title = safe_extract_field(issue, "title", "Untitled Issue")

    try:
        # Check all 7 rules with individual error handling
        try:
            violation = check_rule_1_empty_assignees(issue)
            if violation:
                issue_violations.append(violation)
        except Exception as e:
            print(f"Warning: Rule 1 check failed for issue {issue_number}: {e}")

        try:
            violation = check_rule_2_empty_incoming_date(issue)
            if violation:
                issue_violations.append(violation)
        except Exception as e:
            print(f"Warning: Rule 2 check failed for issue {issue_number}: {e}")

        try:
            violation = check_rule_3_empty_due_date(issue)
            if violation:
                issue_violations.append(violation)
        except Exception as e:
            print(f"Warning: Rule 3 check failed for issue {issue_number}: {e}")

        try:
            violation = check_rule_4_empty_status(issue)
            if violation:
                issue_violations.append(violation)
        except Exception as e:
            print(f"Warning: Rule 4 check failed for issue {issue_number}: {e}")

        try:
            violation = check_rule_5_missing_approval_overdue(issue, current_date)
            if violation:
                issue_violations.append(violation)
        except Exception as e:
            print(f"Warning: Rule 5 check failed for issue {issue_number}: {e}")

        try:
            violation = check_rule_6_due_soon(issue, current_date)
            if violation:
                issue_violations.append(violation)
        except Exception as e:
            print(f"Warning: Rule 6 check failed for issue {issue_number}: {e}")

        try:
            violation = check_rule_7_no_recent_updates(issue, comments, current_date)
            if violation:
                issue_violations.append(violation)
        except Exception as e:
            print(f"Warning: Rule 7 check failed for issue {issue_number}: {e}")

        # Create compliant issue info if no violations
        if not issue_violations:
            return [], {
                "issue_number": issue_number,
                "title": issue_title,
                "status": extract_field_value(issue.get("field_values", []), "Status"),
                "assignees": safe_extract_field(issue, "content.assignees", [])
            }

        return issue_violations, None

    except Exception as e:
        print(f"Error processing issue {issue_number}: {e}")
        # Return partial results on error
        return issue_violations, None


def github_compliance_evaluator_tool(
    issues: List[Dict],
    comments_by_issue: Dict[int, List[Dict]],
    current_date_str: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main GLLM Plugin tool function for compliance evaluation

    Args:
        issues: List of GitHub issue objects from MCP
        comments_by_issue: Dict mapping issue number to list of comments
        current_date_str: Current date in YYYY-MM-DD format (uses today if not provided)

    Returns:
        Dict with violations, summary, and execution details
    """
    # Parse current date
    if current_date_str:
        current_date = to_jakarta_timezone(current_date_str + "T00:00:00+07:00")
    else:
        # Use current time in Jakarta
        jakarta_offset = timezone(timedelta(hours=7))
        current_date = datetime.now(jakarta_offset)

    # Initialize result structure
    violations = []
    compliant_issues = []
    violations_by_rule = {
        "rule_1_empty_assignees": 0,
        "rule_2_empty_incoming_date": 0,
        "rule_3_empty_due_date": 0,
        "rule_4_empty_status": 0,
        "rule_5_missing_approval_overdue": 0,
        "rule_6_due_soon_warning": 0,
        "rule_7_no_recent_updates": 0
    }

    # Process each issue with error handling
    issues_processed = 0
    issues_with_errors = 0

    for index, issue in enumerate(issues):
        try:
            issue_number = safe_extract_field(issue, "content.number", f"unknown_{index}")
            issue_comments = comments_by_issue.get(issue_number, [])

            # Process issue with comprehensive error handling
            issue_violations, compliant_info = process_issue_with_error_handling(
                issue=issue,
                comments=issue_comments,
                current_date=current_date,
                issue_index=index,
                total_issues=len(issues)
            )

            # Update violation counts
            for violation in issue_violations:
                violations.append(violation)
                rule_key = f"rule_{violation.rule_id}_{violation.rule_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}"
                # Normalize the key to match our structure
                if violation.rule_id == 1:
                    violations_by_rule["rule_1_empty_assignees"] += 1
                elif violation.rule_id == 2:
                    violations_by_rule["rule_2_empty_incoming_date"] += 1
                elif violation.rule_id == 3:
                    violations_by_rule["rule_3_empty_due_date"] += 1
                elif violation.rule_id == 4:
                    violations_by_rule["rule_4_empty_status"] += 1
                elif violation.rule_id == 5:
                    violations_by_rule["rule_5_missing_approval_overdue"] += 1
                elif violation.rule_id == 6:
                    violations_by_rule["rule_6_due_soon_warning"] += 1
                elif violation.rule_id == 7:
                    violations_by_rule["rule_7_no_recent_updates"] += 1

            # Add compliant issue if no violations
            if compliant_info:
                compliant_issues.append(compliant_info)

            issues_processed += 1

        except Exception as e:
            print(f"Error processing issue at index {index}: {e}")
            issues_with_errors += 1
            # Continue processing other issues

    # Calculate summary
    total_issues = len(issues)
    issues_with_violations = len(set(v.issue_number for v in violations))
    compliance_rate = ((total_issues - issues_with_violations) / total_issues * 100) if total_issues > 0 else 0

    # Format violations for output
    formatted_violations = []
    for v in violations:
        formatted_violations.append({
            "rule_id": v.rule_id,
            "rule_name": v.rule_name,
            "severity": v.severity.value,
            "issue_number": v.issue_number,
            "issue_title": v.issue_title,
            "issue_url": v.issue_url,
            "violation_details": v.violation_details,
            "assignees": v.assignees,
            "repository": v.repository
        })

    return {
        "check_timestamp": current_date.isoformat(),
        "issues_analyzed": total_issues,
        "compliance_summary": {
            "compliant_issues": len(compliant_issues),
            "issues_with_violations": issues_with_violations,
            "total_violations": len(violations),
            "compliance_rate": round(compliance_rate, 2)
        },
        "violations_by_rule": violations_by_rule,
        "violations": formatted_violations,
        "compliant_issues": compliant_issues,
        "status": "completed"
    }


# For direct testing
if __name__ == "__main__":
    # Test with sample data
    test_issues = [
        {
            "content": {"number": 101, "assignees": [], "url": "test.com/101", "repository": "test"},
            "title": "Test Issue",
            "field_values": [
                {"name": "Status", "value": "Todo"},
                {"name": "Incoming Date", "value": "2025-09-01T00:00:00"}
            ]
        }
    ]
    test_comments = {101: []}

    result = github_compliance_evaluator_tool(test_issues, test_comments, "2025-09-25")
    print(json.dumps(result, indent=2))