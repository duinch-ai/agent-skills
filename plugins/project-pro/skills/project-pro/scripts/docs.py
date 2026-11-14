"""ADR and editorconfig renderers."""

from __future__ import annotations

import datetime as dt
from typing import Any


def render_adr(name: str, info: dict[str, Any], arch: str, pattern: str, repo: str, repo_url: str, features: list[str]) -> str:
    today = dt.date.today().isoformat()
    feat_list = "\n".join(f"- `{f}`" for f in features) if features else "- `solid-dry`"
    return f"""# ADR-0001: Project Base Architecture, Security Gates & Multi-Agent Standards

- **Date**: {today} | **Status**: Accepted | **Project**: {name} | **Stack**: {info['label']}

## Decision
- **Architecture Style**: `{arch}` | **Flow Pattern**: `{pattern}`
- **Reference Architecture Anchor**: [`{repo}`]({repo_url})
- **Boundary Enforcement**: {info['boundary_tool']}
- **File Size Policy**: `1 File = 1 Primary Responsibility`, warn at `300 LOC`, hard block at `450 LOC`.
- **Security & Git Gates**: Staged secret scanning, OWASP heuristics, Conventional Commits, and pre-push test/CVE verification via `.githooks/`.

### Selected Base Capabilities
{feat_list}
"""


def render_editorconfig() -> str:
    return """root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 4

[*.{js,jsx,ts,tsx,vue,json,yaml,yml,md,dart,html,css,scss}]
indent_size = 2

[*.go]
indent_style = tab

[Makefile]
indent_style = tab
"""
