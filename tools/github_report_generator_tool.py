"""
GitHub Issue Compliance Report Generator Tool

Tool that formats compliance evaluation results into terminal-friendly JSON output
with comprehensive reporting features.

Author:
    Ghozy Ghulamul Afif (ghozy.g.afif@gdplabs.id)
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from gllm_agents.utils import LoggerManager
from gllm_plugin.tools import tool_plugin
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = LoggerManager().get_logger(__name__)


# -------------------------
# Utility Functions
# -------------------------

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


# -------------------------
# Tool Schema
# -------------------------

class ReportGeneratorInput(BaseModel):
    """Input schema for the report generator tool"""
    evaluation_results: Dict[str, Any] = Field(
        ...,
        description="Results from compliance evaluator tool"
    )
    project_id: str = Field(
        default="GDP-ADMIN/223",
        description="GitHub project identifier"
    )
    execution_start_time: Optional[float] = Field(
        default=None,
        description="Start time of execution (Unix timestamp)"
    )
    execution_end_time: Optional[float] = Field(
        default=None,
        description="End time of execution (Unix timestamp)"
    )
    format_type: str = Field(
        default="comprehensive",
        description="Report format type: 'comprehensive' or 'summary'"
    )


@tool_plugin(version="1.0.0")
class GithubReportGeneratorTool(BaseTool):
    """
    Format compliance evaluation results into comprehensive terminal-friendly JSON reports.
    Supports multiple output formats and provides actionable recommendations.
    """
    name: str = "github_report_generator_tool"
    description: str = "Generate comprehensive JSON reports from GitHub compliance evaluation results."
    args_schema: type[BaseModel] = ReportGeneratorInput

    def _run(
        self,
        evaluation_results: Dict[str, Any],
        project_id: str = "GDP-ADMIN/223",
        execution_start_time: Optional[float] = None,
        execution_end_time: Optional[float] = None,
        format_type: str = "comprehensive",
        **_: Any
    ) -> Dict[str, Any]:
        try:
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

            if format_type == "summary":
                # Return brief summary format
                result = {
                    "summary_report": {
                        "project": project_id,
                        "check_timestamp": check_timestamp,
                        "execution_time": execution_time,
                        "issues_analyzed": evaluation_results.get("issues_analyzed", 0),
                        "compliance_rate": f"{compliance_summary.get('compliance_rate', 0)}%",
                        "total_violations": compliance_summary.get("total_violations", 0),
                        "violations_by_rule": violations_by_rule,
                        "status": evaluation_results.get("status", "completed")
                    }
                }
            else:
                # Create comprehensive report structure
                result = {
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
                if format_type == "summary":
                    result["summary_report"]["error"] = evaluation_results["error"]
                else:
                    result["github_compliance_report"]["error"] = evaluation_results["error"]

            logger.info(f"Report generated: {format_type} format for {evaluation_results.get('issues_analyzed', 0)} issues")
            return result

        except Exception as e:
            logger.error(f"Report generator error: {e}")
            return {"error": f"❌ Report generator error: {str(e)}"}

    def generate_json_string(
        self,
        evaluation_results: Dict[str, Any],
        project_id: str = "GDP-ADMIN/223",
        execution_start_time: Optional[float] = None,
        execution_end_time: Optional[float] = None
    ) -> str:
        """
        Generate formatted JSON string for terminal output (backward compatibility)
        """
        try:
            result = self._run(
                evaluation_results=evaluation_results,
                project_id=project_id,
                execution_start_time=execution_start_time,
                execution_end_time=execution_end_time,
                format_type="comprehensive"
            )
            return json.dumps(result, indent=2, ensure_ascii=False, sort_keys=False)
        except Exception as e:
            return json.dumps({"error": f"Report generation failed: {str(e)}"}, indent=2)