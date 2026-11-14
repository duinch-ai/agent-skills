"""GitHub-specific API helpers (GraphQL/REST via the `gh` CLI). Every call goes through runner.run_gh."""
import json
import time

from ..specs import parse_backlog_issue_map
from ..store import save_json
from .runner import run_gh


def get_rate_limit_info():
    """Query GitHub API rate limit status without consuming quota."""
    rc, out, _ = run_gh(["gh", "api", "rate_limit"], check=False)
    if rc != 0:
        return None
    try:
        res = json.loads(out).get("resources", {})
        core = res.get("core", {})
        gql = res.get("graphql", {})
        return {
            "core_remaining": core.get("remaining", 0),
            "core_limit": core.get("limit", 5000),
            "core_reset": core.get("reset", 0),
            "gql_remaining": gql.get("remaining", 0),
            "gql_limit": gql.get("limit", 5000),
            "gql_reset": gql.get("reset", 0),
        }
    except Exception:
        return None


def get_project_fields(config, cache, cache_path):
    """Return cached Project field IDs or fetch once via lightweight GraphQL."""
    fields = cache.get("fields")
    if fields and fields.get("status_field_id") and fields.get("status_options"):
        return (
            fields["status_field_id"],
            fields["status_options"],
            fields.get("phase_field_id"),
            fields.get("phase_options", {}),
        )

    project_id = config.get("project_id")
    if not project_id:
        raise ValueError("Missing project_id in config. Run `project_board.py init` or set in .agents/task-board.json")

    query = f"""
    query {{
      node(id: "{project_id}") {{
        ... on ProjectV2 {{
          fields(first: 20) {{
            nodes {{
              ... on ProjectV2SingleSelectField {{
                id
                name
                options {{ id name }}
              }}
            }}
          }}
        }}
      }}
    }}
    """
    rc, out, err = run_gh(["gh", "api", "graphql", "-f", f"query={query}"], check=False)
    if rc != 0:
        raise RuntimeError(err or out)

    nodes = json.loads(out)["data"]["node"]["fields"]["nodes"]
    status_field = next((f for f in nodes if f and f.get("name") in ("Status", "status")), None)
    if not status_field:
        raise RuntimeError("Status field not found on GitHub Project")
    phase_field = next((f for f in nodes if f and f.get("name") in ("Phase", "phase", "Priority")), None)

    parsed = {
        "status_field_id": status_field["id"],
        "status_options": {opt["name"]: opt["id"] for opt in status_field["options"]},
        "phase_field_id": phase_field["id"] if phase_field else None,
        "phase_options": {opt["name"].split(" ")[0]: opt["id"] for opt in phase_field["options"]} if phase_field else {},
        "cached_at": int(time.time()),
    }
    cache["fields"] = parsed
    save_json(cache_path, cache)
    return parsed["status_field_id"], parsed["status_options"], parsed["phase_field_id"], parsed["phase_options"]


def resolve_project_item_id(task_id, config, cache, cache_path):
    """Resolve ProjectV2Item ID for task_id using cache first, then 1-point issue lookup."""
    items_cache = cache.setdefault("items", {})
    if task_id in items_cache and items_cache[task_id].get("item_id"):
        return items_cache[task_id]["item_id"]

    issue_num = parse_backlog_issue_map(config.get("backlog_doc")).get(task_id)
    owner, repo, project_id = config.get("owner"), config.get("repo"), config.get("project_id")
    if issue_num and owner and repo and project_id:
        query = f"""
        query {{
          repository(owner: "{owner}", name: "{repo}") {{
            issue(number: {issue_num}) {{
              id
              projectItems(first: 5) {{
                nodes {{
                  id
                  project {{ id }}
                }}
              }}
            }}
          }}
        }}
        """
        rc, out, _ = run_gh(["gh", "api", "graphql", "-f", f"query={query}"], check=False)
        if rc == 0:
            data = json.loads(out).get("data", {}).get("repository", {}).get("issue")
            if data:
                for node in data.get("projectItems", {}).get("nodes", []):
                    if node.get("project", {}).get("id") == project_id:
                        items_cache[task_id] = {"item_id": node["id"], "issue_number": issue_num}
                        save_json(cache_path, cache)
                        return node["id"]
    return None


def set_status(config, cache, cache_path, task_id, target_status, exit_on_invalid=True):
    """Mutation: set the Status single-select of a task's project item."""
    project_id = config.get("project_id")
    if not project_id:
        raise RuntimeError("Missing project_id in config")
    field_id, options, _, _ = get_project_fields(config, cache, cache_path)
    if target_status not in options:
        if not exit_on_invalid:
            raise KeyError(target_status)
        raise SystemExit(f"Invalid status '{target_status}'. Valid options: {list(options.keys())}")
    item_id = resolve_project_item_id(task_id, config, cache, cache_path)
    if not item_id:
        raise RuntimeError(f"Item ID for {task_id} not cached and remote lookup unavailable")
    mutation = f"""
    mutation {{
      updateProjectV2ItemFieldValue(input: {{
        projectId: "{project_id}"
        itemId: "{item_id}"
        fieldId: "{field_id}"
        value: {{ singleSelectOptionId: "{options[target_status]}" }}
      }}) {{
        projectV2Item {{ id }}
      }}
    }}
    """
    rc, _, err = run_gh(["gh", "api", "graphql", "-f", f"query={mutation}"], check=False)
    if rc != 0:
        raise RuntimeError(err)


def create_issue(config, header, content, phase_code):
    """REST issue creation (separate quota). Returns (rc, url, err)."""
    owner, repo = config.get("owner"), config.get("repo")
    cmd = ["gh", "issue", "create", "--title", header, "--body", content]
    if owner and repo:
        cmd.extend(["--repo", f"{owner}/{repo}"])
    if phase_code:
        cmd.extend(["--label", phase_code])
    return run_gh(cmd, check=False)


def attach_issue(config, cache, cache_path, task_id, issue_url, phase_code, board_status, issue_num=None):
    """Add an existing issue to the project, record the item id, set Status (+ Phase if known)."""
    project_id = config.get("project_id")
    if not project_id:
        raise RuntimeError("Missing project_id in config")
    status_field_id, status_options, phase_field_id, phase_options = get_project_fields(config, cache, cache_path)
    fields = "id" if issue_num is not None else "id,number"
    _, issue_json, _ = run_gh(["gh", "issue", "view", issue_url, "--json", fields])
    issue_data = json.loads(issue_json)
    issue_node_id = issue_data["id"]
    if issue_num is None:
        issue_num = issue_data.get("number")

    add_q = f"""
    mutation {{
      addProjectV2ItemById(input: {{ projectId: "{project_id}", contentId: "{issue_node_id}" }}) {{
        item {{ id }}
      }}
    }}
    """
    _, add_out, _ = run_gh(["gh", "api", "graphql", "-f", f"query={add_q}"])
    item_id = json.loads(add_out)["data"]["addProjectV2ItemById"]["item"]["id"]
    cache.setdefault("items", {})[task_id] = {"item_id": item_id, "issue_number": issue_num}
    save_json(cache_path, cache)

    muts = [
        f"""setStatus: updateProjectV2ItemFieldValue(input: {{
            projectId: "{project_id}", itemId: "{item_id}", fieldId: "{status_field_id}",
            value: {{ singleSelectOptionId: "{status_options[board_status]}" }}
        }}) {{ projectV2Item {{ id }} }}"""
    ]
    if phase_field_id and phase_options and phase_code in phase_options:
        muts.append(
            f"""setPhase: updateProjectV2ItemFieldValue(input: {{
                projectId: "{project_id}", itemId: "{item_id}", fieldId: "{phase_field_id}",
                value: {{ singleSelectOptionId: "{phase_options[phase_code]}" }}
            }}) {{ projectV2Item {{ id }} }}"""
        )
    run_gh(["gh", "api", "graphql", "-f", f"query=mutation {{ {' '.join(muts)} }}"])
