"""Scaffold rehearse.yaml from a target URL."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import yaml


def _slug_from_url(url: str) -> str:
    host = urlparse(url).netloc or "app"
    slug = re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-")
    return slug or "app"


def _product_name(url: str, name: str | None) -> str:
    if name:
        return name
    host = urlparse(url).netloc or url
    return host.replace("www.", "").split(".")[0].title()


def build_config(
    target_url: str,
    *,
    product_name: str | None = None,
    run_id_prefix: str | None = None,
    with_auth: bool = False,
    crawl_enabled: bool = True,
    exclude_path_prefixes: list[str] | None = None,
    viewports: list[str] | None = None,
) -> dict:
    base = target_url.rstrip("/")
    prefix = run_id_prefix or _slug_from_url(base)
    product = _product_name(base, product_name)

    from rehearse.viewports import normalize_viewports

    cfg: dict = {
        "run": {
            "target_url": base,
            "run_id_prefix": prefix,
            "product_name": product,
            "viewports": normalize_viewports(viewports or ["desktop"]),
        },
        "crawl": {
            "enabled": crawl_enabled,
            "max_depth": 2,
            "max_pages": 30,
            "supplement_journeys": True,
        },
    }
    if exclude_path_prefixes:
        cfg["crawl"]["exclude_path_prefixes"] = list(exclude_path_prefixes)
    cfg["personas"] = [
            {
                "id": "p1-evaluator",
                "name": "First-time evaluator",
                "role": "prospect / new user",
                "goals": ["Understand value from landing and primary workflow"],
                "enabled": True,
            },
            {
                "id": "p2-operator",
                "name": "Daily operator",
                "role": "power user",
                "goals": ["Complete core tasks quickly and reliably"],
                "enabled": True,
            },
            {
                "id": "p3-admin",
                "name": "Admin / buyer",
                "role": "IT admin",
                "goals": ["Verify access boundaries and trust signals"],
                "enabled": True,
            },
            {
                "id": "p4-keyboard",
                "name": "Keyboard-only user",
                "role": "accessibility tester / screen reader user",
                "goals": ["Complete all primary journeys using only Tab, Enter, and arrow keys"],
                "enabled": False,
                "keyboard_only": True,
                "tech_literacy": "expert",
                "patience": "high",
                "character": "Uses assistive technology. Navigates entirely by keyboard. Never uses a mouse.",
                "usage_context": "Relies on keyboard navigation due to motor impairment",
            },
            {
                "id": "p5-frustrated",
                "name": "Frustrated / rage user",
                "role": "churning customer",
                "goals": ["Attempt the core task but give up if blocked more than once"],
                "enabled": False,
                "patience": "low",
                "trust_level": "skeptical",
                "character": "Has failed at this task before. Quick to give up. Rage-clicks if confused. Files mental support tickets.",
                "usage_context": "Returning user who hit a bug last week and is trying again",
            },
            {
                "id": "p6-international",
                "name": "International / RTL user",
                "role": "global user on a right-to-left locale",
                "goals": ["Complete signup and primary workflow", "Verify no layout breaks in RTL"],
                "enabled": False,
                "locale": "ar-SA",
                "tech_literacy": "intermediate",
                "character": "Uses the product in Arabic. Expects RTL layout. Notices text overflow and mirroring bugs.",
                "usage_context": "Saudi Arabian market user, first-time evaluation",
            },
    ]
    cfg["journeys"] = [
            {
                "id": "j1-land",
                "name": "Land on primary surface",
                "steps": [{"action": "navigate", "url": f"{base}/"}, {"action": "wait", "value": "2000"}],
            },
            {
                "id": "j2-core",
                "name": "Core workflow",
                "steps": [{"action": "navigate", "url": f"{base}/"}, {"action": "wait", "value": "2000"}],
            },
            {
                "id": "j3-depth",
                "name": "Secondary module",
                "steps": [{"action": "navigate", "url": f"{base}/"}, {"action": "wait", "value": "1500"}],
            },
            {
                "id": "j4-search",
                "name": "Search or discovery",
                "steps": [{"action": "navigate", "url": f"{base}/"}, {"action": "wait", "value": "1500"}],
            },
            {
                "id": "j5-admin",
                "name": "Admin or settings boundary",
                "steps": [{"action": "navigate", "url": f"{base}/admin"}, {"action": "wait", "value": "1500"}],
            },
    ]
    cfg["budgets"] = {
        "max_steps_per_journey": 20,
        "max_run_seconds": 28800,
        "step_timeout_ms": 45000,
    }

    if with_auth:
        cfg["auth"] = {
            "login_path": "/login",
            "email_env": "REHEARSE_EMAIL",
            "password_env": "REHEARSE_PASSWORD",
            "email_label": "Email",
            "password_label": "Password",
            "submit_label": "Login",
        }
        cfg["journeys"][0]["steps"] = [
            {"action": "navigate", "url": f"{base}/database"},
            {"action": "wait", "value": "2000"},
        ]

    return cfg


def build_self_dashboard_config(
    target_url: str = "http://127.0.0.1:8081",
    *,
    product_name: str = "Launch Rehearsal Dashboard",
) -> dict:
    """Config for dogfooding: crawl + journey the monitoring UI itself."""
    base = target_url.rstrip("/")
    cfg = build_config(
        base,
        product_name=product_name,
        run_id_prefix="lr-self",
        crawl_enabled=True,
    )
    cfg["run"]["allow_localhost"] = True
    cfg["crawl"]["max_pages"] = 24
    cfg["crawl"]["max_depth"] = 2
    cfg["crawl"]["exclude_path_prefixes"] = ["/runs/", "/api/"]
    cfg["run"]["viewports"] = ["desktop", "tablet", "mobile"]
    cfg["budgets"]["max_steps_per_journey"] = 48
    cfg["journeys"] = [
        {
            "id": "j1-command-center",
            "name": "Command center",
            "steps": [
                {"action": "navigate", "url": f"{base}/"},
                {"action": "wait", "value": "2500"},
            ],
        },
        {
            "id": "j2-runs",
            "name": "Runs list",
            "steps": [
                {"action": "navigate", "url": f"{base}/runs"},
                {"action": "wait", "value": "2000"},
            ],
        },
        {
            "id": "j3-compare",
            "name": "Compare runs",
            "steps": [
                {"action": "navigate", "url": f"{base}/compare"},
                {"action": "wait", "value": "2000"},
            ],
        },
        {
            "id": "j4-init-dogfood",
            "name": "Init dogfood flow",
            "steps": [
                {"action": "navigate", "url": f"{base}/init"},
                {"action": "wait", "value": "1500"},
                {"action": "click", "intent": f"Use {base}"},
                {"action": "click", "intent": "Preflight HEAD"},
                {"action": "wait", "value": "1500"},
            ],
        },
        {
            "id": "j5-runner",
            "name": "Runner page (observe only — no self-trigger)",
            "steps": [
                {"action": "navigate", "url": f"{base}/runner"},
                {"action": "wait", "value": "2000"},
                {"action": "assert_url_contains", "value": "/runner"},
            ],
        },
        {
            "id": "j6-trends",
            "name": "Trends monitoring",
            "steps": [
                {"action": "navigate", "url": f"{base}/trends"},
                {"action": "wait", "value": "2000"},
            ],
        },
    ]
    return cfg


def write_config(path: Path, config: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# Generated by: rehearse init\n"
        "# Edit journeys to match your product — see examples/enterprise-authenticated.yaml\n\n"
    )
    path.write_text(header + yaml.dump(config, default_flow_style=False, sort_keys=False))
    return path
