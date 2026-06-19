"""Local monitoring dashboard HTTP server."""

from __future__ import annotations

import json
import mimetypes
import os
import re
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from rehearse.dashboard.graphml import load_sitemap_graphml
from rehearse.dashboard.jobs import enqueue_cohort_run, enqueue_run, enqueue_variant_run, list_jobs, mark_stale_running_jobs
from rehearse.dashboard.store import (
    backfill_all,
    diff_runs,
    get_alerts,
    get_annotations,
    get_backlog,
    get_init_wizard,
    get_integrations,
    get_journey_library,
    get_run_detail,
    get_command_digest,
    get_trends,
    get_workspace,
    list_configs,
    list_run_summaries,
    list_runs,
    load_bundle,
    run_preflight,
    save_annotation,
    save_config,
    save_workspace,
    search_artifacts,
)

_STATIC_DIR = Path(__file__).resolve().parent / "static"

# --- Auth -------------------------------------------------------------------
# Set REHEARSE_API_TOKEN in .env or environment to require a bearer token on
# every API request. Leave unset for local dev (no auth enforced).
_API_TOKEN: str | None = os.environ.get("REHEARSE_API_TOKEN") or None

# Guards os.environ mutation in /api/product/analyze so per-request API keys
# don't leak into concurrent background job threads.
_api_key_env_lock = threading.Lock()

# --- CORS -------------------------------------------------------------------
# Defaults to localhost dev ports. Set REHEARSE_CORS_ORIGIN to a comma-
# separated list of allowed origins for deployed environments, e.g.:
#   REHEARSE_CORS_ORIGIN=https://trylapse.up.railway.app
_CORS_ORIGINS: set[str] = set(
    o.strip()
    for o in (
        os.environ.get("REHEARSE_CORS_ORIGIN")
        or "http://localhost:8081,http://127.0.0.1:8081,http://localhost:8080,http://127.0.0.1:8080,http://localhost:8082,http://127.0.0.1:8082,http://localhost:8083,http://127.0.0.1:8083"
    ).split(",")
    if o.strip()
)

# Paths that bypass auth (always public)
_PUBLIC_PATHS = {"/api/health", "/", "/auth/login", "/auth/signup", "/auth/me"}

# Only allow alphanumerics, hyphens, and underscores in user-supplied ids.
# This prevents directory traversal via run_id / journey_id / config_id.
_SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]{1,200}$")


def _safe_id(value: str, field: str = "id") -> str:
    """Validate a user-supplied id is safe for file-path construction.

    Raises ValueError if the value contains slashes, dots, or other characters
    that could enable directory traversal.
    """
    if not value or not _SAFE_ID_RE.match(value):
        raise ValueError(f"Invalid {field}: must be alphanumeric/hyphens/underscores (1–200 chars)")
    return value


def _config_prefix_from_path(config_path: str) -> str:
    """Extract the stable product-slug prefix from a config file path.

    Strips the -YYYYMMDD-HHMMSS timestamp suffix so that
    ``faculty-dashboard-eight-vercel-app-20260611-052339.yaml``
    yields ``faculty-dashboard-eight-vercel-app``.

    Used consistently across /api/jobs, /api/summaries, and /api/trends to
    prevent cross-workspace data bleed when two products share a first word.
    """
    stem = Path(config_path).stem
    m = re.match(r"^(.*)-\d{8}-\d{6}$", stem)
    return m.group(1) if m else stem


def _write_cred_env(artifacts_root: Path, email: str, password: str) -> None:
    """Persist REHEARSE_EMAIL/PASSWORD to project-root .env so both _load_env and
    load_dotenv_files pick them up on next restart."""
    import os as _os
    # Strip newlines to prevent .env injection (e.g. email="x\nSECRET=injected")
    email = email.replace("\n", "").replace("\r", "")
    password = password.replace("\n", "").replace("\r", "")
    if email:
        _os.environ["REHEARSE_EMAIL"] = email
    if password:
        _os.environ["REHEARSE_PASSWORD"] = password
    # artifacts_root.parent.parent == project root — the path _load_env checks as candidate 1
    env_path = artifacts_root.parent.parent / ".env"
    lines: list[str] = []
    if env_path.is_file():
        for ln in env_path.read_text().splitlines():
            if not ln.startswith("REHEARSE_EMAIL=") and not ln.startswith("REHEARSE_PASSWORD="):
                lines.append(ln)
    if email:
        lines.append(f"REHEARSE_EMAIL={email}")
    if password:
        lines.append(f"REHEARSE_PASSWORD={password}")
    try:
        env_path.write_text("\n".join(lines) + "\n")
    except Exception:
        pass


def _cors_headers(origin: str | None) -> dict[str, str]:
    """Return CORS headers. Allow the requesting origin if it is in the allowlist."""
    allowed = origin if (origin and origin in _CORS_ORIGINS) else next(iter(_CORS_ORIGINS), "*")
    return {
        "Access-Control-Allow-Origin": allowed,
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Vary": "Origin",
    }


class DashboardServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, server_address: tuple[str, int], artifacts_root: Path) -> None:
        self.artifacts_root = artifacts_root.resolve()
        super().__init__(server_address, _Handler)


def _bind_server(host: str, port: int, artifacts_root: Path) -> tuple[DashboardServer, int]:
    last_err: OSError | None = None
    for attempt in range(20):
        try_port = port + attempt
        try:
            server = DashboardServer((host, try_port), artifacts_root)
            return server, try_port
        except OSError as exc:
            if exc.errno not in (48, 98):
                raise
            last_err = exc
    raise OSError(
        f"Could not bind {host}:{port}–{port + 19}. "
        f"Stop the other process or use --port. Last error: {last_err}"
    ) from last_err


class _Handler(BaseHTTPRequestHandler):
    server: DashboardServer  # type: ignore[assignment]

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    @property
    def _origin(self) -> str | None:
        return self.headers.get("Origin")

    def _send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in _cors_headers(self._origin).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def _send_bytes(self, data: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        for k, v in _cors_headers(self._origin).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, filepath: str, content_type: str) -> None:
        """Stream a file to the client."""
        from pathlib import Path
        path = Path(filepath)
        if not path.is_file():
            self._send_json({"error": "File not found"}, status=404)
            return
        file_size = path.stat().st_size
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(file_size))
        for k, v in _cors_headers(self._origin).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(65536)  # 64KB chunks
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except (BrokenPipeError, IOError):
            pass

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if not length or length > 10_000_000:  # 10 MB hard cap
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _require_jwt(self) -> dict | None:
        """Return JWT payload dict if a valid token is present, else None."""
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        from rehearse.dashboard.auth_store import decode_token
        return decode_token(auth_header[7:])

    def _check_auth(self, path: str) -> bool:
        """Return True if request is authorised. Sends 401 and returns False otherwise."""
        if not _API_TOKEN:
            return True  # auth disabled — local dev
        if path in _PUBLIC_PATHS or path.startswith("/static") or not path.startswith("/api"):
            return True
        # Accept static API token or a valid user JWT
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if token == _API_TOKEN:
                return True
            from rehearse.dashboard.auth_store import decode_token
            if decode_token(token) is not None:
                return True
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if (qs.get("token") or [""])[0] == _API_TOKEN:
            return True
        self._send_json(
            {"error": "Unauthorized — sign in at /auth/login or set Authorization: Bearer <REHEARSE_API_TOKEN>"},
            status=401,
        )
        return False

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        for k, v in _cors_headers(self._origin).items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = urllib.parse.parse_qs(parsed.query)
        root = self.server.artifacts_root

        if path == "/api/health":
            self._send_json({"ok": True, "artifacts": str(root)})
            return

        if path == "/auth/me":
            payload = self._require_jwt()
            if payload:
                self._send_json({
                    "id": payload["sub"],
                    "email": payload["email"],
                    "name": payload["name"],
                })
                return
            self._send_json({"error": "Not authenticated"}, status=401)
            return

        if path == "/api/workspaces/me":
            payload = self._require_jwt()
            if not payload:
                self._send_json({"error": "Authentication required"}, status=401)
                return
            from rehearse.dashboard.workspace_store import get_workspaces_for_user, backfill_config_paths
            workspaces = get_workspaces_for_user(root, payload["sub"])
            # Backfill configPath for workspaces created before this feature
            workspaces = backfill_config_paths(root, workspaces)
            self._send_json(workspaces)
            return

        if not self._check_auth(path):
            return

        if path == "/api/credentials":
            import os as _os
            self._send_json({
                "hasEmail": bool(_os.environ.get("REHEARSE_EMAIL")),
                "hasPassword": bool(_os.environ.get("REHEARSE_PASSWORD")),
            })
            return

        if path == "/api/runs":
            fmt = (qs.get("format") or [""])[0]
            if fmt == "summary":
                self._send_json(list_run_summaries(root))
            else:
                self._send_json(list_runs(root))
            return

        if path.startswith("/api/runs/") and path.endswith("/crawl-graph"):
            run_id = path.strip("/").split("/")[2]
            try:
                run_id = _safe_id(run_id, "runId")
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            graph_path = root / "runs" / f"{run_id}-crawl-graph.json"
            if graph_path.is_file():
                self._send_json(json.loads(graph_path.read_text()))
            else:
                self._send_json({"nodes": [], "edges": [], "visitedCount": 0})
            return

        if path.startswith("/api/runs/") and path.endswith("/chat"):
            parts = path.strip("/").split("/")
            if len(parts) >= 4:
                run_id = parts[2]
                from rehearse.dashboard.chat_store import load_chat_thread

                self._send_json(load_chat_thread(root, run_id))
                return

        if path.startswith("/api/runs/"):
            run_id = path.split("/")[-1]
            if run_id.endswith("/graphml"):
                run_id = run_id.replace("/graphml", "")
            detail = get_run_detail(root, run_id)
            if not detail:
                self._send_json({"error": "not found"}, status=404)
                return
            self._send_json(detail)
            return

        if path.startswith("/api/bundle/"):
            run_id = path.split("/")[-1]
            bundle = load_bundle(root, run_id)
            if not bundle:
                self._send_json({"error": "not found"}, status=404)
                return
            self._send_json(bundle)
            return

        # ── Outcome feedback loop ─────────────────────────────────────────────
        if path == "/api/outcomes/due":
            from rehearse.dashboard.outcome_store import follow_up_due
            self._send_json({"due": follow_up_due(root)})
            return

        if path == "/api/outcomes":
            from rehearse.dashboard.outcome_store import list_outcomes
            self._send_json(list_outcomes(root))
            return

        if path.startswith("/api/outcomes/"):
            run_id = path.split("/")[-1]
            from rehearse.dashboard.outcome_store import get_outcome
            record = get_outcome(root, run_id)
            if not record:
                self._send_json({"error": "not found"}, status=404)
                return
            self._send_json(record)
            return

        if path == "/api/summaries":
            payload = self._require_jwt()
            config_prefix = None
            if payload:
                from rehearse.dashboard.workspace_store import get_workspaces_for_user
                workspaces = get_workspaces_for_user(root, payload["sub"])
                if workspaces:
                    cp = workspaces[0].get("configPath") or workspaces[0].get("config_path") or ""
                    if cp:
                        config_prefix = _config_prefix_from_path(cp)
            self._send_json(list_run_summaries(root, config_prefix=config_prefix))
            return

        if path.startswith("/api/experiment/") and path.endswith("/chat"):
            job_id = path.split("/")[-2]
            jobs = list_jobs(root)
            job = next((j for j in jobs if j.get("id") == job_id), None)
            if not job:
                self._send_json({"error": "experiment job not found"}, status=404)
                return
            from rehearse.dashboard.chat_store import load_chat_thread as _lct
            thread = _lct(root, f"exp-{job_id}")
            self._send_json({"jobId": job_id, "turns": thread.get("turns", [])})
            return

        if path.startswith("/api/experiment/") and path.endswith("/report"):
            job_id = path.split("/")[-2]
            jobs = list_jobs(root)
            job = next((j for j in jobs if j.get("id") == job_id), None)
            if not job:
                self._send_json({"error": "experiment job not found"}, status=404)
                return
            run_id_a = job.get("runIdA")
            run_id_b = job.get("runIdB")
            report: dict = {"jobId": job_id, "hypothesis": job.get("hypothesis"), "userGoal": job.get("userGoal")}
            if run_id_a and run_id_b:
                try:
                    ba = load_bundle(root, run_id_a)
                    bb = load_bundle(root, run_id_b)
                    d = diff_runs(root, run_id_a, run_id_b)
                    report["bundleA"] = ba
                    report["bundleB"] = bb
                    report["diff"] = d
                    # Per-persona comparison
                    def _persona_grades(bundle: dict) -> dict:
                        grades: dict = {}
                        for cell in (bundle.get("matrix") or []):
                            pid = cell.get("personaId") or cell.get("persona_id", "")
                            grade = cell.get("grade", "")
                            if pid:
                                grades.setdefault(pid, []).append(grade)
                        return {pid: max(set(gs), key=gs.count) for pid, gs in grades.items()}
                    grades_a = _persona_grades(ba)
                    grades_b = _persona_grades(bb)
                    personas_a = {p.get("id"): p.get("name") for p in (ba.get("personas") or [])}
                    personas_b = {p.get("id"): p.get("name") for p in (bb.get("personas") or [])}
                    all_pids = sorted(set(list(grades_a.keys()) + list(grades_b.keys())))
                    report["personaComparison"] = [
                        {"id": pid, "name": personas_a.get(pid) or personas_b.get(pid) or pid,
                         "gradeA": grades_a.get(pid, "—"), "gradeB": grades_b.get(pid, "—")}
                        for pid in all_pids
                    ]
                    # Readiness delta verdict
                    ra = (ba.get("summary") or {}).get("readiness") or 0
                    rb = (bb.get("summary") or {}).get("readiness") or 0
                    delta = rb - ra
                    report["readinessDelta"] = delta
                    report["hypothesisVerdict"] = "held" if delta > 2 else ("regressed" if delta < -2 else "inconclusive")
                except Exception as exc:
                    report["error"] = str(exc)
            self._send_json(report)
            return

        if path.startswith("/api/cohort/"):
            job_id = path.split("/")[-1]
            jobs = list_jobs(root)
            job = next((j for j in jobs if j.get("id") == job_id), None)
            if not job:
                self._send_json({"error": "cohort job not found"}, status=404)
                return
            self._send_json(job)
            return

        if path.startswith("/api/variant/"):
            job_id = path.split("/")[-1]
            jobs = list_jobs(root)
            job = next((j for j in jobs if j.get("id") == job_id), None)
            if not job:
                self._send_json({"error": "variant job not found"}, status=404)
                return
            payload: dict = dict(job)
            run_id_a = job.get("runIdA")
            run_id_b = job.get("runIdB")
            if run_id_a and run_id_b and not payload.get("diffNarrative"):
                try:
                    payload["diff"] = diff_runs(root, run_id_a, run_id_b)
                except Exception:
                    pass
            self._send_json(payload)
            return

        if path == "/api/diff":
            run_a = (qs.get("a") or [""])[0]
            run_b = (qs.get("b") or [""])[0]
            if not run_a or not run_b:
                self._send_json({"error": "query params a and b required"}, status=400)
                return
            refresh = (qs.get("refresh") or [""])[0].lower() in ("1", "true", "yes")
            self._send_json(diff_runs(root, run_a, run_b, refresh=refresh))
            return

        if path == "/api/progress":
            run_id = (qs.get("runId") or [""])[0].strip()
            from rehearse.progress import load_progress, latest_running_progress
            if run_id:
                try:
                    run_id = _safe_id(run_id, "runId")
                except ValueError as exc:
                    self._send_json({"error": str(exc)}, status=400)
                    return
                data = load_progress(root, run_id)
            else:
                data = latest_running_progress(root)
            if not data:
                self._send_json({"error": "no progress found"}, status=404)
                return
            self._send_json(data)
            return

        if path == "/api/trends":
            refresh = (qs.get("refresh") or [""])[0].lower() in ("1", "true", "yes")
            # JWT-authenticated users always get their workspace's prefix.
            # Unauthenticated callers may pass ?configPrefix= (internal/demo use only).
            payload = self._require_jwt()
            config_prefix: str | None = None
            if payload:
                from rehearse.dashboard.workspace_store import get_workspaces_for_user
                workspaces = get_workspaces_for_user(root, payload["sub"])
                if workspaces:
                    cp = workspaces[0].get("configPath") or workspaces[0].get("config_path") or ""
                    if cp:
                        config_prefix = _config_prefix_from_path(cp)
            else:
                config_prefix = (qs.get("configPrefix") or [""])[0].strip() or None
            self._send_json(get_trends(root, refresh=refresh, config_prefix=config_prefix))
            return

        if path == "/api/digest":
            n = int((qs.get("n") or ["7"])[0])
            refresh = (qs.get("refresh") or [""])[0].lower() in ("1", "true", "yes")
            self._send_json(get_command_digest(root, limit=max(1, min(n, 20)), refresh=refresh))
            return

        if path == "/api/search":
            q = (qs.get("q") or [""])[0]
            self._send_json(search_artifacts(root, q))
            return

        if path == "/api/product":
            config_id_q = (qs.get("configId") or [""])[0].strip()
            from rehearse.product_intelligence import load_product_model
            model = load_product_model(root, config_id_q or None)
            if not model:
                self._send_json({"error": "No product model — run POST /api/product/analyze first"}, status=404)
                return
            self._send_json(model)
            return

        if path == "/api/workspace":
            self._send_json(get_workspace(root))
            return

        if path == "/api/integrations":
            self._send_json(get_integrations())
            return

        if path == "/api/alerts":
            self._send_json(get_alerts(root))
            return

        if path == "/api/backlog":
            self._send_json(get_backlog(root))
            return

        if path.startswith("/api/configs/"):
            parts = path.strip("/").split("/")
            # /api/configs/{id}/personas
            if len(parts) == 4 and parts[3] == "personas":
                config_id = parts[2]
                try:
                    from rehearse.dashboard.config_yaml import get_config_personas

                    self._send_json(get_config_personas(root, config_id))
                except ValueError as exc:
                    self._send_json({"error": str(exc)}, status=404)
                return
            if len(parts) == 3 and parts[0] == "api" and parts[1] == "configs":
                config_id = parts[2]
                try:
                    from rehearse.dashboard.config_yaml import get_config_yaml

                    self._send_json(get_config_yaml(root, config_id))
                except ValueError as exc:
                    self._send_json({"error": str(exc)}, status=404)
                return

        if path == "/api/configs":
            payload = self._require_jwt()
            owner_id = payload["sub"] if payload else None
            self._send_json(list_configs(root, owner_id=owner_id))
            return

        if path == "/api/library":
            self._send_json(get_journey_library(root))
            return

        # ── Persona Library ───────────────────────────────────────────────────
        # GET  /api/persona-library          → list all saved personas
        # GET  /api/persona-library/{id}     → single persona
        #
        # POST /api/persona-library          → create / upsert persona
        # POST /api/persona-library/generate → AI-generate + optionally save
        # POST /api/persona-library/import   → bulk import from a config
        # DELETE /api/persona-library/{id}   → remove from library
        #
        # These are workspace-global: the library belongs to the user, not to
        # a single product.  Products reference library personas by id when
        # importing them into a config.
        if path == "/api/persona-library":
            from rehearse.dashboard.persona_store import list_personas
            self._send_json(list_personas(root))
            return

        if path.startswith("/api/persona-library/") and len(path.split("/")) == 4:
            pid = path.split("/")[-1]
            try:
                _safe_id(pid, "id")
            except ValueError as e:
                self._send_json({"error": str(e)}, status=400)
                return
            from rehearse.dashboard.persona_store import get_persona
            p = get_persona(root, pid)
            if p is None:
                self._send_json({"error": "not found"}, status=404)
                return
            self._send_json(p)
            return

        if path == "/api/init":
            self._send_json(get_init_wizard(root))
            return

        if path == "/api/jobs":
            # JWT-authenticated users always get their workspace's prefix so they
            # cannot cross into another workspace by passing ?configPrefix=.
            # Unauthenticated callers (demo / internal) may pass ?configPrefix= directly.
            payload = self._require_jwt()
            config_prefix_q: str | None = None
            if payload:
                from rehearse.dashboard.workspace_store import get_workspaces_for_user
                workspaces = get_workspaces_for_user(root, payload["sub"])
                if workspaces:
                    cp = workspaces[0].get("configPath") or workspaces[0].get("config_path") or ""
                    if cp:
                        config_prefix_q = _config_prefix_from_path(cp)
            else:
                config_prefix_q = (qs.get("configPrefix") or [""])[0].strip() or None

            jobs = list_jobs(root, config_prefix=config_prefix_q)

            # For running jobs: discover runId from progress file if missing,
            # and enrich with current phase (crawling / executing / analysing).
            runs_dir = root / "runs"
            for job in jobs:
                if job.get("status") != "running":
                    continue
                try:
                    run_id = job.get("runId")
                    prog_data: dict | None = None
                    if run_id:
                        pf = runs_dir / f"{run_id}-progress.json"
                        if pf.is_file():
                            prog_data = json.loads(pf.read_text())
                    if prog_data is None:
                        # No runId yet — scan for the most recently modified progress file
                        candidates = sorted(
                            runs_dir.glob("*-progress.json"),
                            key=lambda p: p.stat().st_mtime,
                            reverse=True,
                        )
                        if candidates:
                            prog_data = json.loads(candidates[0].read_text())
                            discovered = prog_data.get("run_id") if prog_data else None
                            if discovered and not run_id:
                                job["runId"] = discovered
                    if prog_data:
                        phase = prog_data.get("phase")
                        if phase and phase not in ("done", "failed", "complete"):
                            job["phase"] = phase
                        # Surface journey progress counts for the live table
                        for key in ("completed_journeys", "total_journeys", "total_personas"):
                            if prog_data.get(key) is not None:
                                job[key] = prog_data[key]
                except Exception:
                    pass
            self._send_json(jobs)
            return

        if path.startswith("/api/annotations/"):
            run_id = path.split("/")[-1]
            self._send_json(get_annotations(root, run_id))
            return

        if path.startswith("/api/sitemap/") and path.endswith("/graphml"):
            run_id = path.split("/")[3]
            graphml = load_sitemap_graphml(root, run_id)
            if not graphml:
                self._send_json({"error": "sitemap not found"}, status=404)
                return
            data = graphml.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/xml")
            self.send_header("Content-Length", str(len(data)))
            for k, v in _cors_headers(self._origin).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)
            return

        if path.startswith("/files/"):
            rel = path[len("/files/") :]
            file_path = (root / rel).resolve()
            if not str(file_path).startswith(str(root)) or not file_path.is_file():
                self.send_response(404)
                for k, v in _cors_headers(self._origin).items():
                    self.send_header(k, v)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            ctype = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            for k, v in _cors_headers(self._origin).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)
            return

        if path in ("/", "/index.html"):
            index = _STATIC_DIR / "index.html"
            if index.is_file():
                data = index.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        root = self.server.artifacts_root

        # Auth endpoints — handled before token check (always public)
        if path == "/auth/signup":
            body = self._read_json_body()
            from rehearse.dashboard.auth_store import create_user, issue_token
            user = create_user(
                root,
                email=str(body.get("email") or ""),
                password=str(body.get("password") or ""),
                name=str(body.get("name") or ""),
            )
            if not user:
                self._send_json({"error": "Email already in use"}, status=409)
                return
            self._send_json(
                {"token": issue_token(user), "user": user},
                status=201,
            )
            return

        if path == "/auth/login":
            body = self._read_json_body()
            from rehearse.dashboard.auth_store import authenticate_user, issue_token
            user = authenticate_user(
                root,
                email=str(body.get("email") or ""),
                password=str(body.get("password") or ""),
            )
            if not user:
                self._send_json({"error": "Invalid email or password"}, status=401)
                return
            self._send_json({"token": issue_token(user), "user": user})
            return

        if path == "/api/workspaces":
            payload = self._require_jwt()
            if not payload:
                self._send_json({"error": "Authentication required"}, status=401)
                return
            body = self._read_json_body()
            from rehearse.dashboard.workspace_store import create_workspace
            try:
                ws = create_workspace(
                    root,
                    owner_id=payload["sub"],
                    name=str(body.get("name") or ""),
                    target_url=str(body.get("targetUrl") or ""),
                    product_name=str(body.get("productName") or ""),
                    team_role=str(body.get("teamRole") or ""),
                )
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json(ws, status=201)
            return

        if not self._check_auth(path):
            return

        # Rate limiting (jobs + expensive LLM endpoints)
        from rehearse.dashboard.rate_limit import check_rate_limit, _LLM_PATHS
        _needs_rate_check = path.startswith("/api/jobs") or path in _LLM_PATHS
        if _needs_rate_check:
            client_ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
            allowed, group = check_rate_limit(client_ip, path)
            if not allowed:
                limit_msg = "5 job requests" if group == "jobs" else "10 LLM requests"
                self._send_json(
                    {"error": f"Rate limit exceeded ({group}). Max {limit_msg} per 60s per IP."},
                    status=429,
                )
                return

        if path == "/api/configs/validate":
            body = self._read_json_body()
            from rehearse.dashboard.config_yaml import validate_config_yaml

            yaml_text = body.get("yaml") or ""
            self._send_json(validate_config_yaml(yaml_text))
            return

        if path == "/api/configs/save":
            body = self._read_json_body()
            from rehearse.dashboard.config_yaml import save_config_yaml

            try:
                result = save_config_yaml(
                    root,
                    body.get("yaml") or "",
                    config_id=body.get("configId"),
                )
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json(result)
            return

        if path == "/api/configs/append-journey":
            body = self._read_json_body()
            from rehearse.dashboard.config_yaml import append_navigate_journey

            try:
                result = append_navigate_journey(
                    root,
                    config_id=str(body.get("configId") or "lr-self"),
                    path=str(body.get("path") or "/"),
                    title=body.get("title"),
                )
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json(result)
            return

        if path == "/api/configs/experiment":
            body = self._read_json_body()
            from rehearse.dashboard.config_yaml import set_config_experiment

            try:
                result = set_config_experiment(
                    root,
                    config_id=str(body.get("configId") or ""),
                    hypothesis=str(body.get("hypothesis") or ""),
                    user_goal=str(body.get("userGoal") or body.get("user_goal") or ""),
                    variant_label=str(body.get("variantLabel") or body.get("variant_label") or ""),
                )
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json(result)
            return

        if path == "/api/journeys/draft":
            body = self._read_json_body()
            from rehearse.dashboard.config_yaml import draft_journey_from_prompt

            try:
                result = draft_journey_from_prompt(
                    str(body.get("prompt") or ""),
                    target_url=str(body.get("targetUrl") or ""),
                )
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json(result)
            return

        if path == "/api/personas/draft":
            body = self._read_json_body()
            from rehearse.dashboard.persona_draft import draft_persona_from_prompt

            try:
                result = draft_persona_from_prompt(
                    str(body.get("prompt") or ""),
                    product_name=body.get("productName"),
                    target_url=body.get("targetUrl"),
                )
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json(result)
            return

        if path == "/api/product/analyze":
            body = self._read_json_body()
            target_url = str(body.get("targetUrl") or body.get("url") or "")
            config_id = str(body.get("configId") or "").strip()
            product_name = str(body.get("productName") or "")
            if not target_url:
                self._send_json({"error": "targetUrl required"}, status=400)
                return
            from rehearse.preflight import assert_url_allowed
            from rehearse.errors import SSRFBlockedError, PreflightError
            try:
                assert_url_allowed(target_url, allow_localhost=True)
            except (SSRFBlockedError, PreflightError) as exc:
                self._send_json({"error": f"URL not allowed: {exc}"}, status=400)
                return
            from rehearse.product_intelligence import analyze_product, save_product_model

            # Run a fresh deep crawl for vision-aware analysis
            sitemap_pages = list(body.get("sitemapPages") or [])
            interaction_map_data: dict = dict(body.get("interactionMap") or {})
            api_calls = list(body.get("apiCalls") or [])

            # Extract auth credentials and API keys from request
            auth_config = dict(body.get("auth") or {})
            llm_api_key = str(body.get("llmApiKey") or "").strip()
            vision_api_key = str(body.get("visionApiKey") or "").strip()

            # Persist auth credentials to env + .env file so rehearsal runs can use them
            if auth_config.get("email") and auth_config.get("password"):
                _write_cred_env(root, str(auth_config["email"]), str(auth_config["password"]))

            # Guard os.environ mutation with a lock so per-request keys don't race
            # with concurrent background job threads that also read REHEARSE_LLM_API_KEY.
            # The lock is held for the entire crawl + analysis window — only one
            # product analysis runs at a time (acceptable: local-first tool).
            import os as _os
            with _api_key_env_lock:
                _orig_llm = _os.environ.get("REHEARSE_LLM_API_KEY")
                _orig_vision = _os.environ.get("REHEARSE_VISION_API_KEY")
                try:
                    if llm_api_key:
                        _os.environ["REHEARSE_LLM_API_KEY"] = llm_api_key
                    if vision_api_key:
                        _os.environ["REHEARSE_VISION_API_KEY"] = vision_api_key

                    # If no crawl data, run a fresh deep crawl right now
                    if not interaction_map_data:
                        try:
                            from playwright.sync_api import sync_playwright
                            from rehearse.deep_crawler import run_deep_crawl, interaction_map_to_dict
                            screenshots_dir = root / "discovery_screenshots" / (config_id or "default")
                            with sync_playwright() as pw:
                                browser = pw.chromium.launch(headless=True)
                                context = browser.new_context(viewport={"width": 1280, "height": 800})
                                page_obj = context.new_page()

                                # Perform login if credentials provided
                                if auth_config.get("email") and auth_config.get("password"):
                                    try:
                                        login_url = str(auth_config.get("loginUrl") or target_url)
                                        page_obj.goto(login_url, wait_until="domcontentloaded", timeout=20000)
                                        page_obj.wait_for_timeout(3000)  # wait for SPA to hydrate
                                        # Fill email
                                        email_sel = str(auth_config.get("emailSelector") or "input[type='email'], input[name='email']")
                                        page_obj.locator(email_sel).first.fill(str(auth_config["email"]))
                                        # Fill password
                                        pw_sel = str(auth_config.get("passwordSelector") or "input[type='password']")
                                        page_obj.locator(pw_sel).first.fill(str(auth_config["password"]))
                                        page_obj.wait_for_timeout(500)
                                        # Submit
                                        submit_sel = str(auth_config.get("submitSelector") or "button[type='submit']")
                                        page_obj.locator(submit_sel).first.click()
                                        page_obj.wait_for_timeout(5000)  # wait for redirect + dashboard load
                                        page_obj.wait_for_load_state("networkidle", timeout=12000)
                                    except Exception:
                                        pass  # Continue even if login fails

                                imap = run_deep_crawl(
                                    page_obj, target_url,
                                    product_name=product_name,
                                    max_pages=15,
                                    max_buttons_per_page=12,
                                    use_vision=True,
                                    screenshots_dir=screenshots_dir,
                                )
                                interaction_map_data = interaction_map_to_dict(imap)
                                api_calls = imap.api_calls
                                context.close()
                                browser.close()
                        except Exception:
                            interaction_map_data = {}

                finally:
                    # Always restore — covers both the crawl path and the pre-crawled path
                    if _orig_llm is not None:
                        _os.environ["REHEARSE_LLM_API_KEY"] = _orig_llm
                    elif llm_api_key:
                        _os.environ.pop("REHEARSE_LLM_API_KEY", None)
                    if _orig_vision is not None:
                        _os.environ["REHEARSE_VISION_API_KEY"] = _orig_vision
                    elif vision_api_key:
                        _os.environ.pop("REHEARSE_VISION_API_KEY", None)

            # Try sitemap from latest run if still empty
            if not sitemap_pages:
                summaries = list_run_summaries(root)
                if summaries:
                    latest_bundle = load_bundle(root, summaries[0].get("id") or "")
                    if latest_bundle:
                        sitemap_pages = latest_bundle.get("sitemapPages") or []

            model = analyze_product(
                target_url,
                product_name=product_name,
                sitemap_pages=sitemap_pages,
                interaction_map=interaction_map_data,
                api_calls=api_calls,
            )
            save_product_model(root, model, config_id or None)
            if interaction_map_data:
                from rehearse.product_intelligence import save_interaction_map
                save_interaction_map(root, interaction_map_data, config_id or None)
            self._send_json(model)
            return

        if path == "/api/product/update":
            body = self._read_json_body()
            config_id = str(body.get("configId") or "").strip()
            from rehearse.product_intelligence import load_product_model, save_product_model
            existing = load_product_model(root, config_id or None) or {}
            existing.update({k: v for k, v in body.items() if k != "source"})
            save_product_model(root, existing, config_id or None)
            self._send_json(existing)
            return

        if path == "/api/journeys/discover":
            body = self._read_json_body()
            personas = list(body.get("personas") or [])
            config_id = str(body.get("configId") or "").strip()
            if not personas:
                self._send_json({"error": "personas list required"}, status=400)
                return
            from rehearse.product_intelligence import load_product_model, load_interaction_map
            from rehearse.persona_journey_discovery import discover_journeys_for_all_personas
            product_model = dict(body.get("productModel") or {})
            if not product_model:
                product_model = load_product_model(root, config_id or None) or {}
            if not product_model:
                self._send_json({"error": "No product model — run product analysis first"}, status=400)
                return
            interaction_map = load_interaction_map(root, config_id or None)
            results = discover_journeys_for_all_personas(personas, product_model, interaction_map)
            self._send_json({"personaJourneys": results, "count": len(results)})
            return

        if path == "/api/journeys/discover/persona":
            body = self._read_json_body()
            persona = dict(body.get("persona") or {})
            config_id = str(body.get("configId") or "").strip()
            if not persona:
                self._send_json({"error": "persona required"}, status=400)
                return
            from rehearse.product_intelligence import load_product_model, load_interaction_map
            from rehearse.persona_journey_discovery import discover_journeys_for_persona
            product_model = dict(body.get("productModel") or {})
            if not product_model:
                product_model = load_product_model(root, config_id or None) or {}
            interaction_map = load_interaction_map(root, config_id or None)
            result = discover_journeys_for_persona(persona, product_model, interaction_map)
            self._send_json(result)
            return

        if path == "/api/journeys/discover/persona/stream":
            body = self._read_json_body()
            persona = dict(body.get("persona") or {})
            config_id = str(body.get("configId") or "").strip()
            if not persona:
                self._send_json({"error": "persona required"}, status=400)
                return

            from rehearse.product_intelligence import (
                load_product_model, load_interaction_map,
            )
            from rehearse.persona_journey_discovery import discover_journeys_for_persona_streaming
            import queue as _queue
            import threading as _threading
            import os as _os

            product_model = dict(body.get("productModel") or {})
            if not product_model:
                product_model = load_product_model(root, config_id or None) or {}

            # Load stored interaction map — built during product analysis
            interaction_map = load_interaction_map(root, config_id or None)

            # If no interaction map stored yet, run a targeted deep crawl now
            if not interaction_map:
                target_url = str(product_model.get("targetUrl") or product_model.get("url") or "")
                if target_url:
                    from rehearse.preflight import assert_url_allowed as _aurl
                    from rehearse.errors import SSRFBlockedError as _SSRFErr, PreflightError as _PFErr
                    try:
                        _aurl(target_url, allow_localhost=True)
                    except (_SSRFErr, _PFErr):
                        target_url = ""  # silently skip crawl — bad URL from stored model
                if target_url:
                    try:
                        from playwright.sync_api import sync_playwright
                        from rehearse.deep_crawler import run_deep_crawl, interaction_map_to_dict
                        from rehearse.product_intelligence import save_interaction_map
                        screenshots_dir = root / "discovery_screenshots" / (config_id or "default")
                        email = _os.environ.get("REHEARSE_EMAIL", "")
                        password = _os.environ.get("REHEARSE_PASSWORD", "")
                        with sync_playwright() as pw:
                            browser = pw.chromium.launch(headless=True)
                            ctx = browser.new_context(viewport={"width": 1280, "height": 800})
                            page_obj = ctx.new_page()
                            if email and password:
                                try:
                                    page_obj.goto(target_url, wait_until="domcontentloaded", timeout=20000)
                                    page_obj.wait_for_timeout(3000)
                                    page_obj.locator("input[type='email'], input[name='email']").first.fill(email)
                                    page_obj.locator("input[type='password']").first.fill(password)
                                    page_obj.wait_for_timeout(500)
                                    page_obj.locator("button[type='submit']").first.click()
                                    page_obj.wait_for_timeout(5000)
                                    page_obj.wait_for_load_state("networkidle", timeout=12000)
                                except Exception:
                                    pass
                            imap = run_deep_crawl(
                                page_obj, target_url,
                                product_name=str(product_model.get("name") or ""),
                                max_pages=20,
                                max_buttons_per_page=15,
                                use_vision=True,
                                screenshots_dir=screenshots_dir,
                            )
                            interaction_map = interaction_map_to_dict(imap)
                            save_interaction_map(root, interaction_map, config_id or None)
                            ctx.close()
                            browser.close()
                    except Exception:
                        interaction_map = None

            # — SSE response —
            try:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("X-Accel-Buffering", "no")
                for k, v in _cors_headers(self._origin).items():
                    self.send_header(k, v)
                self.end_headers()
            except (BrokenPipeError, ConnectionResetError):
                return

            ev_queue: _queue.Queue = _queue.Queue()
            _SENTINEL = object()

            def _on_event(ev: dict) -> None:
                ev_queue.put(ev)

            def _worker() -> None:
                try:
                    discover_journeys_for_persona_streaming(
                        persona, product_model, interaction_map, on_event=_on_event
                    )
                finally:
                    ev_queue.put(_SENTINEL)

            _threading.Thread(target=_worker, daemon=True).start()

            while True:
                try:
                    ev = ev_queue.get(timeout=150)
                    if ev is _SENTINEL:
                        break
                    line = ("data: " + json.dumps(ev) + "\n\n").encode()
                    self.wfile.write(line)
                    self.wfile.flush()
                except (_queue.Empty, BrokenPipeError, ConnectionResetError, OSError):
                    break
            return

        if path == "/api/journeys/import":
            body = self._read_json_body()
            config_id = str(body.get("configId") or "").strip()
            journeys = list(body.get("journeys") or [])
            if not config_id:
                self._send_json({"error": "configId required"}, status=400)
                return
            if not journeys:
                self._send_json({"error": "journeys list required"}, status=400)
                return
            from rehearse.dashboard.config_yaml import append_discovered_journeys
            try:
                result = append_discovered_journeys(root, config_id=config_id, journeys=journeys)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json(result)
            return

        if path == "/api/personas/suggest":
            body = self._read_json_body()
            from rehearse.dashboard.persona_draft import suggest_personas_for_product

            result = suggest_personas_for_product(
                product_name=body.get("productName"),
                target_url=body.get("targetUrl"),
                existing_ids=list(body.get("existingIds") or []),
            )
            self._send_json(result)
            return

        # ── Persona Library mutations (POST) ─────────────────────────────────
        if path == "/api/persona-library":
            # Upsert a persona record into the library.
            # Only known fields are forwarded to prevent arbitrary key injection
            # into personas.json.
            _PERSONA_FIELDS = {
                "id", "name", "role", "goals", "enabled", "tech_literacy",
                "patience", "trust_level", "character", "usage_context",
                "tags", "source", "created_at", "updated_at",
            }
            body = self._read_json_body()
            body = {k: v for k, v in body.items() if k in _PERSONA_FIELDS}
            from rehearse.dashboard.persona_store import save_persona
            saved = save_persona(root, body)
            self._send_json(saved)
            return

        if path == "/api/persona-library/generate":
            # AI-generate a rich behavioral persona, then optionally save it.
            # Body: { prompt, productName?, targetUrl?, save?: bool }
            body = self._read_json_body()
            prompt = str(body.get("prompt") or "").strip()
            if not prompt:
                self._send_json({"error": "prompt is required"}, status=400)
                return
            from rehearse.dashboard.persona_draft import draft_library_persona
            try:
                persona = draft_library_persona(
                    prompt,
                    product_name=body.get("productName"),
                    target_url=body.get("targetUrl"),
                )
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return

            # ``save=true`` → persist to library immediately; frontend can also
            # let the user review before saving (``save=false`` is the default).
            if body.get("save"):
                from rehearse.dashboard.persona_store import save_persona
                persona = save_persona(root, persona)

            import yaml as _yaml
            from rehearse.dashboard.persona_draft import persona_to_yaml_entry
            fragment = _yaml.dump(
                [persona_to_yaml_entry(persona)],
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
            self._send_json({"persona": persona, "yamlFragment": fragment})
            return

        if path == "/api/persona-library/import":
            # Bulk-import personas from an existing config file into the library.
            # Body: { configId: string }   (the config filename stem)
            body = self._read_json_body()
            config_id = str(body.get("configId") or "").strip()
            if not config_id:
                self._send_json({"error": "configId is required"}, status=400)
                return
            try:
                config_id = _safe_id(config_id, "configId")
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            cfg_path = root / "configs" / f"{config_id}.yaml"
            if not cfg_path.is_file():
                self._send_json({"error": f"config {config_id!r} not found"}, status=404)
                return
            try:
                import yaml as _yaml
                cfg = _yaml.safe_load(cfg_path.read_text())
                personas_in_cfg = cfg.get("personas") or []
            except Exception as exc:
                self._send_json({"error": f"Failed to read config: {exc}"}, status=500)
                return

            import re as _re
            # Derive product slug by stripping the -YYYYMMDD-HHMMSS suffix
            m = _re.match(r"^(.*)-\d{8}-\d{6}$", config_id)
            slug = m.group(1) if m else config_id

            from rehearse.dashboard.persona_store import import_from_config
            saved = import_from_config(root, personas_in_cfg, product_slug=slug)
            self._send_json({"imported": len(saved), "personas": saved})
            return

        if path == "/api/recordings/save":
            body = self._read_json_body()
            run_id = str(body.get("runId") or "").strip()
            journey_id = str(body.get("journeyId") or "").strip()
            events = body.get("events") or []
            if not run_id or not journey_id or not events:
                self._send_json({"error": "runId, journeyId, and events required"}, status=400)
                return
            try:
                run_id = _safe_id(run_id, "runId")
                journey_id = _safe_id(journey_id, "journeyId")
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            from rehearse.recording import save_rrweb_recording
            try:
                path = save_rrweb_recording(root, run_id, journey_id, events)
                self._send_json({"ok": True, "path": str(path), "eventCount": len(events)})
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=500)
            return

        if path == "/api/recordings/list":
            run_id = self._get_query_param("runId") or ""
            if not run_id:
                self._send_json({"error": "runId required"}, status=400)
                return
            try:
                run_id = _safe_id(run_id, "runId")
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            from rehearse.recording import list_recordings_for_run
            recordings = list_recordings_for_run(root, run_id)
            self._send_json({"runId": run_id, "recordings": recordings})
            return

        # GET /api/recordings/{runId}/{journeyId}
        if path.startswith("/api/recordings/") and path.count("/") == 4:
            parts = path.split("/")
            try:
                run_id = _safe_id(parts[3], "runId")
                journey_id = _safe_id(parts[4], "journeyId")
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            from rehearse.recording import load_rrweb_recording, get_video_path
            recording = load_rrweb_recording(root, run_id, journey_id)
            if not recording:
                self._send_json({"error": "Recording not found"}, status=404)
                return
            video_path = get_video_path(root, run_id, journey_id)
            self._send_json({
                "journeyId": journey_id,
                "eventCount": recording.get("eventCount", 0),
                "hasVideo": video_path is not None,
            })
            return

        # GET /api/recordings/{runId}/{journeyId}/video
        if path.endswith("/video") and path.startswith("/api/recordings/"):
            parts = path.split("/")
            try:
                run_id = _safe_id(parts[3], "runId")
                journey_id = _safe_id(parts[4], "journeyId")
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            from rehearse.recording import get_video_path
            video_path = get_video_path(root, run_id, journey_id)
            if not video_path or not video_path.is_file():
                self._send_json({"error": "Video not found"}, status=404)
                return
            self._send_file(str(video_path), "video/webm")
            return

        # GET /api/recordings/{runId}/{journeyId}/export
        if path.endswith("/export") and path.startswith("/api/recordings/"):
            parts = path.split("/")
            try:
                run_id = _safe_id(parts[3], "runId")
                journey_id = _safe_id(parts[4], "journeyId")
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            from rehearse.recording import load_rrweb_recording
            recording = load_rrweb_recording(root, run_id, journey_id)
            if not recording:
                self._send_json({"error": "Recording not found"}, status=404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Disposition", f'attachment; filename="{journey_id}-events.json"')
            self.end_headers()
            self.wfile.write(json.dumps(recording, indent=2).encode())
            return

        if path == "/api/configs/append-persona":
            body = self._read_json_body()
            from rehearse.dashboard.config_yaml import append_persona_to_config

            try:
                result = append_persona_to_config(
                    root,
                    config_id=str(body.get("configId") or ""),
                    persona=body.get("persona") or {},
                )
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json(result)
            return

        if path == "/api/configs/personas":
            body = self._read_json_body()
            from rehearse.dashboard.config_yaml import update_config_personas

            try:
                result = update_config_personas(
                    root,
                    config_id=str(body.get("configId") or ""),
                    persona_enabled=body.get("personaEnabled"),
                    persona_lens=body.get("personaLens"),
                )
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json(result)
            return

        if path == "/api/configs/personas/replace":
            body = self._read_json_body()
            from rehearse.dashboard.config_yaml import replace_config_personas

            try:
                result = replace_config_personas(
                    root,
                    config_id=str(body.get("configId") or ""),
                    personas=list(body.get("personas") or []),
                    persona_lens=body.get("personaLens"),
                )
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json(result)
            return

        if path == "/api/configs":
            payload = self._require_jwt()
            if not payload:
                if _API_TOKEN:
                    # Production mode — JWT is required
                    self._send_json({"error": "Authentication required"}, status=401)
                    return
                # Local dev — no owner, saves to flat artifacts/configs/
                payload = {"sub": ""}
            body = self._read_json_body()
            # Only scope to owner subdirectory when there's a real authenticated user
            if payload.get("sub"):
                body["_owner_id"] = payload["sub"]
            try:
                result = save_config(root, body)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json(result, status=201)
            return

        if path == "/api/preflight":
            body = self._read_json_body()
            url = body.get("url", "")
            if not url:
                self._send_json({"error": "url required"}, status=400)
                return
            self._send_json(run_preflight(url, allow_localhost=bool(body.get("allowLocalhost"))))
            return

        if path == "/api/workspace":
            body = self._read_json_body()
            self._send_json(save_workspace(root, body))
            return

        if path.startswith("/api/experiment/") and path.endswith("/chat"):
            job_id = path.split("/")[-2]
            jobs = list_jobs(root)
            job = next((j for j in jobs if j.get("id") == job_id), None)
            if not job:
                self._send_json({"error": "experiment job not found"}, status=404)
                return
            body = self._read_json_body()
            message = (body.get("message") or "").strip()
            if not message:
                self._send_json({"error": "message required"}, status=400)
                return
            from rehearse.dashboard.chat_store import chat_history_for_llm, load_chat_thread, save_chat_turn
            from rehearse.llm import chat_about_experiment

            thread_key = f"exp-{job_id}"
            thread = load_chat_thread(root, thread_key)
            history = chat_history_for_llm(thread)
            bundle_a = load_bundle(root, job.get("runIdA") or "") if job.get("runIdA") else None
            bundle_b = load_bundle(root, job.get("runIdB") or "") if job.get("runIdB") else None
            diff = None
            if job.get("runIdA") and job.get("runIdB"):
                try:
                    diff = diff_runs(root, job["runIdA"], job["runIdB"])
                except Exception:
                    pass
            result = chat_about_experiment(job, bundle_a, bundle_b, diff, message, history=history)
            save_chat_turn(root, thread_key, user_message=message,
                           assistant_reply=result.get("reply", ""), source=result.get("source", "template"))
            self._send_json({"jobId": job_id, "reply": result.get("reply"), "source": result.get("source"), "turns": load_chat_thread(root, thread_key).get("turns", [])})
            return

        if path.startswith("/api/runs/") and path.endswith("/chat"):
            parts = path.strip("/").split("/")
            if len(parts) >= 4 and parts[-1] == "chat":
                run_id = parts[2]
                try:
                    _safe_id(run_id, "runId")
                except ValueError as e:
                    self._send_json({"error": str(e)}, status=400)
                    return
                bundle = load_bundle(root, run_id)
                if not bundle:
                    self._send_json({"error": "run not found"}, status=404)
                    return
                body = self._read_json_body()
                message = (body.get("message") or "").strip()
                if not message:
                    self._send_json({"error": "message required"}, status=400)
                    return
                from rehearse.dashboard.chat_store import (
                    chat_history_for_llm,
                    load_chat_thread,
                    save_chat_turn,
                )
                from rehearse.llm import chat_about_run

                thread = load_chat_thread(root, run_id)
                history = chat_history_for_llm(thread)
                if not history and isinstance(body.get("history"), list):
                    history = body.get("history")
                result = chat_about_run(bundle, message, history=history)
                save_chat_turn(
                    root,
                    run_id,
                    user_message=message,
                    assistant_reply=result.get("reply", ""),
                    source=result.get("source", "template"),
                )
                self._send_json({"runId": run_id, **result})
                return

        if path == "/api/recordings/compile":
            body = self._read_json_body()
            from rehearse.dashboard.recordings import compile_journey_yaml

            out = compile_journey_yaml(
                journey_id=str(body.get("journeyId") or "recorded-journey"),
                journey_name=str(body.get("journeyName") or "Recorded journey"),
                steps=body.get("steps") if isinstance(body.get("steps"), list) else [],
            )
            self._send_json(out)
            return

        if path == "/api/jobs/cohort":
            body = self._read_json_body()
            cfg = Path(body.get("configPath", ""))
            try:
                cfg.resolve().relative_to(root.resolve())
            except (ValueError, OSError):
                self._send_json({"error": "configPath must be within artifacts root"}, status=400)
                return
            if not cfg.is_file():
                self._send_json({"error": "configPath required"}, status=400)
                return
            job = enqueue_cohort_run(
                root,
                config_path=cfg,
                n_seeds=int(body.get("nSeeds", 3)),
                hypothesis=str(body.get("hypothesis") or ""),
                output_dir=root,
                use_llm=bool(body.get("llm")),
            )
            self._send_json(job, status=202)
            return

        if path == "/api/jobs/variant":
            body = self._read_json_body()
            config_a = Path(body.get("configAPath", ""))
            config_b = Path(body.get("configBPath", ""))
            try:
                root_resolved = root.resolve()
                config_a.resolve().relative_to(root_resolved)
                config_b.resolve().relative_to(root_resolved)
            except (ValueError, OSError):
                self._send_json({"error": "configAPath and configBPath must be within artifacts root"}, status=400)
                return
            if not config_a.is_file() or not config_b.is_file():
                self._send_json({"error": "configAPath and configBPath must be valid files"}, status=400)
                return
            job = enqueue_variant_run(
                root,
                config_a=config_a,
                config_b=config_b,
                hypothesis=str(body.get("hypothesis") or ""),
                user_goal=str(body.get("userGoal") or ""),
                output_dir=root,
                use_llm=bool(body.get("llm")),
            )
            self._send_json(job, status=202)
            return

        if path == "/api/jobs":
            body = self._read_json_body()
            config_path = Path(body.get("configPath", ""))
            if config_path.parts:  # only bounds-check if a path was actually provided
                try:
                    config_path.resolve().relative_to(root.resolve())
                except (ValueError, OSError):
                    self._send_json({"error": "configPath must be within artifacts root"}, status=400)
                    return
            if not config_path.is_file():
                configs = list_configs(root)
                if configs:
                    config_path = Path(configs[0]["path"])
                else:
                    self._send_json({"error": "configPath required"}, status=400)
                    return
            job = enqueue_run(
                root,
                config_path=config_path,
                output_dir=root,
                mode=body.get("mode", "run"),
                use_llm=bool(body.get("llm")),
                no_crawl=bool(body.get("noCrawl")),
            )
            self._send_json(job, status=202)
            return

        if path.startswith("/api/annotations/"):
            run_id = path.split("/")[-1]
            try:
                _safe_id(run_id, "runId")
            except ValueError as e:
                self._send_json({"error": str(e)}, status=400)
                return
            body = self._read_json_body()
            anns = save_annotation(root, run_id, body)
            self._send_json(anns)
            return

        if path == "/api/backfill":
            rebuilt = backfill_all(root)
            self._send_json({"rebuilt": rebuilt, "count": len(rebuilt)})
            return

        if path == "/api/credentials":
            import os as _os
            body = self._read_json_body()
            email = str(body.get("email") or "").strip()
            password = str(body.get("password") or "").strip()
            config_id = str(body.get("configId") or "").strip()
            login_path = str(body.get("loginPath") or "").strip()
            _write_cred_env(root, email, password)
            # Inject auth block into config YAML if configId + loginPath provided
            yaml_updated = False
            if config_id and login_path:
                try:
                    import yaml as _yaml
                    from rehearse.dashboard.config_yaml import get_config_yaml, save_config_yaml
                    _meta = get_config_yaml(root, config_id)
                    _data = _yaml.safe_load(_meta["yaml"]) or {}
                    _data["auth"] = {
                        "login_path": login_path,
                        "email_env": "REHEARSE_EMAIL",
                        "password_env": "REHEARSE_PASSWORD",
                    }
                    _new_yaml = _yaml.dump(_data, default_flow_style=False, sort_keys=False, allow_unicode=True)
                    save_config_yaml(root, _new_yaml, config_id=config_id)
                    yaml_updated = True
                except Exception:
                    pass
            self._send_json({"ok": True, "yamlUpdated": yaml_updated})
            return

        if path.startswith("/api/runs/") and path.endswith("/control"):
            parts = path.split("/")
            if len(parts) == 5:
                try:
                    run_id = _safe_id(parts[3], "runId")
                except ValueError as exc:
                    self._send_json({"error": str(exc)}, status=400)
                    return
                body = self._read_json_body()
                signal = str(body.get("signal") or "").strip()
                if signal not in ("pause", "resume", "stop"):
                    self._send_json({"error": "signal must be pause, resume, or stop"}, status=400)
                    return
                from rehearse.progress import send_signal
                send_signal(root, run_id, signal)
                self._send_json({"runId": run_id, "signal": signal})
                return

        self.send_error(404)

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        root = self.server.artifacts_root

        if not self._check_auth(path):
            return

        # DELETE /api/persona-library/{id}
        if path.startswith("/api/persona-library/"):
            pid = path.split("/")[-1]
            try:
                _safe_id(pid, "id")
            except ValueError as e:
                self._send_json({"error": str(e)}, status=400)
                return
            from rehearse.dashboard.persona_store import delete_persona
            found = delete_persona(root, pid)
            if not found:
                self._send_json({"error": "not found"}, status=404)
                return
            self._send_json({"deleted": pid})
            return

        self.send_error(404)

    def do_PUT(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        root = self.server.artifacts_root

        if not self._check_auth(path):
            return

        if path == "/api/workspace":
            body = self._read_json_body()
            self._send_json(save_workspace(root, body))
            return

        # ── Outcome feedback loop ─────────────────────────────────────────────
        if path == "/api/outcomes":
            body = self._read_json_body()
            from rehearse.dashboard.outcome_store import record_outcome
            try:
                saved = record_outcome(root, body)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json(saved, status=201)
            return

        self.send_error(404)


def serve_dashboard(artifacts_root: Path, host: str = "127.0.0.1", port: int = 8765) -> None:
    artifacts_root = artifacts_root.resolve()
    # Ensure auth + workspace tables exist (idempotent)
    from rehearse.dashboard.auth_store import ensure_users_table
    from rehearse.dashboard.workspace_store import ensure_workspaces_table
    ensure_users_table(artifacts_root)
    ensure_workspaces_table(artifacts_root)
    # Migrate legacy jobs.json → SQLite on first boot
    from rehearse.dashboard.job_store import migrate_from_json
    migrated = migrate_from_json(artifacts_root)
    if migrated:
        print(f"Migrated {migrated} job(s) from jobs.json → jobs.db")
    stale = mark_stale_running_jobs(artifacts_root)
    if stale:
        print(f"Marked {stale} stale running job(s) as failed (prior serve restart).")
    from rehearse.run_manager import RunStateMachine
    recovered_states = RunStateMachine.recover_stale(artifacts_root / "runs")
    if recovered_states:
        print(f"Recovered {len(recovered_states)} stale run state(s): {recovered_states}")
    rebuilt = backfill_all(artifacts_root)
    if rebuilt:
        print(f"Backfilled analysis.json for {len(rebuilt)} run(s).")
    server, bound_port = _bind_server(host, port, artifacts_root)
    url = f"http://{host}:{bound_port}"
    if bound_port != port:
        print(f"Port {port} in use — using {bound_port} instead.")
    print(f"Launch Rehearsal dashboard → {url}")
    print(f"Artifacts root: {artifacts_root}")
    runs_dir = artifacts_root / "runs"
    if not runs_dir.is_dir() or not any(runs_dir.glob("*.json")):
        print(
            "Warning: no runs found under artifacts/runs/. "
            "Use -o artifacts when cwd is launch-rehearsal/ (not launch-rehearsal/artifacts)."
        )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.shutdown()


def serve_dashboard_background(
    artifacts_root: Path, host: str = "127.0.0.1", port: int = 8765
) -> threading.Thread:
    thread = threading.Thread(
        target=serve_dashboard,
        args=(artifacts_root, host, port),
        daemon=True,
        name="rehearse-dashboard",
    )
    thread.start()
    return thread
