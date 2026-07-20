"""Run concurrency — unrelated workspaces must not serialize behind each other.

Regression for the production bug where a single global threading.Lock()
wrapped every rehearsal run on the deployment: two customers running
rehearsals at the same moment had one queue behind the other with zero
actual resource contention reason to do so. Replaced with a bounded
Semaphore sized to protect the container from unbounded concurrent
Chromium subprocesses, without forcing unrelated runs to serialize.
"""
from __future__ import annotations

import importlib
import threading
import time

import rehearse.dashboard.jobs as jobs_module


def _reload_jobs_with_limit(monkeypatch, limit: int):
    monkeypatch.setenv("REHEARSE_MAX_CONCURRENT_RUNS", str(limit))
    importlib.reload(jobs_module)
    return jobs_module


def test_default_allows_more_than_one_concurrent_run(monkeypatch):
    """The old bug: capacity was hardcoded to 1 (a plain Lock)."""
    mod = _reload_jobs_with_limit(monkeypatch, 3)
    entered = []
    barrier = threading.Barrier(2, timeout=2)

    def worker():
        with mod._run_serial_lock:
            entered.append(threading.current_thread().name)
            barrier.wait()  # both threads must be inside the `with` block at once

    t1 = threading.Thread(target=worker, name="workspace-a")
    t2 = threading.Thread(target=worker, name="workspace-b")
    t1.start()
    t2.start()
    t1.join(timeout=3)
    t2.join(timeout=3)

    # If this were still a Lock (capacity 1), the barrier would time out
    # because the second thread can't enter until the first releases.
    assert len(entered) == 2


def test_semaphore_still_bounds_total_concurrency(monkeypatch):
    """Resource protection must survive the fix — not unlimited concurrency."""
    mod = _reload_jobs_with_limit(monkeypatch, 2)
    max_concurrent_seen = [0]
    current = [0]
    lock = threading.Lock()

    def worker():
        with mod._run_serial_lock:
            with lock:
                current[0] += 1
                max_concurrent_seen[0] = max(max_concurrent_seen[0], current[0])
            time.sleep(0.05)
            with lock:
                current[0] -= 1

    threads = [threading.Thread(target=worker) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    assert max_concurrent_seen[0] <= 2


def test_default_limit_is_three_when_unset(monkeypatch):
    monkeypatch.delenv("REHEARSE_MAX_CONCURRENT_RUNS", raising=False)
    importlib.reload(jobs_module)
    assert jobs_module._MAX_CONCURRENT_RUNS == 3
