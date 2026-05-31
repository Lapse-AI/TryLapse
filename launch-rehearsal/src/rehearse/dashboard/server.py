"""Local monitoring dashboard HTTP server."""

from __future__ import annotations

import json
import mimetypes
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from rehearse.dashboard.graphml import load_sitemap_graphml
from rehearse.dashboard.jobs import enqueue_run, list_jobs
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
    get_trends,
    get_workspace,
    list_configs,
    list_run_summaries,
    list_runs,
    load_bundle,
    run_preflight,
    save_annotation,
    save_workspace,
    search_artifacts,
)

_STATIC_DIR = Path(__file__).resolve().parent / "static"
_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
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

    def _send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in _CORS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, data: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        for k, v in _CORS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        for k, v in _CORS.items():
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

        if path == "/api/runs":
            fmt = (qs.get("format") or [""])[0]
            if fmt == "summary":
                self._send_json(list_run_summaries(root))
            else:
                self._send_json(list_runs(root))
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

        if path == "/api/diff":
            run_a = (qs.get("a") or [""])[0]
            run_b = (qs.get("b") or [""])[0]
            if not run_a or not run_b:
                self._send_json({"error": "query params a and b required"}, status=400)
                return
            self._send_json(diff_runs(root, run_a, run_b))
            return

        if path == "/api/trends":
            self._send_json(get_trends(root))
            return

        if path == "/api/search":
            q = (qs.get("q") or [""])[0]
            self._send_json(search_artifacts(root, q))
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

        if path == "/api/preflight":
            body = self._read_json_body()
            url = body.get("url", "")
            if not url:
                self._send_json({"error": "url required"}, status=400)
                return
            self._send_json(run_preflight(url))
            return

        if path == "/api/workspace":
            body = self._read_json_body()
            self._send_json(save_workspace(root, body))
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
        if path == "/api/workspace":
            body = self._read_json_body()
            self._send_json(save_workspace(root, body))
            return
        self.send_error(404)


def serve_dashboard(artifacts_root: Path, host: str = "127.0.0.1", port: int = 8765) -> None:
    artifacts_root = artifacts_root.resolve()
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
