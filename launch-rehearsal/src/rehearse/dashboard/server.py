"""Local monitoring dashboard HTTP server."""

from __future__ import annotations

import json
import mimetypes
import os
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


def _cors_headers(origin: str | None) -> dict[str, str]:
    """Return CORS headers. Allow the requesting origin if it is in the allowlist."""
    allowed = origin if (origin and origin in _CORS_ORIGINS) else next(iter(_CORS_ORIGINS), "*")
    return {
        "Access-Control-Allow-Origin": allowed,
        "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
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

        if path == "/api/runs":
            fmt = (qs.get("format") or [""])[0]
            if fmt == "summary":
                self._send_json(list_run_summaries(root))
            else:
                self._send_json(list_runs(root))
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

        if path == "/api/summaries":
            self._send_json(list_run_summaries(root))
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

        if path == "/api/trends":
            refresh = (qs.get("refresh") or [""])[0].lower() in ("1", "true", "yes")
            self._send_json(get_trends(root, refresh=refresh))
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
            from rehearse.product_intelligence import load_product_model
            model = load_product_model(root)
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
            self._send_json(list_configs(root))
            return

        if path == "/api/library":
            self._send_json(get_journey_library(root))
            return

        if path == "/api/init":
            self._send_json(get_init_wizard(root))
            return

        if path == "/api/jobs":
            self._send_json(list_jobs(root))
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
            for k, v in _CORS.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)
            return

        if path.startswith("/files/"):
            rel = path[len("/files/") :]
            file_path = (root / rel).resolve()
            if not str(file_path).startswith(str(root)) or not file_path.is_file():
                self.send_error(404)
                return
            ctype = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            for k, v in _CORS.items():
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

        # Rate limiting (jobs endpoints — prevent run storms)
        if path.startswith("/api/jobs") or path.startswith("/api/jobs/"):
            from rehearse.dashboard.rate_limit import check_rate_limit
            client_ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
            allowed, group = check_rate_limit(client_ip, path)
            if not allowed:
                self._send_json(
                    {"error": f"Rate limit exceeded ({group}). Max 5 job requests per 60s per IP."},
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
            if not target_url:
                self._send_json({"error": "targetUrl required"}, status=400)
                return
            from rehearse.product_intelligence import analyze_product, save_product_model
            # Use existing sitemap data if available (from a recent run)
            sitemap_pages = list(body.get("sitemapPages") or [])
            interaction_map = dict(body.get("interactionMap") or {})
            api_calls = list(body.get("apiCalls") or [])
            # If no crawl data provided, try to load from latest run
            if not sitemap_pages:
                summaries = list_run_summaries(root)
                if summaries:
                    latest = summaries[0]
                    latest_bundle = load_bundle(root, latest.get("id") or "")
                    if latest_bundle:
                        sitemap_pages = latest_bundle.get("sitemapPages") or []
            model = analyze_product(
                target_url,
                product_name=str(body.get("productName") or ""),
                sitemap_pages=sitemap_pages,
                interaction_map=interaction_map,
                api_calls=api_calls,
            )
            save_product_model(root, model)
            self._send_json(model)
            return

        if path == "/api/product/update":
            body = self._read_json_body()
            from rehearse.product_intelligence import load_product_model, save_product_model
            existing = load_product_model(root) or {}
            existing.update({k: v for k, v in body.items() if k != "source"})
            save_product_model(root, existing)
            self._send_json(existing)
            return

        if path == "/api/journeys/discover":
            body = self._read_json_body()
            personas = list(body.get("personas") or [])
            config_id = str(body.get("configId") or "").strip()
            if not personas:
                self._send_json({"error": "personas list required"}, status=400)
                return
            from rehearse.product_intelligence import load_product_model
            from rehearse.persona_journey_discovery import discover_journeys_for_all_personas
            from rehearse.dashboard.config_yaml import load_config

            # Load config to get workspace context
            cfg = load_config(root, config_id) if config_id else None
            if not cfg:
                self._send_json({"error": "Config not found or not provided"}, status=400)
                return

            product_model = load_product_model(root) or {}
            if not product_model:
                self._send_json({"error": "No product model — run POST /api/product/analyze first"}, status=400)
                return
            results = discover_journeys_for_all_personas(personas, product_model)
            self._send_json({"personaJourneys": results, "count": len(results)})
            return

        if path == "/api/journeys/discover/persona":
            body = self._read_json_body()
            persona = dict(body.get("persona") or {})
            if not persona:
                self._send_json({"error": "persona required"}, status=400)
                return
            from rehearse.product_intelligence import load_product_model
            from rehearse.persona_journey_discovery import discover_journeys_for_persona
            product_model = load_product_model(root) or {}
            result = discover_journeys_for_persona(persona, product_model)
            self._send_json(result)
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

        if path == "/api/recordings/save":
            body = self._read_json_body()
            run_id = str(body.get("runId") or "").strip()
            journey_id = str(body.get("journeyId") or "").strip()
            events = body.get("events") or []
            if not run_id or not journey_id or not events:
                self._send_json({"error": "runId, journeyId, and events required"}, status=400)
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
            from rehearse.recording import list_recordings_for_run
            recordings = list_recordings_for_run(root, run_id)
            self._send_json({"runId": run_id, "recordings": recordings})
            return

        # GET /api/recordings/{runId}/{journeyId}
        if path.startswith("/api/recordings/") and path.count("/") == 4:
            parts = path.split("/")
            run_id, journey_id = parts[3], parts[4]
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
            run_id, journey_id = parts[3], parts[4]
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
            run_id, journey_id = parts[3], parts[4]
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
            body = self._read_json_body()
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
            body = self._read_json_body()
            anns = save_annotation(root, run_id, body)
            self._send_json(anns)
            return

        if path == "/api/backfill":
            rebuilt = backfill_all(root)
            self._send_json({"rebuilt": rebuilt, "count": len(rebuilt)})
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
