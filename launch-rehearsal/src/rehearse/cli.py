"""CLI: rehearse run | crawl | scorecard"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import click

from rehearse.browser import BrowserSession
from rehearse.context import RunContext
from rehearse.crawler import crawl_site
from rehearse.dsl import load_config
from rehearse.errors import RehearseError
from rehearse.evidence import RunEvidence, new_run_id
from rehearse.heuristics import analyze_run
from rehearse.preflight import preflight_head
from rehearse.runner import run_rehearsal
from rehearse.scorecard import write_scorecard
from rehearse.sitemap import SiteMap
from rehearse.workflows import detect_workflows


@click.group()
def main() -> None:
    """Launch Rehearsal — enterprise E2E monitoring and feedback."""
    from rehearse.env_loader import load_dotenv_files

    load_dotenv_files()


@main.command("run")
@click.option("--config", "-c", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", default="artifacts", type=click.Path(path_type=Path))
@click.option("--dry-run", is_flag=True, help="Preflight + DSL validation only; no browser")
@click.option("--no-crawl", is_flag=True, help="Skip site crawl phase")
@click.option("--run-id", default=None, help="Pre-assigned run ID (used by server job worker)")
@click.option(
    "--llm",
    is_flag=True,
    help="LLM persona analysis (NVIDIA NIM or OpenAI-compatible API via env)",
)
@click.option(
    "--fail-on-gate",
    is_flag=True,
    help="Exit non-zero if the launch gate is CAUTION or BLOCKED (for CI/CD use)",
)
def run_cmd(
    config: Path,
    output: Path,
    dry_run: bool,
    no_crawl: bool,
    run_id: str | None,
    llm: bool,
    fail_on_gate: bool,
) -> None:
    """Crawl (optional), execute journeys, multi-agent analysis, scorecard."""
    try:
        from rehearse.env_loader import load_dotenv_files
        from rehearse.llm import llm_enabled, llm_provider

        load_dotenv_files(start=config.parent)
        cfg = load_config(config)
        if llm and not llm_enabled():
            click.echo(
                "Warning: --llm set but no API key found. Set DEEPSEEK_API_KEY, "
                "NVIDIA_NIM_API_KEY, or OPENAI_API_KEY.",
                err=True,
            )
        elif llm or llm_enabled():
            click.echo(f"LLM provider: {llm_provider()}")
        if no_crawl and cfg.crawl:
            cfg.crawl.enabled = False
        probe = preflight_head(cfg.target_url, allow_localhost=cfg.allow_localhost)
        click.echo(f"Preflight OK: {probe['url']} ({probe['status_code']})")

        if dry_run:
            click.echo(f"Product: {cfg.product_name}")
            click.echo(f"Personas: {len(cfg.personas)} | Journeys: {len(cfg.journeys)}")
            click.echo(f"Crawl: {'on' if cfg.crawl and cfg.crawl.enabled else 'off'}")
            evidence, _, _ = run_rehearsal(cfg, output_dir=output, dry_run=True)
            click.echo(f"Dry run complete. run_id={evidence.run_id}")
            return

        evidence, scorecard_path, ctx = run_rehearsal(cfg, output_dir=output, dry_run=False, use_llm=llm, config_path=config, run_id=run_id)
        analysis = ctx.synthesis if ctx else analyze_run(cfg, evidence)

        # The Gate (PASS/REVIEW/CAUTION/BLOCKED) lives in the analysis bundle,
        # written by run_rehearsal() to output/analysis/{run_id}.json — read it
        # back so the CLI surfaces the actual verdict, not just the legacy
        # Green/Amber/Red band computed before the bundle exists.
        bundle_path = output / "analysis" / f"{evidence.run_id}.json"
        launch_gate: str | None = None
        verdict: str | None = None
        readiness_score: int | None = None
        flake_rate: float | None = None
        if bundle_path.is_file():
            try:
                bundle_summary = json.loads(bundle_path.read_text()).get("summary", {})
                launch_gate = bundle_summary.get("launchGate")
                verdict = bundle_summary.get("verdict")
                readiness_score = bundle_summary.get("readiness")
                flake_rate = bundle_summary.get("flakeRate")
            except Exception:
                pass

        result = {
            "run_id": evidence.run_id,
            "outcome": evidence.outcome,
            "launch_gate": launch_gate,
            "verdict": verdict,
            "readiness_score": readiness_score,
            "readiness_band": analysis.readiness,
            "flake_rate": flake_rate,
            "issues": len(analysis.issues),
            "delights": len(analysis.delights),
            "pages_crawled": len(ctx.sitemap.pages) if ctx and ctx.sitemap else 0,
            "agents": len(ctx.agent_reports) if ctx else 0,
            "llm_enabled": llm,
            "scorecard": str(scorecard_path) if scorecard_path else None,
            "sitemap": (
                str(output / "sitemaps" / f"{evidence.run_id}-sitemap.md")
                if ctx and ctx.sitemap
                else None
            ),
            "evidence": str(output / "runs" / f"{evidence.run_id}.json"),
            "bundle": str(bundle_path) if bundle_path.is_file() else None,
        }
        click.echo(json.dumps(result, indent=2))
        if launch_gate:
            click.echo(f"\nLaunch Gate: {launch_gate} — {verdict or ''}", err=False)

        # Machine-readable result, written separately from stdout — log lines
        # (preflight, LLM provider, the human Gate echo above) make stdout
        # unsafe to parse as pure JSON. CI tooling should read this file, not
        # scrape stdout.
        try:
            (output / "last-run-result.json").write_text(json.dumps(result, indent=2))
        except Exception:
            pass

        if fail_on_gate and launch_gate in ("CAUTION", "BLOCKED"):
            click.echo(f"\n--fail-on-gate: exiting non-zero (gate={launch_gate})", err=True)
            sys.exit(2)
    except RehearseError as e:
        click.echo(f"Error [{type(e).__name__}]: {e}", err=True)
        sys.exit(1)


@main.command("crawl")
@click.option("--config", "-c", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", default="artifacts", type=click.Path(path_type=Path))
def crawl_cmd(config: Path, output: Path) -> None:
    """Crawl target site only — emit sitemap JSON/Markdown + workflow graph."""
    try:
        cfg = load_config(config)
        if not cfg.crawl:
            cfg.crawl = __import__("rehearse.dsl", fromlist=["CrawlConfig"]).CrawlConfig()
        preflight_head(cfg.target_url, allow_localhost=cfg.allow_localhost)
        run_id = new_run_id(cfg.run_id_prefix)
        artifacts = output / "artifacts" / run_id
        started = time.perf_counter()

        with BrowserSession(cfg, artifacts, record_video=True) as session:
            if cfg.auth:
                session.perform_auth(cfg.auth)
            result = crawl_site(
                session.page,
                cfg.target_url,
                cfg.crawl,
                timeout_ms=cfg.budgets.step_timeout_ms,
            )

        sitemap = SiteMap.from_pages(cfg.target_url, result.pages)
        sitemap.save_json(output / "sitemaps" / f"{run_id}-sitemap.json")
        sitemap.save_markdown(output / "sitemaps" / f"{run_id}-sitemap.md")
        workflows = detect_workflows(sitemap)

        click.echo(
            json.dumps(
                {
                    "run_id": run_id,
                    "pages": len(pages),
                    "workflows": len(workflows.workflows),
                    "suggested_journeys": len(workflows.suggested_journeys),
                    "duration_s": int(time.perf_counter() - started),
                    "sitemap_md": str(output / "sitemaps" / f"{run_id}-sitemap.md"),
                },
                indent=2,
            )
        )
    except RehearseError as e:
        click.echo(f"Error [{type(e).__name__}]: {e}", err=True)
        sys.exit(1)


@main.command("scorecard")
@click.option("--evidence", "-e", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--config", "-c", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", default="artifacts", type=click.Path(path_type=Path))
def scorecard_cmd(evidence: Path, config: Path, output: Path) -> None:
    """Regenerate scorecard markdown from saved evidence JSON."""
    from rehearse.evidence import StepSnapshot

    cfg = load_config(config)
    data = json.loads(evidence.read_text())
    ev = RunEvidence(
        run_id=data["run_id"],
        target_url=data["target_url"],
        product_name=data.get("product_name", cfg.product_name),
        started_at=data["started_at"],
        finished_at=data.get("finished_at"),
        duration_ms=data.get("duration_ms", 0),
        auth_attempted=data.get("auth_attempted", False),
        auth_outcome=data.get("auth_outcome"),
        outcome=data.get("outcome", "complete"),
    )
    ev.steps = [StepSnapshot(**s) for s in data.get("steps", [])]
    analysis = analyze_run(cfg, ev)
    path = write_scorecard(cfg, ev, analysis, output)
    click.echo(f"Scorecard written: {path}")


@main.command("backfill")
@click.option("--output", "-o", default="artifacts", type=click.Path(path_type=Path))
def backfill_cmd(output: Path) -> None:
    """Rebuild analysis.json bundles for runs missing them."""
    from rehearse.dashboard.store import backfill_all

    rebuilt = backfill_all(output.resolve())
    click.echo(json.dumps({"rebuilt": rebuilt, "count": len(rebuilt)}, indent=2))


@main.command("serve")
@click.option("--output", "-o", default="artifacts", type=click.Path(path_type=Path))
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8765, show_default=True, type=int)
def serve_cmd(output: Path, host: str, port: int) -> None:
    """Local monitoring dashboard for runs, scorecards, and diffs."""
    from rehearse.dashboard.server import serve_dashboard
    from rehearse.env_loader import load_dotenv_files

    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    load_dotenv_files(start=output)  # pick up credentials saved via the UI
    serve_dashboard(output, host=host, port=port)


@main.command("init")
@click.argument("url")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Write config YAML to this path")
@click.option("--name", default=None, help="Product display name")
@click.option("--prefix", default=None, help="run_id_prefix")
@click.option("--auth", is_flag=True, help="Include auth block and database deep-link journey")
@click.option("--no-crawl", is_flag=True, help="Disable crawl in generated config")
def init_cmd(
    url: str,
    output: Path | None,
    name: str | None,
    prefix: str | None,
    auth: bool,
    no_crawl: bool,
) -> None:
    """Scaffold a 3-persona / 5-journey YAML from a target URL."""
    from rehearse.init_config import build_config, write_config

    cfg = build_config(
        url,
        product_name=name,
        run_id_prefix=prefix,
        with_auth=auth,
        crawl_enabled=not no_crawl,
    )
    if output is None:
        slug = cfg["run"]["run_id_prefix"]
        output = Path("configs") / f"{slug}.yaml"
    out = write_config(output, cfg)
    click.echo(f"Config written: {out.resolve()}")
    click.echo(f"Next: rehearse run -c {out} -o artifacts")


@main.command("diff")
@click.option("--output", "-o", default="artifacts", type=click.Path(path_type=Path))
@click.argument("run_a")
@click.argument("run_b")
def diff_cmd(output: Path, run_a: str, run_b: str) -> None:
    """Compare two runs (readiness, sitemap, step outcomes)."""
    from rehearse.dashboard.store import diff_runs

    result = diff_runs(output, run_a, run_b)
    click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
