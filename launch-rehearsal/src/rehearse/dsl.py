"""Journey DSL loader and validation."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from rehearse.errors import ConfigError

REQUIRED_PERSONAS = 3
REQUIRED_JOURNEYS = 5
ALLOWED_ACTIONS = frozenset(
    {"navigate", "click", "fill", "wait", "assert_url_contains", "open_link"}
)

_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


@dataclass
class Step:
    action: str
    url: str | None = None
    intent: str | None = None
    selector: str | None = None
    value: str | None = None

    def resolve_value(self) -> str | None:
        if self.value is None:
            return None
        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            if key not in os.environ:
                raise ConfigError(f"Environment variable not set: {key}")
            return os.environ[key]
        return _ENV_PATTERN.sub(repl, self.value)


@dataclass
class Journey:
    id: str
    name: str
    steps: list[Step]


@dataclass
class Persona:
    id: str
    name: str
    role: str
    goals: list[str]


@dataclass
class AuthConfig:
    login_path: str = "/login"
    email_env: str = "REHEARSE_EMAIL"
    password_env: str = "REHEARSE_PASSWORD"
    email_label: str = "Email"
    password_label: str = "Password"
    submit_label: str = "Login"


@dataclass
class CrawlConfig:
    enabled: bool = True
    max_depth: int = 2
    max_pages: int = 30
    same_origin_only: bool = True
    supplement_journeys: bool = True
    strict_enterprise: bool = False


@dataclass
class Budgets:
    max_steps_per_journey: int = 20
    max_run_seconds: int = 1800
    step_timeout_ms: int = 30000
    parallel_seeds: int = 1
    repeat_micro_loop: int = 1


@dataclass
class RunConfig:
    target_url: str
    run_id_prefix: str
    product_name: str
    personas: list[Persona]
    journeys: list[Journey]
    budgets: Budgets = field(default_factory=Budgets)
    auth: AuthConfig | None = None
    crawl: CrawlConfig | None = field(default_factory=CrawlConfig)

    def materialize_steps(self) -> None:
        base = self.target_url.rstrip("/")
        for journey in self.journeys:
            for step in journey.steps:
                if step.url and "{target_url}" in step.url:
                    step.url = step.url.replace("{target_url}", base)

    def login_url(self) -> str | None:
        if not self.auth:
            return None
        path = self.auth.login_path
        if path.startswith("http"):
            return path.replace("{target_url}", self.target_url.rstrip("/"))
        return f"{self.target_url.rstrip('/')}/{path.lstrip('/')}"


def _parse_step(raw: dict[str, Any]) -> Step:
    action = raw.get("action")
    if not action:
        raise ConfigError("Each step requires 'action'")
    action = str(action)
    if action not in ALLOWED_ACTIONS:
        raise ConfigError(f"Unknown action: {action}. Allowed: {sorted(ALLOWED_ACTIONS)}")
    return Step(
        action=action,
        url=raw.get("url"),
        intent=raw.get("intent"),
        selector=raw.get("selector"),
        value=raw.get("value"),
    )


def load_config(path: Path) -> RunConfig:
    if not path.exists():
        raise ConfigError(f"Config not found: {path}")
    data = yaml.safe_load(path.read_text()) or {}
    run = data.get("run") or {}
    target_url = run.get("target_url")
    if not target_url:
        raise ConfigError("run.target_url is required")
    run_id_prefix = run.get("run_id_prefix") or "run"
    product_name = run.get("product_name") or target_url

    personas_raw = data.get("personas") or []
    journeys_raw = data.get("journeys") or []
    if len(personas_raw) != REQUIRED_PERSONAS:
        raise ConfigError(f"Expected {REQUIRED_PERSONAS} personas, got {len(personas_raw)}")
    if len(journeys_raw) != REQUIRED_JOURNEYS:
        raise ConfigError(f"Expected {REQUIRED_JOURNEYS} journeys, got {len(journeys_raw)}")

    personas = [
        Persona(
            id=p["id"],
            name=p["name"],
            role=p["role"],
            goals=list(p.get("goals") or []),
        )
        for p in personas_raw
    ]
    journeys = [
        Journey(
            id=j["id"],
            name=j["name"],
            steps=[_parse_step(s) for s in j.get("steps") or []],
        )
        for j in journeys_raw
    ]

    b = data.get("budgets") or {}
    budgets = Budgets(
        max_steps_per_journey=int(b.get("max_steps_per_journey", 20)),
        max_run_seconds=int(b.get("max_run_seconds", 1800)),
        step_timeout_ms=int(b.get("step_timeout_ms", 30000)),
        parallel_seeds=max(1, int(b.get("parallel_seeds", 1))),
        repeat_micro_loop=max(1, int(b.get("repeat_micro_loop", 1))),
    )

    auth_raw = data.get("auth")
    auth = None
    if auth_raw:
        auth = AuthConfig(
            login_path=str(auth_raw.get("login_path", "/login")),
            email_env=str(auth_raw.get("email_env", "REHEARSE_EMAIL")),
            password_env=str(auth_raw.get("password_env", "REHEARSE_PASSWORD")),
            email_label=str(auth_raw.get("email_label", "Email")),
            password_label=str(auth_raw.get("password_label", "Password")),
            submit_label=str(auth_raw.get("submit_label", "Login")),
        )

    crawl_raw = data.get("crawl")
    crawl = CrawlConfig()
    if crawl_raw is not None:
        crawl = CrawlConfig(
            enabled=bool(crawl_raw.get("enabled", True)),
            max_depth=int(crawl_raw.get("max_depth", 2)),
            max_pages=int(crawl_raw.get("max_pages", 30)),
            same_origin_only=bool(crawl_raw.get("same_origin_only", True)),
            supplement_journeys=bool(crawl_raw.get("supplement_journeys", True)),
            strict_enterprise=bool(crawl_raw.get("strict_enterprise", False)),
        )

    cfg = RunConfig(
        target_url=str(target_url).rstrip("/"),
        run_id_prefix=str(run_id_prefix),
        product_name=str(product_name),
        personas=personas,
        journeys=journeys,
        budgets=budgets,
        auth=auth,
        crawl=crawl,
    )
    cfg.materialize_steps()
    return cfg
