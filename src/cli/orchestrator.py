#!/usr/bin/env python3
"""GitHub Issue Compliance Agent Orchestrator.

Test harness for running the compliance agent workflow.
This simulates the background agent execution flow.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.compliance_evaluator import github_compliance_evaluator_tool
from src.services.report_generator import github_report_generator_tool


def load_fixture_data(fixture_dir: Path) -> tuple[List[Dict], Dict[int, List[Dict]]]:
    """Load fixture data for testing.

    Returns:
        Tuple of (issues, comments_by_issue)
    """
    issues = []
    comments_by_issue = {}

    # Load issue lists (5 per status)
    statuses = ["todo", "in_progress", "in_review"]
    for status in statuses:
        list_file = fixture_dir / f"github_list_project_items_{status}_5.json"
        if list_file.exists():
            with open(list_file) as f:
                data = json.load(f)
                issues.extend(data["result"]["data"])

    # Load comments for each issue
    issue_numbers = [101, 102, 103, 104, 105, 201, 202, 203, 204, 205, 301, 302, 303, 304, 305]
    for issue_num in issue_numbers:
        comments_file = fixture_dir / f"github_list_issues_comments_{issue_num}.json"
        if comments_file.exists():
            with open(comments_file) as f:
                data = json.load(f)
                comments_by_issue[issue_num] = data["result"]["data"]
        else:
            comments_by_issue[issue_num] = []

    return issues, comments_by_issue


def simulate_mcp_calls(project_id: str) -> tuple[List[Dict], Dict[int, List[Dict]]]:
    """Simulate MCP calls to GitHub API.

    OPTIMIZED: Uses only list_project_items + comments (18 total calls)
    In production, these would be actual MCP connector calls

    Returns:
        Tuple of (issues, comments_by_issue)
    """
    print("📊 Simulating optimized MCP calls to GitHub API...")
    print(f"   Project: {project_id}")
    print("   Pattern: 3 list calls + 15 comment calls = 18 total (45% reduction)")

    # In test mode, load from fixtures
    fixture_dir = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "mcp"
    if fixture_dir.exists():
        print("   Loading from test fixtures...")
        return load_fixture_data(fixture_dir)

    # In production, would make actual MCP calls here
    print("   ⚠️ No fixtures found - would make real MCP calls in production")
    return [], {}


def run_compliance_evaluation(
    issues: List[Dict],
    comments_by_issue: Dict[int, List[Dict]],
    current_date: Optional[str] = None
) -> Dict[str, Any]:
    """Run the compliance evaluation.

    Args:
        issues: List of GitHub issues
        comments_by_issue: Comments mapped by issue number
        current_date: Current date for testing (YYYY-MM-DD)

    Returns:
        Evaluation results
    """
    print("\n🔍 Running compliance evaluation...")
    print(f"   Issues to analyze: {len(issues)}")

    start_time = time.time()

    # Run compliance evaluation
    results = github_compliance_evaluator_tool(
        issues=issues,
        comments_by_issue=comments_by_issue,
        current_date_str=current_date
    )

    end_time = time.time()
    elapsed = end_time - start_time

    print(f"   Evaluation complete in {elapsed:.2f} seconds")
    print(f"   Violations found: {results['compliance_summary']['total_violations']}")
    print(f"   Compliance rate: {results['compliance_summary']['compliance_rate']}%")

    return results


def generate_terminal_report(
    evaluation_results: Dict[str, Any],
    project_id: str,
    start_time: float,
    end_time: float
) -> str:
    """Generate the terminal report.

    Args:
        evaluation_results: Results from compliance evaluation
        project_id: GitHub project identifier
        start_time: Workflow start time
        end_time: Workflow end time

    Returns:
        JSON report string
    """
    print("\n📝 Generating terminal report...")

    report = github_report_generator_tool(
        evaluation_results=evaluation_results,
        project_id=project_id,
        execution_start_time=start_time,
        execution_end_time=end_time
    )

    return report


def main():
    """Main orchestration workflow.

    Simulates the background agent execution.
    """
    print("=" * 60)
    print("GitHub Issue Compliance Agent - Background Mode")
    print("=" * 60)

    # Configuration
    project_id = "GDP-ADMIN/223"
    current_date = "2025-09-25"  # For testing

    # Start workflow
    workflow_start = time.time()

    try:
        # Step 1: Fetch issues from GitHub (simulated via fixtures)
        issues, comments_by_issue = simulate_mcp_calls(project_id)

        if not issues:
            print("\n❌ No issues found to analyze")
            sys.exit(1)

        # Step 2: Run compliance evaluation
        evaluation_results = run_compliance_evaluation(
            issues=issues,
            comments_by_issue=comments_by_issue,
            current_date=current_date
        )

        # Step 3: Generate terminal report
        report_json = generate_terminal_report(
            evaluation_results=evaluation_results,
            project_id=project_id,
            start_time=workflow_start,
            end_time=time.time()
        )

        # Step 4: Output to terminal
        print("\n" + "=" * 60)
        print("TERMINAL OUTPUT (JSON)")
        print("=" * 60)
        print(report_json)
        print("=" * 60)

        # Step 5: Exit (background mode)
        print("\n✅ Agent execution complete - exiting")
        sys.exit(0)

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"\n❌ Error during execution: {e}")

        # Generate error report
        error_results = {
            "status": "error",
            "error": str(e),
            "issues_analyzed": 0,
            "compliance_summary": {},
            "violations_by_rule": {},
            "violations": [],
            "compliant_issues": []
        }

        error_report = github_report_generator_tool(
            evaluation_results=error_results,
            project_id=project_id,
            execution_start_time=workflow_start,
            execution_end_time=time.time()
        )

        print("\n" + "=" * 60)
        print("ERROR REPORT")
        print("=" * 60)
        print(error_report)
        print("=" * 60)

        sys.exit(1)


if __name__ == "__main__":
    main()
