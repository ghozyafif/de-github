#!/usr/bin/env python3
"""
GitHub Issue Compliance Report Generator Tool

Self-contained GLLM Plugin tool that formats compliance evaluation results
into terminal-friendly JSON output.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional


def format_execution_time(start_time: float, end_time: float) -> str:
    """Format execution time in human-readable format"""
    elapsed = end_time - start_time
    if elapsed < 60:
        return f"{elapsed:.1f} seconds"
    elif elapsed < 3600:
        minutes = int(elapsed / 60)
        seconds = int(elapsed % 60)
        return f"{minutes} minutes {seconds} seconds"
    else:
        hours = int(elapsed / 3600)
        minutes = int((elapsed % 3600) / 60)
        return f"{hours} hours {minutes} minutes"


def group_violations_by_issue(violations: List[Dict]) -> Dict[int, List[Dict]]:
    """Group violations by issue number for better organization"""
    grouped = {}
    for violation in violations:
        issue_num = violation.get("issue_number")
        if issue_num not in grouped:
            grouped[issue_num] = []
        grouped[issue_num].append(violation)
    return grouped


def calculate_severity_distribution(violations: List[Dict]) -> Dict[str, int]:
    """Calculate distribution of violations by severity"""
    distribution = {"high": 0, "medium": 0, "low": 0}
    for violation in violations:
        severity = violation.get("severity", "medium")
        if severity in distribution:
            distribution[severity] += 1
    return distribution


def generate_issue_summary(issue_violations: List[Dict]) -> Dict[str, Any]:
    """Generate summary for a specific issue with violations"""
    if not issue_violations:
        return {}

    first_violation = issue_violations[0]
    return {
        "issue_number": first_violation.get("issue_number"),
        "issue_title": first_violation.get("issue_title"),
        "issue_url": first_violation.get("issue_url"),
        "repository": first_violation.get("repository"),
        "assignees": first_violation.get("assignees", []),
        "violation_count": len(issue_violations),
        "violations": [
            {
                "rule_id": v.get("rule_id"),
                "rule_name": v.get("rule_name"),
                "severity": v.get("severity"),
                "details": v.get("violation_details")
            }
            for v in issue_violations
        ]
    }


def generate_recommendations(violations_by_rule: Dict[str, int]) -> List[str]:
    """Generate actionable recommendations based on violations"""
    recommendations = []

    if violations_by_rule.get("rule_1_empty_assignees", 0) > 0:
        recommendations.append("🔴 Assign team members to unassigned issues immediately")

    if violations_by_rule.get("rule_2_empty_incoming_date", 0) > 0:
        recommendations.append("📅 Update missing 'Incoming Date' fields for proper tracking")

    if violations_by_rule.get("rule_3_empty_due_date", 0) > 0:
        recommendations.append("⏰ Set 'Due Date' for all issues to manage timelines")

    if violations_by_rule.get("rule_4_empty_status", 0) > 0:
        recommendations.append("📊 Ensure all issues have valid status values")

    if violations_by_rule.get("rule_5_missing_approval_overdue", 0) > 0:
        recommendations.append("✅ URGENT: Get Pak On's approval for overdue issues")

    if violations_by_rule.get("rule_6_due_soon_warning", 0) > 0:
        recommendations.append("⚠️ Review issues due within 7 days for completion")

    if violations_by_rule.get("rule_7_no_recent_updates", 0) > 0:
        recommendations.append("💬 Add status updates to stale issues (>7 days)")

    return recommendations


def github_report_generator_tool(
    evaluation_results: Dict[str, Any],
    project_id: str = "GDP-ADMIN/223",
    execution_start_time: Optional[float] = None,
    execution_end_time: Optional[float] = None
) -> str:
    """
    Main GLLM Plugin tool function for report generation

    Args:
        evaluation_results: Results from compliance evaluator tool
        project_id: GitHub project identifier
        execution_start_time: Start time of execution (for timing)
        execution_end_time: End time of execution (for timing)

    Returns:
        Formatted JSON string for terminal output
    """
    # Calculate execution time
    if execution_start_time and execution_end_time:
        execution_time = format_execution_time(execution_start_time, execution_end_time)
    else:
        execution_time = "Not measured"

    # Extract key data
    violations = evaluation_results.get("violations", [])
    violations_by_rule = evaluation_results.get("violations_by_rule", {})
    compliance_summary = evaluation_results.get("compliance_summary", {})
    compliant_issues = evaluation_results.get("compliant_issues", [])
    check_timestamp = evaluation_results.get("check_timestamp", datetime.now().isoformat())

    # Group violations by issue
    grouped_violations = group_violations_by_issue(violations)

    # Calculate severity distribution
    severity_distribution = calculate_severity_distribution(violations)

    # Generate recommendations
    recommendations = generate_recommendations(violations_by_rule)

    # Build issue summaries
    issue_summaries = []
    for issue_num, issue_violations in sorted(grouped_violations.items()):
        summary = generate_issue_summary(issue_violations)
        if summary:
            issue_summaries.append(summary)

    # Create the comprehensive report structure
    report = {
        "github_compliance_report": {
            "metadata": {
                "project": project_id,
                "check_timestamp": check_timestamp,
                "execution_time": execution_time,
                "report_version": "1.0.0",
                "timezone": "Asia/Jakarta (UTC+7)"
            },
            "summary": {
                "issues_analyzed": evaluation_results.get("issues_analyzed", 0),
                "compliant_issues": compliance_summary.get("compliant_issues", 0),
                "issues_with_violations": compliance_summary.get("issues_with_violations", 0),
                "total_violations": compliance_summary.get("total_violations", 0),
                "compliance_rate": f"{compliance_summary.get('compliance_rate', 0)}%"
            },
            "violations_overview": {
                "by_rule": violations_by_rule,
                "by_severity": severity_distribution,
                "critical_issues": len([v for v in violations if v.get("severity") == "high"])
            },
            "detailed_violations": issue_summaries,
            "compliant_issues": [
                {
                    "issue_number": issue.get("issue_number"),
                    "title": issue.get("title"),
                    "status": issue.get("status"),
                    "assignees": issue.get("assignees", [])
                }
                for issue in compliant_issues[:5]  # Show first 5 compliant issues
            ],
            "recommendations": recommendations,
            "status": evaluation_results.get("status", "completed")
        }
    }

    # Add error information if present
    if "error" in evaluation_results:
        report["github_compliance_report"]["error"] = evaluation_results["error"]

    # Format as pretty JSON for terminal display
    return json.dumps(report, indent=2, ensure_ascii=False, sort_keys=False)


def generate_summary_report(evaluation_results: Dict[str, Any]) -> str:
    """
    Generate a brief summary report (alternative format)

    Args:
        evaluation_results: Results from compliance evaluator tool

    Returns:
        Brief text summary for quick viewing
    """
    compliance_summary = evaluation_results.get("compliance_summary", {})
    violations_by_rule = evaluation_results.get("violations_by_rule", {})

    lines = [
        "=" * 60,
        "GitHub Issue Compliance Report",
        "=" * 60,
        f"Issues Analyzed: {evaluation_results.get('issues_analyzed', 0)}",
        f"Compliance Rate: {compliance_summary.get('compliance_rate', 0)}%",
        f"Total Violations: {compliance_summary.get('total_violations', 0)}",
        "",
        "Violations by Rule:",
    ]

    for rule, count in violations_by_rule.items():
        if count > 0:
            rule_name = rule.replace("_", " ").title()
            lines.append(f"  - {rule_name}: {count}")

    lines.extend([
        "",
        "Status: " + evaluation_results.get("status", "completed"),
        "=" * 60
    ])

    return "\n".join(lines)


# For direct testing
if __name__ == "__main__":
    # Test with sample evaluation results
    test_results = {
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

    # Generate and print report
    report = github_report_generator_tool(test_results, execution_start_time=0, execution_end_time=87)
    print(report)

    # Also test summary format
    print("\n" + generate_summary_report(test_results))