"""Journey DSL loader and validation."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from rehearse.errors import ConfigError

MIN_PERSONAS = 3
MIN_JOURNEYS = 5
ALLOWED_ACTIONS = frozenset(
    {
        "navigate",
        "click",
        "fill",
        "wait",
        "hover",
        "scroll",
        "select",
        "press",
        "assert_url_contains",
        "open_link",
        "explore",
        "dismiss",
    }
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
    persona_ids: list[str] = field(default_factory=list)  # empty = runs for all personas


@dataclass
class Persona:
    id: str
    name: str
    role: str
    goals: list[str]
    enabled: bool = True
    # Behavioral depth — all optional, safe defaults preserve existing behavior
    tech_literacy: str = "intermediate"  # "novice" | "intermediate" | "expert"
    patience: str = "medium"             # "low" | "medium" | "high"
    trust_level: str = "neutral"         # "skeptical" | "neutral" | "trusting"
    character: str = ""                  # free-text psychological texture
    usage_context: str = ""              # "first-time user", "switching from X", etc.
    # Accessibility / environment modifiers
    keyboard_only: bool = False          # navigate via Tab/Enter — no mouse
    locale: str | None = None           # e.g. "ar-SA" for RTL, "ja-JP" for CJK
    network_throttle: str | None = None  # "slow3g" | "offline_intermittent" | None
    rage_mode: bool = False              # after step failure: retry click 3x rapidly to surface duplicate-submit bugs
    screen_reader: bool = False          # navigate via ARIA tree only — no CSS selectors, no coordinates


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
    exclude_path_prefixes: list[str] = field(default_factory=list)


@dataclass
class ExperimentSpec:
    """Optional pre-ship experiment metadata (L3-PRED-02)."""

    hypothesis: str = ""
    user_goal: str = ""
    variant_label: str = ""


@dataclass
class Budgets:
    max_steps_per_journey: int = 30
    max_run_seconds: int = 7200  # 2 hours — was 30 min, not enough for multi-persona runs
    step_timeout_ms: int = 30000
    parallel_seeds: int = 1
    repeat_micro_loop: int = 1
    explore_max_rounds: int = 3
    parallel_journeys: int = 1  # concurrent journey workers (each gets own browser context)


@dataclass
class RunConfig:
    target_url: str
    run_id_prefix: str
    product_name: str
    personas: list[Persona]
    journeys: list[Journey]
    budgets: Budgets = field(default_factory=Budgets)
    experiment: ExperimentSpec | None = None
    auth: AuthConfig | None = None
    crawl: CrawlConfig | None = field(default_factory=CrawlConfig)
    allow_localhost: bool = False
    viewports: list[str] = field(default_factory=lambda: ["desktop"])
    execute_all_personas_in_browser: bool = False
    persona_lens: bool = True
    product_type: str = "b2b_saas"

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
    if len(personas_raw) < MIN_PERSONAS:
        raise ConfigError(f"Expected at least {MIN_PERSONAS} personas, got {len(personas_raw)}")
    if len(journeys_raw) < MIN_JOURNEYS:
        raise ConfigError(f"Expected at least {MIN_JOURNEYS} journeys, got {len(journeys_raw)}")

    personas = [
        Persona(
            id=p["id"],
            name=p["name"],
            role=p["role"],
            goals=list(p.get("goals") or []),
            enabled=bool(p.get("enabled", True)),
            tech_literacy=str(p.get("tech_literacy") or "intermediate"),
            patience=str(p.get("patience") or "medium"),
            trust_level=str(p.get("trust_level") or "neutral"),
            character=str(p.get("character") or ""),
            usage_context=str(p.get("usage_context") or ""),
            keyboard_only=bool(p.get("keyboard_only", False)),
            locale=str(p["locale"]) if p.get("locale") else None,
            network_throttle=str(p["network_throttle"]) if p.get("network_throttle") else None,
            rage_mode=bool(p.get("rage_mode", False)),
            screen_reader=bool(p.get("screen_reader", False)),
        )
        for p in personas_raw
    ]
    journeys = [
        Journey(
            id=j["id"],
            name=j["name"],
            steps=[_parse_step(s) for s in j.get("steps") or []],
            persona_ids=list(j.get("persona_ids") or []),
        )
        for j in journeys_raw
    ]

    b = data.get("budgets") or {}
    budgets = Budgets(
        max_steps_per_journey=int(b.get("max_steps_per_journey", 30)),
        max_run_seconds=int(b.get("max_run_seconds", 7200)),
        step_timeout_ms=int(b.get("step_timeout_ms", 30000)),
        parallel_seeds=max(1, int(b.get("parallel_seeds", 1))),
        repeat_micro_loop=max(1, int(b.get("repeat_micro_loop", 1))),
        explore_max_rounds=max(1, int(b.get("explore_max_rounds", 3))),
        parallel_journeys=max(1, min(10, int(b.get("parallel_journeys", 1)))),
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
            exclude_path_prefixes=list(crawl_raw.get("exclude_path_prefixes") or []),
        )

    from rehearse.viewports import normalize_viewports

    exp_raw = data.get("experiment")
    experiment = None
    if isinstance(exp_raw, dict) and exp_raw:
        experiment = ExperimentSpec(
            hypothesis=str(exp_raw.get("hypothesis") or "").strip(),
            user_goal=str(exp_raw.get("user_goal") or exp_raw.get("userGoal") or "").strip(),
            variant_label=str(
                exp_raw.get("variant_label") or exp_raw.get("variantLabel") or ""
            ).strip(),
        )

    cfg = RunConfig(
        target_url=str(target_url).rstrip("/"),
        run_id_prefix=str(run_id_prefix),
        product_name=str(product_name),
        personas=personas,
        journeys=journeys,
        budgets=budgets,
        experiment=experiment,
        auth=auth,
        crawl=crawl,
        allow_localhost=bool(run.get("allow_localhost", False)),
        viewports=normalize_viewports(run.get("viewports")),
        execute_all_personas_in_browser=bool(run.get("execute_all_personas_in_browser", False)),
        persona_lens=bool(run.get("persona_lens", True)),
        product_type=str(run.get("product_type", "b2b_saas")),
    )
    cfg.materialize_steps()
    return cfg


def active_personas(config: RunConfig) -> list[Persona]:
    """Personas used for matrix grading and persona agents (L2-UI-70)."""
    if not config.persona_lens:
        return []
    return [p for p in config.personas if p.enabled]
