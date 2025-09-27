"""
GitHub Issue Compliance Evaluator Tool

Tool that evaluates GitHub issues against 7 compliance rules with comprehensive
error handling and Asia/Jakarta timezone support.

Author:
    Ghozy Ghulamul Afif (ghozy.g.afif@gdplabs.id)
"""

from __future__ import annotations

import json
import random
import re
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from gllm_agents.utils import LoggerManager
from gllm_plugin.tools import tool_plugin
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = LoggerManager().get_logger(__name__)


# -------------------------
# Constants and Enums
# -------------------------

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


# -------------------------
# Utility Functions
# -------------------------

def to_jakarta_timezone(iso_string: Optional[str]) -> Optional[datetime]:
    """Convert ISO 8601 string to Asia/Jakarta timezone (UTC+7)"""
    if not iso_string:
        return None

    try:
        # Handle Z notation
        if iso_string.endswith('Z'):
            iso_string = iso_string.replace('Z', '+00:00')

        # Parse the datetime
        if 'T' in iso_string:
            dt = datetime.fromisoformat(iso_string)
        else:
            dt = datetime.fromisoformat(iso_string + 'T00:00:00+00:00')

        # Convert to Jakarta timezone (UTC+7)
        jakarta_offset = timezone(timedelta(hours=7))
        return dt.astimezone(jakarta_offset)
    except (ValueError, AttributeError) as e:
        logger.warning(f"Could not parse date '{iso_string}': {e}")
        return None


def calculate_days_difference(start_date: Optional[datetime], end_date: datetime) -> Optional[int]:
    """Calculate calendar days difference in Jakarta timezone"""
    if not start_date:
        return None

    # Ensure both dates are in the same timezone
    if start_date.tzinfo != end_date.tzinfo:
        jakarta_offset = timezone(timedelta(hours=7))
        start_date = start_date.astimezone(jakarta_offset)
        end_date = end_date.astimezone(jakarta_offset)

    # Calculate calendar days (date only, ignoring time)
    return (end_date.date() - start_date.date()).days


def is_bot_comment(username: str, body: str = "") -> bool:
    """Detect if comment is from bot/system"""
    if not username:
        return False

    # Check username patterns
    for pattern in BOT_PATTERNS:
        if re.match(pattern, username, re.IGNORECASE):
            return True

    # Check for emoji-only comments
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


def safe_extract_field(issue: Dict, field_path: str, default: Any = None) -> Any:
    """Safely extract a field from nested dictionary"""
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


# -------------------------
# Compliance Rule Checkers
# -------------------------

def check_rule_1_empty_assignees(issue: Dict) -> Optional[Dict[str, Any]]:
    """Rule 1: Check if assignees field is empty"""
    assignees = issue.get("content", {}).get("assignees", [])

    if not assignees or len(assignees) == 0:
        return {
            "rule_id": 1,
            "rule_name": "Empty Assignees",
            "severity": "medium",
            "issue_number": issue.get("content", {}).get("number", 0),
            "issue_title": issue.get("title", ""),
            "issue_url": issue.get("content", {}).get("url", ""),
            "violation_details": "Issue has no assignees",
            "assignees": [],
            "repository": issue.get("content", {}).get("repository", "")
        }
    return None


def check_rule_2_empty_incoming_date(issue: Dict) -> Optional[Dict[str, Any]]:
    """Rule 2: Check if incoming date field is empty"""
    incoming_date = extract_field_value(issue.get("field_values", []), "Incoming Date")

    if not incoming_date:
        return {
            "rule_id": 2,
            "rule_name": "Empty Incoming Date",
            "severity": "medium",
            "issue_number": issue.get("content", {}).get("number", 0),
            "issue_title": issue.get("title", ""),
            "issue_url": issue.get("content", {}).get("url", ""),
            "violation_details": "Missing 'Incoming Date' field",
            "assignees": issue.get("content", {}).get("assignees", []),
            "repository": issue.get("content", {}).get("repository", "")
        }
    return None


def check_rule_3_empty_due_date(issue: Dict) -> Optional[Dict[str, Any]]:
    """Rule 3: Check if due date field is empty"""
    due_date = extract_field_value(issue.get("field_values", []), "Due Date")

    if not due_date:
        return {
            "rule_id": 3,
            "rule_name": "Empty Due Date",
            "severity": "medium",
            "issue_number": issue.get("content", {}).get("number", 0),
            "issue_title": issue.get("title", ""),
            "issue_url": issue.get("content", {}).get("url", ""),
            "violation_details": "Missing 'Due Date' field",
            "assignees": issue.get("content", {}).get("assignees", []),
            "repository": issue.get("content", {}).get("repository", "")
        }
    return None


def check_rule_4_empty_status(issue: Dict) -> Optional[Dict[str, Any]]:
    """Rule 4: Check if status field is empty or unrecognized"""
    status = extract_field_value(issue.get("field_values", []), "Status")
    valid_statuses = ["Todo", "In Progress", "In Review", "Done", "Blocked", "Draft"]

    if not status or status not in valid_statuses:
        return {
            "rule_id": 4,
            "rule_name": "Empty Status",
            "severity": "medium",
            "issue_number": issue.get("content", {}).get("number", 0),
            "issue_title": issue.get("title", ""),
            "issue_url": issue.get("content", {}).get("url", ""),
            "violation_details": f"Invalid or missing status: '{status or 'None'}'",
            "assignees": issue.get("content", {}).get("assignees", []),
            "repository": issue.get("content", {}).get("repository", "")
        }
    return None


def check_rule_5_missing_approval_overdue(issue: Dict, current_date: datetime) -> Optional[Dict[str, Any]]:
    """Rule 5: Check if Pak On's Approval is missing and issue is >7 days old"""
    approval = extract_field_value(issue.get("field_values", []), "Pak On's Approval for Timeline")
    incoming_date_str = extract_field_value(issue.get("field_values", []), "Incoming Date")

    if not approval and incoming_date_str:
        incoming_date = to_jakarta_timezone(incoming_date_str)
        if incoming_date:
            days_since_incoming = calculate_days_difference(incoming_date, current_date)
            if days_since_incoming and days_since_incoming > 7:
                return {
                    "rule_id": 5,
                    "rule_name": "Missing Pak On Approval (Overdue)",
                    "severity": "high",
                    "issue_number": issue.get("content", {}).get("number", 0),
                    "issue_title": issue.get("title", ""),
                    "issue_url": issue.get("content", {}).get("url", ""),
                    "violation_details": f"Missing approval, {days_since_incoming} days since incoming date",
                    "assignees": issue.get("content", {}).get("assignees", []),
                    "repository": issue.get("content", {}).get("repository", "")
                }
    return None


def check_rule_6_due_soon(issue: Dict, current_date: datetime) -> Optional[Dict[str, Any]]:
    """Rule 6: Check if issue is due within next 7 days"""
    due_date_str = extract_field_value(issue.get("field_values", []), "Due Date")

    if due_date_str:
        due_date = to_jakarta_timezone(due_date_str)
        if due_date:
            days_until_due = calculate_days_difference(current_date, due_date)
            if days_until_due is not None and 0 <= days_until_due <= 7:
                severity = "high" if days_until_due <= 3 else "medium"
                return {
                    "rule_id": 6,
                    "rule_name": "Due Soon Warning",
                    "severity": severity,
                    "issue_number": issue.get("content", {}).get("number", 0),
                    "issue_title": issue.get("title", ""),
                    "issue_url": issue.get("content", {}).get("url", ""),
                    "violation_details": f"Due in {days_until_due} days",
                    "assignees": issue.get("content", {}).get("assignees", []),
                    "repository": issue.get("content", {}).get("repository", "")
                }
    return None


def check_rule_7_no_recent_updates(issue: Dict, comments: List[Dict], current_date: datetime) -> Optional[Dict[str, Any]]:
    """Rule 7: Check if issue has no human comments in last 7 days"""
    if not comments:
        return {
            "rule_id": 7,
            "rule_name": "No Recent Updates",
            "severity": "medium",
            "issue_number": issue.get("content", {}).get("number", 0),
            "issue_title": issue.get("title", ""),
            "issue_url": issue.get("content", {}).get("url", ""),
            "violation_details": "No comments on this issue",
            "assignees": issue.get("content", {}).get("assignees", []),
            "repository": issue.get("content", {}).get("repository", "")
        }

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
        return {
            "rule_id": 7,
            "rule_name": "No Recent Updates",
            "severity": "medium",
            "issue_number": issue.get("content", {}).get("number", 0),
            "issue_title": issue.get("title", ""),
            "issue_url": issue.get("content", {}).get("url", ""),
            "violation_details": "Only bot/system comments found",
            "assignees": issue.get("content", {}).get("assignees", []),
            "repository": issue.get("content", {}).get("repository", "")
        }

    # Check if most recent human comment is >7 days old
    days_since_comment = calculate_days_difference(most_recent_human_comment, current_date)
    if days_since_comment and days_since_comment > 7:
        return {
            "rule_id": 7,
            "rule_name": "No Recent Updates",
            "severity": "medium",
            "issue_number": issue.get("content", {}).get("number", 0),
            "issue_title": issue.get("title", ""),
            "issue_url": issue.get("content", {}).get("url", ""),
            "violation_details": f"No human comments for {days_since_comment} days",
            "assignees": issue.get("content", {}).get("assignees", []),
            "repository": issue.get("content", {}).get("repository", "")
        }

    return None


# -------------------------
# Tool Schema
# -------------------------

class ComplianceEvaluatorInput(BaseModel):
    """Input schema for the compliance evaluator tool"""
    issues: List[Dict[str, Any]] = Field(
        ...,
        description="List of GitHub issue objects from MCP (github_list_project_items format)"
    )
    comments_by_issue: Dict[int, List[Dict[str, Any]]] = Field(
        ...,
        description="Dictionary mapping issue number to list of comments"
    )
    current_date_str: Optional[str] = Field(
        default=None,
        description="Current date in YYYY-MM-DD format (uses today if not provided)"
    )


@tool_plugin(version="1.0.0")
class GithubComplianceEvaluatorTool(BaseTool):
    """
    Evaluate GitHub issues against 7 compliance rules with comprehensive error handling.
    Uses Asia/Jakarta timezone for all date operations.
    """
    name: str = "github_compliance_evaluator_tool"
    description: str = "Evaluate GitHub Project issues against 7 compliance rules and return detailed violation analysis."
    args_schema: type[BaseModel] = ComplianceEvaluatorInput

    def _run(
        self,
        issues: List[Dict[str, Any]],
        comments_by_issue: Dict[int, List[Dict[str, Any]]],
        current_date_str: Optional[str] = None,
        **_: Any
    ) -> Dict[str, Any]:
        try:
            # Parse current date
            if current_date_str:
                current_date = to_jakarta_timezone(current_date_str + "T00:00:00+07:00")
                if current_date is None:
                    jakarta_offset = timezone(timedelta(hours=7))
                    current_date = datetime.now(jakarta_offset)
            else:
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

            issues_processed = 0
            issues_with_errors = 0

            # Process each issue
            for index, issue in enumerate(issues):
                try:
                    issue_number = safe_extract_field(issue, "content.number", f"unknown_{index}")
                    issue_comments = comments_by_issue.get(issue_number, [])
                    issue_violations = []

                    # Check all 7 rules with individual error handling
                    rule_checkers = [
                        check_rule_1_empty_assignees,
                        check_rule_2_empty_incoming_date,
                        check_rule_3_empty_due_date,
                        check_rule_4_empty_status,
                        lambda x: check_rule_5_missing_approval_overdue(x, current_date),
                        lambda x: check_rule_6_due_soon(x, current_date),
                        lambda x: check_rule_7_no_recent_updates(x, issue_comments, current_date)
                    ]

                    for i, checker in enumerate(rule_checkers, 1):
                        try:
                            violation = checker(issue)
                            if violation:
                                issue_violations.append(violation)
                                violations.append(violation)
                                
                                # Update counts
                                if i == 1:
                                    violations_by_rule["rule_1_empty_assignees"] += 1
                                elif i == 2:
                                    violations_by_rule["rule_2_empty_incoming_date"] += 1
                                elif i == 3:
                                    violations_by_rule["rule_3_empty_due_date"] += 1
                                elif i == 4:
                                    violations_by_rule["rule_4_empty_status"] += 1
                                elif i == 5:
                                    violations_by_rule["rule_5_missing_approval_overdue"] += 1
                                elif i == 6:
                                    violations_by_rule["rule_6_due_soon_warning"] += 1
                                elif i == 7:
                                    violations_by_rule["rule_7_no_recent_updates"] += 1
                        except Exception as e:
                            logger.warning(f"Rule {i} check failed for issue {issue_number}: {e}")

                    # Add compliant issue if no violations
                    if not issue_violations:
                        compliant_issues.append({
                            "issue_number": issue_number,
                            "title": safe_extract_field(issue, "title", "Untitled Issue"),
                            "status": extract_field_value(issue.get("field_values", []), "Status"),
                            "assignees": safe_extract_field(issue, "content.assignees", [])
                        })

                    issues_processed += 1

                except Exception as e:
                    logger.error(f"Error processing issue at index {index}: {e}")
                    issues_with_errors += 1

            # Calculate summary
            total_issues = len(issues)
            issues_with_violations = len(set(v["issue_number"] for v in violations))
            compliance_rate = ((total_issues - issues_with_violations) / total_issues * 100) if total_issues > 0 else 0

            result = {
                "check_timestamp": current_date.isoformat(),
                "issues_analyzed": total_issues,
                "compliance_summary": {
                    "compliant_issues": len(compliant_issues),
                    "issues_with_violations": issues_with_violations,
                    "total_violations": len(violations),
                    "compliance_rate": round(compliance_rate, 2)
                },
                "violations_by_rule": violations_by_rule,
                "violations": violations,
                "compliant_issues": compliant_issues,
                "status": "completed"
            }

            logger.info(f"Compliance evaluation completed: {total_issues} issues analyzed, {len(violations)} violations found")
            return result

        except Exception as e:
            logger.error(f"Compliance evaluator error: {e}")
            return {"error": f"❌ Compliance evaluator error: {str(e)}"}