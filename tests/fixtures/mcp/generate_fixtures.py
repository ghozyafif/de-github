#!/usr/bin/env python3
import json
import os
from datetime import datetime, timedelta
import random

def generate_issue_detail(issue_num, status, start_date, incoming_date=None):
    """Generate issue detail fixture"""
    assignee = f"developer{issue_num % 20 + 1}"

    if status == "Todo":
        status_id = f"todo_{issue_num % 100:02d}"
    elif status == "In Progress":
        status_id = f"progress_{issue_num % 100:02d}"
    elif status == "In Review":
        status_id = f"review_{issue_num % 100:02d}"
    else:
        status_id = f"done_{issue_num % 100:02d}"

    data = {
        "result": {
            "data": {
                "id": f"I_kwDOL-78q8_{status.lower().replace(' ', '_')}_{issue_num}",
                "assignees": [assignee],
                "number": issue_num,
                "body": f"Issue body for #{issue_num}",
                "state": "OPEN" if status != "Done" else "CLOSED",
                "closed_at": None,
                "closed_by": None,
                "labels": ["automated-test"],
                "milestone": None,
                "project_details": {
                    "project_items": [
                        {
                            "id": f"PVTI_{status.lower().replace(' ', '_')}_{issue_num:03d}",
                            "type": "ISSUE",
                            "created_at": incoming_date.isoformat() + "+00:00" if incoming_date else start_date.isoformat() + "+00:00",
                            "updated_at": datetime.now().isoformat() + "+00:00",
                            "field_values": [
                                {
                                    "name": "Status",
                                    "value": status,
                                    "field_type": "single_select",
                                    "option_id": status_id
                                }
                            ]
                        }
                    ],
                    "projects": [
                        {
                            "id": "PVT_kwDOACQejc4AvWAd",
                            "number": 223,
                            "title": "GL SDK Project Board",
                            "url": "https://github.com/orgs/GDP-ADMIN/projects/223"
                        }
                    ]
                },
                "author": assignee,
                "created_at": incoming_date.isoformat() + "+00:00" if incoming_date else start_date.isoformat() + "+00:00",
                "updated_at": datetime.now().isoformat() + "+00:00",
                "title": f"Test issue #{issue_num}",
                "url": f"https://github.com/GDP-ADMIN/dummy-gl-sdk/issues/{issue_num}",
                "repository": {
                    "name": "dummy-gl-sdk",
                    "owner": "GDP-ADMIN"
                },
                "comments": random.randint(1, 5)
            }
        }
    }

    # Add date fields based on status
    if incoming_date:
        data["result"]["data"]["project_details"]["project_items"][0]["field_values"].append({
            "name": "Incoming Date",
            "value": incoming_date.strftime("%Y-%m-%dT00:00:00"),
            "field_type": "date"
        })

    if status in ["In Progress", "In Review", "Done"]:
        data["result"]["data"]["project_details"]["project_items"][0]["field_values"].append({
            "name": "Start date",
            "value": start_date.strftime("%Y-%m-%dT00:00:00"),
            "field_type": "date"
        })

    return data

def generate_comments(issue_num, num_comments, last_comment_date):
    """Generate comments fixture with mix of human and bot comments"""
    comments = []
    current_date = last_comment_date - timedelta(days=num_comments * 2)

    for i in range(num_comments):
        is_bot = random.random() < 0.3  # 30% chance of bot comment

        if is_bot:
            username = random.choice(["github-actions[bot]", "dependabot[bot]", "renovate[bot]"])
            body = random.choice([
                "This issue has been automatically marked as stale.",
                "Dependencies updated successfully.",
                "CI checks passed.",
                "Automated security scan completed."
            ])
            user_type = "Bot"
        else:
            username = f"developer{random.randint(1, 20)}"
            body = random.choice([
                "Working on this issue now.",
                "Need clarification on requirements.",
                "PR is ready for review.",
                "Fixed the reported issue.",
                "Blocked by dependency issue.",
                "Will update once testing is complete."
            ])
            user_type = "User"

        comment = {
            "url": f"https://api.github.com/repos/GDP-ADMIN/dummy-gl-sdk/issues/comments/{issue_num*100+i}",
            "html_url": f"https://github.com/GDP-ADMIN/dummy-gl-sdk/issues/{issue_num}#issuecomment-{issue_num*100+i}",
            "issue_url": f"https://api.github.com/repos/GDP-ADMIN/dummy-gl-sdk/issues/{issue_num}",
            "id": issue_num * 100 + i,
            "user": {
                "login": username,
                "type": user_type
            },
            "created_at": current_date.isoformat() + "Z",
            "updated_at": current_date.isoformat() + "Z",
            "body": body,
            "author_association": "MEMBER" if user_type == "User" else "NONE"
        }

        comments.append(comment)
        current_date += timedelta(days=1, hours=random.randint(0, 12))

    return {"result": {"data": comments}}

# Generate remaining issue details and comments
base_date = datetime(2025, 9, 25)

# Already created 101 manually, generate rest
issues_config = [
    # Todo issues (102-105)
    (102, "Todo", base_date - timedelta(days=7)),
    (103, "Todo", base_date - timedelta(days=3)),
    (104, "Todo", base_date - timedelta(days=15)),  # Violation: >5 days old
    (105, "Todo", base_date - timedelta(days=2)),

    # In Progress issues (201-205)
    (201, "In Progress", base_date - timedelta(days=10)),  # Violation: >8 days
    (202, "In Progress", base_date - timedelta(days=15)),  # Violation: >8 days
    (203, "In Progress", base_date - timedelta(days=7)),
    (204, "In Progress", base_date - timedelta(days=20)),  # Violation: >8 days
    (205, "In Progress", base_date - timedelta(days=3)),

    # In Review issues (301-305)
    (301, "In Review", base_date - timedelta(days=15)),  # Violation: >5 days
    (302, "In Review", base_date - timedelta(days=10)),  # Violation: >5 days
    (303, "In Review", base_date - timedelta(days=7)),   # Violation: >5 days
    (304, "In Review", base_date - timedelta(days=13)),  # Violation: >5 days
    (305, "In Review", base_date - timedelta(days=5)),
]

for issue_num, status, date in issues_config:
    # Generate issue detail
    issue_data = generate_issue_detail(issue_num, status, date)
    filename = f"github_get_issue_handler_{issue_num}.json"

    with open(filename, 'w') as f:
        json.dump(issue_data, f, indent=2)

    # Generate comments
    # Some issues will have old comments to trigger comment frequency violations
    if issue_num in [104, 201, 301]:  # These will have stale comments
        last_comment = base_date - timedelta(days=5)  # Violation: >3 days
    else:
        last_comment = base_date - timedelta(days=1)

    num_comments = random.randint(1, 5)
    comments_data = generate_comments(issue_num, num_comments, last_comment)

    comments_filename = f"github_list_issues_comments_{issue_num}.json"
    with open(comments_filename, 'w') as f:
        json.dump(comments_data, f, indent=2)

print("Fixtures generated successfully!")