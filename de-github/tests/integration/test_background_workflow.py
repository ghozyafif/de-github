#!/usr/bin/env python3
"""
Integration tests for the GitHub Issue Compliance Agent background workflow
"""

import pytest
import json
import time
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock
import subprocess

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.compliance_evaluator import github_compliance_evaluator_tool
from src.services.report_generator import github_report_generator_tool
from src.cli.orchestrator import (
    load_fixture_data,
    simulate_mcp_calls,
    run_compliance_check,
    generate_terminal_report
)


class TestBackgroundWorkflow:
    """Test the complete background workflow"""

    @pytest.fixture
    def fixture_dir(self):
        """Get fixture directory path"""
        return Path(__file__).parent.parent / "fixtures" / "mcp"

    @pytest.fixture
    def sample_issues_and_comments(self, fixture_dir):
        """Load sample issues and comments from fixtures"""
        return load_fixture_data(fixture_dir)

    def test_load_fixture_data(self, fixture_dir):
        """Test loading fixture data"""
        issues, comments_by_issue = load_fixture_data(fixture_dir)

        # Should load 15 issues (5 per status)
        assert len(issues) == 15

        # Should have comments for each issue number
        expected_issue_numbers = [101, 102, 103, 104, 105, 201, 202, 203, 204, 205, 301, 302, 303, 304, 305]
        for issue_num in expected_issue_numbers:
            assert issue_num in comments_by_issue

    def test_complete_workflow_with_fixtures(self, sample_issues_and_comments):
        """Test complete workflow from fixtures to report"""
        issues, comments_by_issue = sample_issues_and_comments

        # Step 1: Run compliance check
        evaluation_results, start_time, end_time = run_compliance_check(
            issues=issues,
            comments_by_issue=comments_by_issue,
            current_date="2025-09-25"
        )

        # Verify evaluation results
        assert evaluation_results["status"] == "completed"
        assert evaluation_results["issues_analyzed"] == 15
        assert "violations_by_rule" in evaluation_results
        assert "compliance_summary" in evaluation_results

        # Step 2: Generate report
        report_json = generate_terminal_report(
            evaluation_results=evaluation_results,
            project_id="GDP-ADMIN/223",
            start_time=start_time,
            end_time=end_time
        )

        # Verify report is valid JSON
        report = json.loads(report_json)
        assert "github_compliance_report" in report
        assert report["github_compliance_report"]["status"] == "completed"

    def test_workflow_execution_time(self, sample_issues_and_comments):
        """Test that workflow completes within target time"""
        issues, comments_by_issue = sample_issues_and_comments

        start = time.time()

        # Run full workflow
        evaluation_results, _, _ = run_compliance_check(
            issues=issues,
            comments_by_issue=comments_by_issue,
            current_date="2025-09-25"
        )

        report_json = generate_terminal_report(
            evaluation_results=evaluation_results,
            project_id="GDP-ADMIN/223",
            start_time=start,
            end_time=time.time()
        )

        elapsed = time.time() - start

        # Should complete within 2 minutes (120 seconds)
        assert elapsed < 120, f"Workflow took {elapsed:.2f} seconds, exceeding 2-minute target"

    def test_workflow_with_missing_data(self):
        """Test workflow handles missing data gracefully"""
        # Create issues with missing fields
        issues = [
            {
                "content": {"number": 999},
                "title": "Issue with missing fields",
                "field_values": []
            }
        ]
        comments = {999: []}

        evaluation_results, start_time, end_time = run_compliance_check(
            issues=issues,
            comments_by_issue=comments,
            current_date="2025-09-25"
        )

        # Should complete even with missing data
        assert evaluation_results["status"] == "completed"
        assert evaluation_results["issues_analyzed"] == 1

        # Should detect violations for missing fields
        assert evaluation_results["violations_by_rule"]["rule_1_empty_assignees"] > 0
        assert evaluation_results["violations_by_rule"]["rule_2_empty_incoming_date"] > 0

    def test_workflow_with_all_compliant_issues(self):
        """Test workflow with fully compliant issues"""
        issues = [
            {
                "content": {
                    "number": 501,
                    "assignees": ["user1", "user2"],
                    "url": "test.com/501",
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
            501: [
                {
                    "user": {"login": "developer1"},
                    "body": "Recent update on the issue",
                    "created_at": "2025-09-24T00:00:00Z"
                }
            ]
        }

        evaluation_results, _, _ = run_compliance_check(
            issues=issues,
            comments_by_issue=comments,
            current_date="2025-09-25"
        )

        assert evaluation_results["compliance_summary"]["compliance_rate"] == 100.0
        assert evaluation_results["compliance_summary"]["issues_with_violations"] == 0
        assert len(evaluation_results["compliant_issues"]) == 1

    def test_simulate_mcp_calls(self):
        """Test MCP call simulation"""
        with patch.object(Path, 'exists', return_value=True):
            issues, comments = simulate_mcp_calls("GDP-ADMIN/223")
            # Should return data when fixtures exist
            assert isinstance(issues, list)
            assert isinstance(comments, dict)

    def test_orchestrator_cli_execution(self, tmp_path):
        """Test the orchestrator CLI can be executed"""
        # Create a test script that imports and runs the orchestrator
        test_script = tmp_path / "test_cli.py"
        test_script.write_text("""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli.orchestrator import main

# Mock sys.exit to prevent actual exit
class MockExit(Exception):
    def __init__(self, code):
        self.code = code

def mock_exit(code):
    raise MockExit(code)

sys.exit = mock_exit

try:
    main()
except MockExit as e:
    print(f"Exit code: {e.code}")
""")

        # Run the test script
        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )

        # Should complete without errors
        assert "GitHub Issue Compliance Agent" in result.stdout
        assert "Exit code: 0" in result.stdout or "Exit code: 1" in result.stdout

    def test_error_handling_in_workflow(self):
        """Test error handling throughout the workflow"""
        # Create malformed issue data
        issues = [
            {"malformed": "data"},  # Missing required fields
            None,  # Null issue
            {
                "content": {"number": "not_a_number"},  # Invalid data type
                "field_values": "not_a_list"  # Wrong structure
            }
        ]
        comments = {}

        # Should handle errors gracefully
        evaluation_results, _, _ = run_compliance_check(
            issues=issues,
            comments_by_issue=comments,
            current_date="2025-09-25"
        )

        # Should return partial results
        assert "status" in evaluation_results
        assert isinstance(evaluation_results.get("violations", []), list)

    def test_terminal_output_format(self, sample_issues_and_comments):
        """Test that terminal output matches expected format"""
        issues, comments_by_issue = sample_issues_and_comments

        evaluation_results, start_time, end_time = run_compliance_check(
            issues=issues,
            comments_by_issue=comments_by_issue,
            current_date="2025-09-25"
        )

        report_json = generate_terminal_report(
            evaluation_results=evaluation_results,
            project_id="GDP-ADMIN/223",
            start_time=start_time,
            end_time=end_time
        )

        # Parse and validate structure
        report = json.loads(report_json)
        compliance_report = report["github_compliance_report"]

        # Check required sections
        assert "metadata" in compliance_report
        assert "summary" in compliance_report
        assert "violations_overview" in compliance_report
        assert "detailed_violations" in compliance_report
        assert "recommendations" in compliance_report

        # Check metadata fields
        metadata = compliance_report["metadata"]
        assert metadata["project"] == "GDP-ADMIN/223"
        assert metadata["timezone"] == "Asia/Jakarta (UTC+7)"
        assert "execution_time" in metadata

        # Check summary fields
        summary = compliance_report["summary"]
        assert "issues_analyzed" in summary
        assert "compliance_rate" in summary

    @pytest.mark.parametrize("status_filter", ["Todo", "In Progress", "In Review"])
    def test_status_filtering(self, fixture_dir, status_filter):
        """Test filtering issues by status"""
        issues, _ = load_fixture_data(fixture_dir)

        # Filter by status
        filtered_issues = [
            i for i in issues
            if any(f.get("name") == "Status" and f.get("value") == status_filter
                   for f in i.get("field_values", []))
        ]

        # Should have 5 issues per status
        assert len(filtered_issues) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])