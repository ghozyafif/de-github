#!/usr/bin/env python3
"""
Unit tests for the GitHub Issue Compliance Evaluator
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.compliance_evaluator import (
    github_compliance_evaluator_tool,
    to_jakarta_timezone,
    calculate_days_difference,
    is_bot_comment,
    extract_field_value,
    check_rule_1_empty_assignees,
    check_rule_2_empty_incoming_date,
    check_rule_3_empty_due_date,
    check_rule_4_empty_status,
    check_rule_5_missing_approval_overdue,
    check_rule_6_due_soon,
    check_rule_7_no_recent_updates,
)


class TestTimezoneUtilities:
    """Test timezone conversion utilities"""

    def test_to_jakarta_timezone_with_z_notation(self):
        """Test conversion with Z notation"""
        result = to_jakarta_timezone("2025-09-25T00:00:00Z")
        assert result is not None
        assert result.utcoffset() == timedelta(hours=7)

    def test_to_jakarta_timezone_with_offset(self):
        """Test conversion with explicit offset"""
        result = to_jakarta_timezone("2025-09-25T00:00:00+00:00")
        assert result is not None
        assert result.utcoffset() == timedelta(hours=7)

    def test_to_jakarta_timezone_date_only(self):
        """Test conversion with date only"""
        result = to_jakarta_timezone("2025-09-25")
        assert result is not None
        assert result.hour == 7  # Midnight UTC is 7 AM Jakarta

    def test_to_jakarta_timezone_none(self):
        """Test with None input"""
        result = to_jakarta_timezone(None)
        assert result is None

    def test_calculate_days_difference(self):
        """Test calendar days calculation"""
        jakarta_tz = timezone(timedelta(hours=7))
        start = datetime(2025, 9, 20, 10, 0, 0, tzinfo=jakarta_tz)
        end = datetime(2025, 9, 25, 15, 0, 0, tzinfo=jakarta_tz)
        result = calculate_days_difference(start, end)
        assert result == 5

    def test_calculate_days_difference_none(self):
        """Test days calculation with None start"""
        end = datetime.now(timezone(timedelta(hours=7)))
        result = calculate_days_difference(None, end)
        assert result is None


class TestBotDetection:
    """Test bot comment filtering"""

    def test_is_bot_comment_github_actions(self):
        """Test GitHub Actions bot detection"""
        assert is_bot_comment("github-actions[bot]") is True

    def test_is_bot_comment_dependabot(self):
        """Test Dependabot detection"""
        assert is_bot_comment("dependabot[bot]") is True

    def test_is_bot_comment_human(self):
        """Test human user is not detected as bot"""
        assert is_bot_comment("developer1") is False

    def test_is_bot_comment_emoji_only(self):
        """Test emoji-only comment detection"""
        assert is_bot_comment("user", "👍") is True

    def test_is_bot_comment_system_message(self):
        """Test system message detection"""
        assert is_bot_comment("user", "This issue has been automatically closed") is True

    def test_is_bot_comment_normal_message(self):
        """Test normal message is not detected as bot"""
        assert is_bot_comment("user", "Working on this issue now") is False


class TestFieldExtraction:
    """Test field value extraction"""

    def test_extract_field_value_exists(self):
        """Test extraction of existing field"""
        field_values = [
            {"name": "Status", "value": "In Progress"},
            {"name": "Due Date", "value": "2025-09-30"}
        ]
        result = extract_field_value(field_values, "Status")
        assert result == "In Progress"

    def test_extract_field_value_missing(self):
        """Test extraction of missing field"""
        field_values = [
            {"name": "Status", "value": "In Progress"}
        ]
        result = extract_field_value(field_values, "Due Date")
        assert result is None

    def test_extract_field_value_empty_list(self):
        """Test extraction from empty list"""
        result = extract_field_value([], "Status")
        assert result is None


class TestComplianceRules:
    """Test individual compliance rules"""

    def test_rule_1_empty_assignees_violation(self):
        """Test Rule 1 with empty assignees"""
        issue = {
            "content": {
                "number": 101,
                "assignees": [],
                "url": "test.com/101",
                "repository": "test"
            },
            "title": "Test Issue",
            "field_values": []
        }
        violation = check_rule_1_empty_assignees(issue)
        assert violation is not None
        assert violation.rule_id == 1
        assert violation.issue_number == 101

    def test_rule_1_empty_assignees_compliant(self):
        """Test Rule 1 with assignees present"""
        issue = {
            "content": {
                "number": 101,
                "assignees": ["user1"],
                "url": "test.com/101",
                "repository": "test"
            },
            "title": "Test Issue",
            "field_values": []
        }
        violation = check_rule_1_empty_assignees(issue)
        assert violation is None

    def test_rule_2_empty_incoming_date_violation(self):
        """Test Rule 2 with missing incoming date"""
        issue = {
            "content": {"number": 102},
            "title": "Test Issue",
            "field_values": [
                {"name": "Status", "value": "Todo"}
            ]
        }
        violation = check_rule_2_empty_incoming_date(issue)
        assert violation is not None
        assert violation.rule_id == 2

    def test_rule_3_empty_due_date_violation(self):
        """Test Rule 3 with missing due date"""
        issue = {
            "content": {"number": 103},
            "title": "Test Issue",
            "field_values": [
                {"name": "Status", "value": "In Progress"}
            ]
        }
        violation = check_rule_3_empty_due_date(issue)
        assert violation is not None
        assert violation.rule_id == 3

    def test_rule_4_empty_status_violation(self):
        """Test Rule 4 with invalid status"""
        issue = {
            "content": {"number": 104},
            "title": "Test Issue",
            "field_values": [
                {"name": "Status", "value": "Invalid"}
            ]
        }
        violation = check_rule_4_empty_status(issue)
        assert violation is not None
        assert violation.rule_id == 4

    def test_rule_5_missing_approval_overdue(self):
        """Test Rule 5 with missing approval and >7 days"""
        issue = {
            "content": {"number": 105},
            "title": "Test Issue",
            "field_values": [
                {"name": "Incoming Date", "value": "2025-09-01T00:00:00"}
            ]
        }
        current_date = to_jakarta_timezone("2025-09-25T00:00:00+07:00")
        violation = check_rule_5_missing_approval_overdue(issue, current_date)
        assert violation is not None
        assert violation.rule_id == 5
        assert violation.severity.value == "high"

    def test_rule_6_due_soon(self):
        """Test Rule 6 with issue due in 3 days"""
        issue = {
            "content": {"number": 106},
            "title": "Test Issue",
            "field_values": [
                {"name": "Due Date", "value": "2025-09-28T00:00:00"}
            ]
        }
        current_date = to_jakarta_timezone("2025-09-25T00:00:00+07:00")
        violation = check_rule_6_due_soon(issue, current_date)
        assert violation is not None
        assert violation.rule_id == 6
        assert "3 days" in violation.violation_details

    def test_rule_7_no_recent_updates_no_comments(self):
        """Test Rule 7 with no comments at all"""
        issue = {
            "content": {"number": 107},
            "title": "Test Issue",
            "field_values": []
        }
        comments = []
        current_date = to_jakarta_timezone("2025-09-25T00:00:00+07:00")
        violation = check_rule_7_no_recent_updates(issue, comments, current_date)
        assert violation is not None
        assert violation.rule_id == 7
        assert "No comments" in violation.violation_details

    def test_rule_7_no_recent_updates_only_bot_comments(self):
        """Test Rule 7 with only bot comments"""
        issue = {
            "content": {"number": 108},
            "title": "Test Issue",
            "field_values": []
        }
        comments = [
            {
                "user": {"login": "github-actions[bot]"},
                "body": "Automated message",
                "created_at": "2025-09-24T00:00:00Z"
            }
        ]
        current_date = to_jakarta_timezone("2025-09-25T00:00:00+07:00")
        violation = check_rule_7_no_recent_updates(issue, comments, current_date)
        assert violation is not None
        assert violation.rule_id == 7
        assert "Only bot/system comments" in violation.violation_details

    def test_rule_7_no_recent_updates_old_human_comment(self):
        """Test Rule 7 with old human comment"""
        issue = {
            "content": {"number": 109},
            "title": "Test Issue",
            "field_values": []
        }
        comments = [
            {
                "user": {"login": "developer1"},
                "body": "Working on this",
                "created_at": "2025-09-10T00:00:00Z"
            }
        ]
        current_date = to_jakarta_timezone("2025-09-25T00:00:00+07:00")
        violation = check_rule_7_no_recent_updates(issue, comments, current_date)
        assert violation is not None
        assert violation.rule_id == 7
        assert "15 days" in violation.violation_details


class TestComplianceEvaluatorTool:
    """Test the main compliance evaluator tool"""

    def test_github_compliance_evaluator_tool_basic(self):
        """Test basic evaluation with mixed violations"""
        issues = [
            {
                "content": {
                    "number": 101,
                    "assignees": [],  # Rule 1 violation
                    "url": "test.com/101",
                    "repository": "test"
                },
                "title": "Test Issue 1",
                "field_values": [
                    {"name": "Status", "value": "Todo"},
                    {"name": "Incoming Date", "value": "2025-09-20T00:00:00"}
                ]
            },
            {
                "content": {
                    "number": 102,
                    "assignees": ["user1"],
                    "url": "test.com/102",
                    "repository": "test"
                },
                "title": "Test Issue 2",
                "field_values": [
                    {"name": "Status", "value": "In Progress"},
                    {"name": "Incoming Date", "value": "2025-09-15T00:00:00"},
                    {"name": "Due Date", "value": "2025-09-30T00:00:00"}
                ]
            }
        ]
        comments = {101: [], 102: []}

        result = github_compliance_evaluator_tool(issues, comments, "2025-09-25")

        assert result["status"] == "completed"
        assert result["issues_analyzed"] == 2
        assert result["violations_by_rule"]["rule_1_empty_assignees"] == 1
        assert result["violations_by_rule"]["rule_3_empty_due_date"] == 1
        assert len(result["violations"]) >= 2

    def test_github_compliance_evaluator_tool_no_violations(self):
        """Test evaluation with fully compliant issue"""
        issues = [
            {
                "content": {
                    "number": 201,
                    "assignees": ["user1"],
                    "url": "test.com/201",
                    "repository": "test"
                },
                "title": "Compliant Issue",
                "field_values": [
                    {"name": "Status", "value": "In Progress"},
                    {"name": "Incoming Date", "value": "2025-09-20T00:00:00"},
                    {"name": "Due Date", "value": "2025-10-30T00:00:00"},
                    {"name": "Pak On's Approval for Timeline", "value": "Approved"}
                ]
            }
        ]
        comments = {
            201: [
                {
                    "user": {"login": "developer1"},
                    "body": "Recent update",
                    "created_at": "2025-09-24T00:00:00Z"
                }
            ]
        }

        result = github_compliance_evaluator_tool(issues, comments, "2025-09-25")

        assert result["status"] == "completed"
        assert result["compliance_summary"]["compliant_issues"] == 1
        assert result["compliance_summary"]["issues_with_violations"] == 0
        assert result["compliance_summary"]["compliance_rate"] == 100.0
        assert len(result["compliant_issues"]) == 1

    def test_github_compliance_evaluator_tool_with_fixtures(self):
        """Test with actual fixture data"""
        fixtures_dir = Path(__file__).parent.parent / "fixtures" / "mcp"

        # Load a fixture file
        fixture_file = fixtures_dir / "github_list_project_items_todo_5.json"
        if fixture_file.exists():
            with open(fixture_file) as f:
                data = json.load(f)
                issues = data["result"]["data"]

            # Create empty comments for each issue
            comments = {issue["content"]["number"]: [] for issue in issues}

            result = github_compliance_evaluator_tool(issues, comments, "2025-09-25")

            assert result["status"] == "completed"
            assert result["issues_analyzed"] == 5
            # All issues should have Rule 7 violation (no comments)
            assert result["violations_by_rule"]["rule_7_no_recent_updates"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])