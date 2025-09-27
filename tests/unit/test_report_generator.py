#!/usr/bin/env python3
"""
Unit tests for the GitHub Issue Compliance Report Generator
"""

import json
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.report_generator import (calculate_severity_distribution,
                                           format_execution_time,
                                           generate_issue_summary,
                                           generate_recommendations,
                                           generate_summary_report,
                                           github_report_generator_tool,
                                           group_violations_by_issue)


class TestReportFormatting:
    """Test report formatting utilities"""

    def test_format_execution_time_seconds(self):
        """Test formatting execution time in seconds"""
        result = format_execution_time(0, 45.5)
        assert result == "45.5 seconds"

    def test_format_execution_time_minutes(self):
        """Test formatting execution time in minutes"""
        result = format_execution_time(0, 125)
        assert result == "2 minutes 5 seconds"

    def test_format_execution_time_hours(self):
        """Test formatting execution time in hours"""
        result = format_execution_time(0, 7325)
        assert result == "2 hours 2 minutes"

    def test_group_violations_by_issue(self):
        """Test grouping violations by issue number"""
        violations = [
            {"issue_number": 101, "rule_id": 1},
            {"issue_number": 102, "rule_id": 2},
            {"issue_number": 101, "rule_id": 3},
        ]
        result = group_violations_by_issue(violations)
        assert len(result) == 2
        assert len(result[101]) == 2
        assert len(result[102]) == 1

    def test_calculate_severity_distribution(self):
        """Test calculating severity distribution"""
        violations = [
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"},
        ]
        result = calculate_severity_distribution(violations)
        assert result["high"] == 2
        assert result["medium"] == 1
        assert result["low"] == 1

    def test_generate_issue_summary(self):
        """Test generating issue summary"""
        violations = [
            {
                "issue_number": 101,
                "issue_title": "Test Issue",
                "issue_url": "test.com/101",
                "repository": "test-repo",
                "assignees": ["user1"],
                "rule_id": 1,
                "rule_name": "Empty Assignees",
                "severity": "medium",
                "violation_details": "No assignees"
            },
            {
                "issue_number": 101,
                "issue_title": "Test Issue",
                "issue_url": "test.com/101",
                "repository": "test-repo",
                "assignees": ["user1"],
                "rule_id": 3,
                "rule_name": "Empty Due Date",
                "severity": "medium",
                "violation_details": "Missing due date"
            }
        ]
        result = generate_issue_summary(violations)
        assert result["issue_number"] == 101
        assert result["violation_count"] == 2
        assert len(result["violations"]) == 2


class TestRecommendations:
    """Test recommendation generation"""

    def test_generate_recommendations_empty_assignees(self):
        """Test recommendations for empty assignees"""
        violations_by_rule = {"rule_1_empty_assignees": 5}
        result = generate_recommendations(violations_by_rule)
        assert any("Assign team members" in r for r in result)

    def test_generate_recommendations_missing_dates(self):
        """Test recommendations for missing dates"""
        violations_by_rule = {
            "rule_2_empty_incoming_date": 3,
            "rule_3_empty_due_date": 2
        }
        result = generate_recommendations(violations_by_rule)
        assert any("Incoming Date" in r for r in result)
        assert any("Due Date" in r for r in result)

    def test_generate_recommendations_approval_overdue(self):
        """Test recommendations for overdue approval"""
        violations_by_rule = {"rule_5_missing_approval_overdue": 1}
        result = generate_recommendations(violations_by_rule)
        assert any("URGENT" in r and "Pak On" in r for r in result)

    def test_generate_recommendations_stale_issues(self):
        """Test recommendations for stale issues"""
        violations_by_rule = {"rule_7_no_recent_updates": 10}
        result = generate_recommendations(violations_by_rule)
        assert any("status updates" in r for r in result)


class TestReportGeneratorTool:
    """Test the main report generator tool"""

    def test_github_report_generator_tool_basic(self):
        """Test basic report generation"""
        evaluation_results = {
            "check_timestamp": "2025-09-25T10:00:00+07:00",
            "issues_analyzed": 15,
            "compliance_summary": {
                "compliant_issues": 5,
                "issues_with_violations": 10,
                "total_violations": 18,
                "compliance_rate": 33.33
            },
            "violations_by_rule": {
                "rule_1_empty_assignees": 3,
                "rule_2_empty_incoming_date": 2,
                "rule_3_empty_due_date": 4,
                "rule_4_empty_status": 0,
                "rule_5_missing_approval_overdue": 2,
                "rule_6_due_soon_warning": 3,
                "rule_7_no_recent_updates": 4
            },
            "violations": [
                {
                    "rule_id": 1,
                    "rule_name": "Empty Assignees",
                    "severity": "medium",
                    "issue_number": 101,
                    "issue_title": "Test Issue",
                    "issue_url": "https://github.com/test/101",
                    "violation_details": "Issue has no assignees",
                    "assignees": [],
                    "repository": "test-repo"
                }
            ],
            "compliant_issues": [
                {
                    "issue_number": 201,
                    "title": "Compliant Issue",
                    "status": "In Progress",
                    "assignees": ["user1"]
                }
            ],
            "status": "completed"
        }

        report_json = github_report_generator_tool(
            evaluation_results,
            execution_start_time=0,
            execution_end_time=87
        )

        # Parse the JSON output
        report = json.loads(report_json)
        assert "github_compliance_report" in report

        compliance_report = report["github_compliance_report"]
        assert compliance_report["metadata"]["project"] == "GDP-ADMIN/223"
        # Check that execution time was calculated correctly
        execution_time = compliance_report["metadata"]["execution_time"]
        # With start=0 and end=87, we should get "1 minutes 27 seconds" or "87.0 seconds"
        assert "87.0 seconds" in execution_time or "1 minutes 27 seconds" in execution_time
        assert compliance_report["summary"]["issues_analyzed"] == 15
        assert compliance_report["summary"]["compliance_rate"] == "33.33%"
        assert len(compliance_report["recommendations"]) > 0

    def test_github_report_generator_tool_no_violations(self):
        """Test report generation with no violations"""
        evaluation_results = {
            "check_timestamp": "2025-09-25T10:00:00+07:00",
            "issues_analyzed": 5,
            "compliance_summary": {
                "compliant_issues": 5,
                "issues_with_violations": 0,
                "total_violations": 0,
                "compliance_rate": 100.0
            },
            "violations_by_rule": {
                "rule_1_empty_assignees": 0,
                "rule_2_empty_incoming_date": 0,
                "rule_3_empty_due_date": 0,
                "rule_4_empty_status": 0,
                "rule_5_missing_approval_overdue": 0,
                "rule_6_due_soon_warning": 0,
                "rule_7_no_recent_updates": 0
            },
            "violations": [],
            "compliant_issues": [
                {"issue_number": i, "title": f"Issue {i}", "status": "In Progress", "assignees": ["user1"]}
                for i in range(101, 106)
            ],
            "status": "completed"
        }

        report_json = github_report_generator_tool(evaluation_results)
        report = json.loads(report_json)

        compliance_report = report["github_compliance_report"]
        assert compliance_report["summary"]["compliance_rate"] == "100.0%"
        assert compliance_report["summary"]["issues_with_violations"] == 0
        assert len(compliance_report["detailed_violations"]) == 0
        assert len(compliance_report["recommendations"]) == 0

    def test_github_report_generator_tool_with_error(self):
        """Test report generation with error status"""
        evaluation_results = {
            "check_timestamp": "2025-09-25T10:00:00+07:00",
            "issues_analyzed": 0,
            "compliance_summary": {},
            "violations_by_rule": {},
            "violations": [],
            "compliant_issues": [],
            "status": "error",
            "error": "Failed to connect to GitHub API"
        }

        report_json = github_report_generator_tool(evaluation_results)
        report = json.loads(report_json)

        compliance_report = report["github_compliance_report"]
        assert compliance_report["status"] == "error"
        assert "error" in compliance_report

    def test_generate_summary_report(self):
        """Test summary report generation"""
        evaluation_results = {
            "issues_analyzed": 15,
            "compliance_summary": {
                "compliant_issues": 5,
                "issues_with_violations": 10,
                "total_violations": 18,
                "compliance_rate": 33.33
            },
            "violations_by_rule": {
                "rule_1_empty_assignees": 3,
                "rule_7_no_recent_updates": 4
            },
            "status": "completed"
        }

        result = generate_summary_report(evaluation_results)
        assert "GitHub Issue Compliance Report" in result
        assert "Issues Analyzed: 15" in result
        assert "Compliance Rate: 33.33%" in result
        assert "Rule 1 Empty Assignees: 3" in result
        assert "Status: completed" in result

    def test_report_json_validity(self):
        """Test that generated report is valid JSON"""
        evaluation_results = {
            "check_timestamp": "2025-09-25T10:00:00+07:00",
            "issues_analyzed": 5,
            "compliance_summary": {
                "compliant_issues": 3,
                "issues_with_violations": 2,
                "total_violations": 4,
                "compliance_rate": 60.0
            },
            "violations_by_rule": {
                "rule_1_empty_assignees": 2,
                "rule_3_empty_due_date": 2
            },
            "violations": [
                {
                    "rule_id": 1,
                    "rule_name": "Empty Assignees",
                    "severity": "medium",
                    "issue_number": 101,
                    "issue_title": "Test Issue with Special Chars: \"quotes\" and 'apostrophes'",
                    "issue_url": "https://github.com/test/101",
                    "violation_details": "Issue has no assignees",
                    "assignees": [],
                    "repository": "test-repo"
                }
            ],
            "compliant_issues": [],
            "status": "completed"
        }

        report_json = github_report_generator_tool(evaluation_results)

        # Should not raise JSONDecodeError
        report = json.loads(report_json)
        assert isinstance(report, dict)
        assert "github_compliance_report" in report

        # Re-serialize should work
        json.dumps(report)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])