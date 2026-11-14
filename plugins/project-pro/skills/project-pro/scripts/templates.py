"""Facade: template renderers live in `agents_md`, `rules`, `ci`, `hooks` and `docs`."""

from __future__ import annotations

from agents_md import render_agents_md
from ci import render_cpp_switch_ci_workflow, render_rust_ci_workflow
from docs import render_adr, render_editorconfig
from hooks import render_commit_msg_hook, render_pre_commit_hook, render_pre_push_hook
from rules import (
    render_category_rule,
    render_data_rule,
    render_domain_rule,
    render_execution_harness_rule,
    render_i18n_rule,
    render_presentation_rule,
    render_security_rule,
)

__all__ = [
    "render_adr", "render_agents_md", "render_category_rule", "render_commit_msg_hook", "render_cpp_switch_ci_workflow",
    "render_data_rule", "render_domain_rule", "render_editorconfig", "render_execution_harness_rule", "render_i18n_rule",
    "render_pre_commit_hook", "render_pre_push_hook", "render_presentation_rule", "render_rust_ci_workflow",
    "render_security_rule",
]
