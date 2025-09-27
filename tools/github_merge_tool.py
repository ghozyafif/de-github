"""
Custom tool to merge multiple `github_list_project_items` responses
into a unique list of issues (dedup by repo+number), fast & deterministic.

Author:
    Ghozy Ghulamul Afif (ghozy.g.afif@gdplabs.id)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from gllm_agents.utils import LoggerManager
from gllm_plugin.tools import tool_plugin
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, validator

logger = LoggerManager().get_logger(__name__)


# -------------------------
# Helpers
# -------------------------

def _safe_list_items(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract `result.data` list safely from list-items response."""
    if not isinstance(resp, dict):
        return []
    result = resp.get("result")
    if not isinstance(result, dict):
        return []
    data = result.get("data")
    if isinstance(data, list):
        return data
    return []

def _extract_minimal(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Pull minimal fields needed for downstream steps.
    Shape expected per github_list_project_items response:
      item = {
        "type": "ISSUE",
        "content": {"repository": str, "number": int, "title": str, "url": str, "assignees": [...]},
        "status": str,
        "field_values": [...]
      }
    """
    if not isinstance(item, dict):
        return None
    if item.get("type") != "ISSUE":
        return None

    content = item.get("content") or {}
    repo = content.get("repository")
    number = content.get("number")
    if repo is None or number is None:
        return None

    return {
        "repo": repo,
        "number": number,
        "title": content.get("title"),
        "url": content.get("url"),
        "assignees": content.get("assignees") or [],
        "status": item.get("status"),
        # keep raw field_values for later (e.g., Incoming Date / Due Date)
        "field_values": item.get("field_values") or [],
        "updated_at": item.get("updated_at"),
    }


# -------------------------
# Tool Schema
# -------------------------

class MergeInput(BaseModel):
    """Input schema for the merge tool."""
    mcp_list_payload_results: List[Dict[str, Any]] = Field(
        ...,
        description=(
            "List of RAW responses from `github_list_project_items` "
            "(e.g., for statuses In Progress, Todo, In Review). "
            "Each element must contain `result.data` array."
        )
    )
    include_index_map: bool = Field(
        default=False,
        description="If true, returns a map keyed by '<repo>#<number>' -> issue object."
    )
    include_counts: bool = Field(
        default=True,
        description="If true, returns total_count and unique_count."
    )

    @validator("mcp_list_payload_results")
    def _non_empty(cls, v):
        if not v:
            raise ValueError("mcp_list_payload_results must not be empty")
        return v


@tool_plugin(version="1.0.0")
class GithubMergeTool(BaseTool):
    """
    Merge multiple list-items responses and deduplicate by (repo, number).
    Intended to be called by gh_merge_agent to speed up the merge step.
    """
    name: str = "github_merge_tool"
    description: str = "Merge `github_list_project_items` responses, dedup by repo+number, and return a compact list."
    args_schema: type[BaseModel] = MergeInput

    def _run(
        self,
        mcp_list_payload_results: List[Dict[str, Any]],
        include_index_map: bool = False,
        include_counts: bool = True,
        **_: Any
    ) -> Dict[str, Any]:
        try:
            # Stream over all responses
            total = 0
            index: Dict[str, Dict[str, Any]] = {}  # key: "repo#number" -> minimal issue
            order: List[str] = []  # keep stable order of first appearance

            for resp in mcp_list_payload_results:
                items = _safe_list_items(resp)
                total += len(items)
                for it in items:
                    mini = _extract_minimal(it)
                    if not mini:
                        continue
                    key = f"{mini['repo']}#{mini['number']}"
                    if key in index:
                        # Already seen: keep first-seen record (deterministic & fast)
                        continue
                    index[key] = mini
                    order.append(key)

            merged_list = [index[k] for k in order]

            result: Dict[str, Any] = {
                "merged_data": merged_list
            }
            if include_index_map:
                result["index_map"] = index
            if include_counts:
                result["total_count"] = total
                result["unique_count"] = len(merged_list)

            logger.info(
                f"Merged {total} items from {len(mcp_list_payload_results)} responses "
                f"into {len(merged_list)} unique issues."
            )

            # Document the response format explicitly to reduce hallucination downstream:
            result["_schema"] = {
                "response_format": {
                    "merged_data": [
                        {
                            "repo": "string",
                            "number": 0,
                            "title": "string",
                            "url": "string",
                            "assignees": ["string"],
                            "status": "string",
                            "field_values": [
                                {"name": "string", "value": "any", "field_type": "string"}
                            ],
                            "updated_at": "ISO-8601 string"
                        }
                    ],
                    "index_map?": {"<repo>#<number>": "<issue_object>"},
                    "total_count?": "int",
                    "unique_count?": "int"
                }
            }

            return result

        except Exception as e:
            logger.error(f"Merge error: {e}")
            return {"error": f"❌ Merge error: {str(e)}"}
