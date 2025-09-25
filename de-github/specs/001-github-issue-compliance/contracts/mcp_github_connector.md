# MCP GitHub Projects v2 Connector Contract

## Required Capabilities

### github_list_project_items

**Description**: Retrieves all items from a GitHub Project with field values and content details.

**MCP Parameters**:

```json
{
  "response_fields": [
    "id",
    "type",
    "status",
    "content.title",
    "content.number",
    "content.url",
    "content.repository",
    "content.assignees",
    "field_values",
    "updated_at"
  ],
  "organization": "GDP-ADMIN",
  "number": 223,
  "per_page": 100,
  "page": 1,
  "force_new": false,
  "type": "ISSUE",
  "filters": [
    {
      "field_name": "Status",
      "type": "string",
      "value": "In Progress"
    }
  ],
  "summarize": false
}
```

**Expected Response Structure**:

```json
{
  "result": {
    "data": [
      {
        "id": "PVTI_lADOACQejc4AvWAdzge62Wc",
        "type": "ISSUE",
        "title": "Issue Title",
        "status": "In Progress",
        "content": {
          "title": "Issue Title",
          "body": "Issue description",
          "number": 534,
          "state": "OPEN",
          "url": "https://github.com/GDP-ADMIN/dummy-gl-sdk/issues/534",
          "labels": [],
          "assignees": ["michellshandaka", "widardi"],
          "milestone": null,
          "repository": "dummy-gl-sdk"
        },
        "field_values": [
          {
            "name": "Status",
            "value": "In Progress",
            "field_type": "single_select",
            "option_id": "47fc9ee4"
          },
          {
            "name": "Incoming Date",
            "value": "2025-05-14T00:00:00",
            "field_type": "date"
          },
          {
            "name": "Due Date",
            "value": "2025-09-26T00:00:00",
            "field_type": "date"
          },
          {
            "name": "Pak On's Approval for Timeline",
            "value": "Approved",
            "field_type": "single_select",
            "option_id": "a05671de"
          }
        ],
        "created_at": "2025-08-22T03:56:41+00:00",
        "updated_at": "2025-09-19T11:55:54+00:00"
      }
    ],
    "meta": {
      "total": 627,
      "has_next": true
    }
  }
}
```

### github_get_issue_handler

**Description**: Retrieves detailed information for a specific GitHub issue including project field values.

**MCP Parameters**:

```json
{
  "owner": "GDP-ADMIN",
  "repo": "glchat",
  "issue_number": 2231
}
```

**Expected Response Structure**:

```json
{
  "result": {
    "data": {
      "id": "I_kwDOL-78q862hghs",
      "assignees": ["kevin-yauris", "arkalisa-gl"],
      "number": 2231,
      "title": "[Parent Backlog] GLChat - Guardrail Implementation",
      "body": "Issue description content",
      "state": "OPEN",
      "url": "https://github.com/GDP-ADMIN/glchat/issues/2231",
      "closed_at": null,
      "closed_by": null,
      "labels": null,
      "milestone": null,
      "repository": {
        "name": "glchat",
        "owner": "GDP-ADMIN"
      },
      "created_at": "2025-08-22T03:56:41Z",
      "updated_at": "2025-09-19T11:55:54Z",
      "project_details": {
        "project_items": [
          {
            "id": "PVTI_lADOACQejc4AvWAdzgd59Hg",
            "type": "ISSUE",
            "created_at": "2025-08-22T03:56:41+00:00",
            "updated_at": "2025-09-19T11:55:54+00:00",
            "field_values": [
              {
                "name": "Title",
                "value": "[Parent Backlog] GLChat - Guardrail Implementation ",
                "field_type": "text"
              },
              {
                "name": "Status",
                "value": "In Progress",
                "field_type": "single_select",
                "option_id": "47fc9ee4"
              },
              {
                "name": "Incoming Date",
                "value": "2025-05-14T00:00:00",
                "field_type": "date"
              },
              {
                "name": "Due Date",
                "value": "2025-09-26T00:00:00",
                "field_type": "date"
              },
              {
                "name": "Pak On's Approval for Timeline",
                "value": "Approved",
                "field_type": "single_select",
                "option_id": "b12345cd"
              }
            ]
          }
        ],
        "projects": [
          {
            "number": 223,
            "title": "Development Tracking"
          }
        ]
      }
    }
  }
}
```

### github_list_issues_comments

**Description**: Retrieves all comments for a specific GitHub issue with timestamps and authors for Rule #7 evaluation.

**MCP Parameters**:

```json
{
  "owner": "GDP-ADMIN",
  "repo": "glchat",
  "issue_number": 2231
}
```

**Expected Response**:

```json
{
  "result": {
    "data": [
      {
        "url": "https://api.github.com/repos/GDP-ADMIN/glchat/issues/comments/3034218560",
        "html_url": "https://github.com/GDP-ADMIN/glchat/issues/2231#issuecomment-3034218560",
        "issue_url": "https://api.github.com/repos/GDP-ADMIN/glchat/issues/2231",
        "id": 3034218560,
        "node_id": "IC_kwDOL-78q8602oBA",
        "user": {
          "login": "arkalisa-gl",
          "id": 165311029,
          "node_id": "U_kgDOCdpyNQ",
          "avatar_url": "https://avatars.githubusercontent.com/u/165311029?v=4",
          "url": "https://api.github.com/users/arkalisa-gl",
          "html_url": "https://github.com/arkalisa-gl",
          "type": "User",
          "site_admin": false
        },
        "created_at": "2025-07-04T02:21:56Z",
        "updated_at": "2025-07-04T02:21:56Z",
        "body": "1. PM has decided to prioritize Phrase and Topic Guardrail...",
        "author_association": "MEMBER",
        "reactions": {
          "url": "https://api.github.com/repos/GDP-ADMIN/glchat/issues/comments/3034218560/reactions",
          "total_count": 0,
          "+1": 0,
          "-1": 0,
          "laugh": 0,
          "hooray": 0,
          "confused": 0,
          "heart": 0,
          "rocket": 0,
          "eyes": 0
        },
        "performed_via_github_app": null
      }
    ],
    "meta": {
      "page": 1,
      "limit": 30,
      "total": 7,
      "total_page": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

## Required Scopes

The GitHub token used by the MCP connector must have the following scopes:

- `project:read` - Read GitHub Projects v2 data
- `repo:read` - Read repository issues and comments (read-only access)
- `read:org` - Read organization project data (if applicable)

## Field Mapping Requirements

The connector must handle field_values array parsing and provide consistent field access by name:

- Field names are case-sensitive and must match exactly: "Status", "Incoming Date", "Due Date", "Pak On's Approval for Timeline"
- Date fields should be returned as ISO 8601 strings (format: "YYYY-MM-DDTHH:mm:ss" or "YYYY-MM-DDTHH:mm:ss+00:00")
- Single select fields should return the selected option value as string with optional `option_id`
- Missing/empty fields should be returned as null or excluded from field_values array

### Status Field Values

- Valid values: "In Progress", "In Review", "Todo" (exact case-sensitive match)
- Invalid/empty status triggers Rule #4 violation

### Pak On's Approval for Timeline Field Values

- Valid approved values: "Approved"
- Valid other values: "Other Action Items", "Rejected", "Pending"
- Empty/missing values: null, "", "Blank" (triggers Rule #5 when combined with overdue condition)

## Filter Structure

For `github_list_project_items`, the filters array supports the following structure:

```json
{
  "filters": [
    {
      "field_name": "Status",
      "type": "string",
      "value": "In Progress"
    },
    {
      "field_name": "Due Date",
      "type": "date_range",
      "value": {
        "start": "2025-01-01T00:00:00",
        "end": "2025-12-31T23:59:59"
      }
    }
  ]
}
```
