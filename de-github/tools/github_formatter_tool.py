"""
Tool to normalize GitHub issue detail responses (from `github_get_issue_handler`)
and format them into JSON + CSV, aligned with the orchestrator Step 6.

Input: an array of RAW detail responses exactly as returned by `github_get_issue_handler`.
Output: {
  "issues": [ ...normalized rows... ],
  "csv": "repo,number,title,assignees,status,incoming_date,due_date,approval,updated_at,url\n..."
}

Author:
    Ghozy Ghulamul Afif (ghozy.g.afif@gdplabs.id)
"""

from __future__ import annotations

import csv
import io
from typing import Any, Dict, List, Optional

from gllm_agents.utils import LoggerManager
from gllm_plugin.tools import tool_plugin
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = LoggerManager().get_logger(__name__)


# -------------------------
# Helpers
# -------------------------

def _get_field(field_values: List[Dict[str, Any]] | None, name: str) -> Any:
    """Fetch value from field_values by case-insensitive name."""
    if not field_values:
        return None
    name_l = name.strip().lower()
    for fv in field_values:
        if (fv.get("name") or "").strip().lower() == name_l:
            return fv.get("value")
    return None

def _select_project_item_for_number(detail_data: Dict[str, Any], project_number: int) -> Optional[Dict[str, Any]]:
    """
    Try to select the project item that belongs to the target project_number.
    Strategy:
      1) If `project_details.projects` contains the target number, return the first `project_items` entry.
      2) Else, return the first available `project_items` entry (best-effort).
    """
    proj_details = (detail_data.get("project_details") or {})
    proj_items = proj_details.get("project_items") or []
    projects = proj_details.get("projects") or []

    # Check if the target project is linked
    has_target = any(p.get("number") == project_number for p in projects if isinstance(p, dict))
    if has_target and proj_items:
        return proj_items[0]
    # Fallback: first item
    return proj_items[0] if proj_items else None

def _normalize_issue_detail(
    detail_resp: Dict[str, Any],
    target_project_number: int
) -> Dict[str, Any]:
    """
    Normalize a single RAW detail response from `github_get_issue_handler`.
    Expected shape (subset):
        {
          "data": {
            "assignees": [...],
            "number": 123,
            "title": "...",
            "url": "...",
            "state": "OPEN|CLOSED",
            "repository": {"name": "<repo>", "owner": "GDP-ADMIN"},
            "updated_at": "ISO-8601",
            "project_details": {
              "project_items": [ { "field_values": [ { "name": "...", "value": "..."} ] } ],
              "projects": [ { "number": 223, ... } ]
            }
          }
        }
    """
    data = detail_resp.get("data") or {}

    repo = (data.get("repository") or {}).get("name")
    number = data.get("number")
    title = data.get("title")
    url = data.get("url")
    assignees = data.get("assignees") or []
    updated_at = data.get("updated_at")

    proj_item = _select_project_item_for_number(data, target_project_number)
    fv = (proj_item or {}).get("field_values") or []

    status = _get_field(fv, "Status") or data.get("state")
    incoming_date = _get_field(fv, "Incoming Date")
    due_date = _get_field(fv, "Due Date")
    approval = _get_field(fv, "Pak On's Approval for Timeline")

    return {
        "repo": repo,
        "number": number,
        "title": title,
        "url": url,
        "assignees": assignees,
        "status": status,
        "incoming_date": incoming_date,
        "due_date": due_date,
        "approval": approval,
        "updated_at": updated_at,
    }

def _to_csv(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return ""
    headers = ["repo","number","title","assignees","status","incoming_date","due_date","approval","updated_at","url"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    for r in rows:
        writer.writerow({
            "repo": r.get("repo"),
            "number": r.get("number"),
            "title": r.get("title"),
            "assignees": ", ".join(r.get("assignees") or []),
            "status": r.get("status"),
            "incoming_date": r.get("incoming_date"),
            "due_date": r.get("due_date"),
            "approval": r.get("approval"),
            "updated_at": r.get("updated_at"),
            "url": r.get("url"),
        })
    return buf.getvalue()


# -------------------------
# Tool Schema
# -------------------------

class FormatterInput(BaseModel):
    """
    Input schema strictly aligned with orchestrator Step 6.

    issues: array of RAW detail responses from `github_get_issue_handler`.
    project_number: which project we should read field_values from (default: 223).
    include_csv: whether to include the CSV string.
    """
    issues: List[Dict[str, Any]] = Field(
        ...,
        description="List of RAW `github_get_issue_handler` responses (verbatim)."
    )
    project_number: int = Field(
        default=223,
        description="Project number used to select the correct project item for field_values."
    )
    include_csv: bool = Field(default=True, description="If true, include CSV string in the output.")


@tool_plugin(version="2.0.0")
class GithubFormatterTool(BaseTool):
    """
    Normalize RAW issue detail responses (from `github_get_issue_handler`) and output JSON + CSV.
    Designed to be called exactly as in orchestrator Step 6.
    """
    name: str = "github_formatter_tool"
    description: str = "Format RAW issue details (from github_get_issue_handler) into normalized JSON and optional CSV."
    args_schema: type[BaseModel] = FormatterInput

    def _run(
        self,
        issues: List[Dict[str, Any]],
        project_number: int = 223,
        include_csv: bool = True,
        **_: Any
    ) -> Dict[str, Any]:
        try:
            normalized = [
                _normalize_issue_detail(resp, project_number)
                for resp in issues
                if isinstance(resp, dict)
            ]

            result: Dict[str, Any] = {"issues": normalized}
            if include_csv:
                result["csv"] = _to_csv(normalized)

            logger.info(f"Formatter: normalized {len(normalized)} issues for project #{project_number}")
            return result

        except Exception as e:
            logger.error(f"Formatter error: {e}")
            return {"error": f"❌ Formatter error: {str(e)}"}
