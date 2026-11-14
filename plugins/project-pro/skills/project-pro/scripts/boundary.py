"""Dispatch `boundary_config` renderers named in the stack data; stacks without one report "not yet automated"."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import boundary_go
import boundary_py


def generate_boundary_config(target: Path, stack: str, arch: str, info: dict[str, Any], go_module: str | None = None) -> list[str]:
    renderer = info.get("boundary_config")
    if renderer == "go-depguard":
        return boundary_go.generate(target, arch, info, go_module)
    if renderer == "python-importlinter":
        return boundary_py.generate(target, arch, info)
    return [f"NOTE: boundary config not yet automated for stack `{stack}` (only go and python today)."]
