#!/usr/bin/env python3
"""Unified Development & Testing Orchestrator for VulnFlow AI.

Single-entrypoint command runner that works identically across Windows,
macOS, and Linux (PowerShell, Bash, CMD).

Features:
  - 1 COMMAND TO RUN EVERYTHING: `uv run python scripts/dev.py`
    (Brings up Docker, applies migrations, starts Celery, launches API server).
  - 1 COMMAND FULL DEMO: `uv run python scripts/dev.py demo`
    (Starts server, runs E2E setup, downloads scanner, scans API, pushes findings).
  - Automatically loads `.env` so you never have to specify `--env-file .env`.
  - Port conflict detection with graceful fallback.

Usage:
  uv run python scripts/dev.py                  # Run all services (default: up)
  uv run python scripts/dev.py up               # Run all services
  uv run python scripts/dev.py demo             # Full automated test run
  uv run python scripts/dev.py migrate          # Run database migrations
  uv run python scripts/dev.py server           # Run only API server
  uv run python scripts/dev.py worker           # Run only Celery worker
  uv run python scripts/dev.py test-e2e         # Run CLI scan & push against live server
  uv run python scripts/dev.py status           # Check Docker & port connectivity
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import socket
import subprocess  # nosec: B404
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_env_file(env_path: Path) -> None:
    """Load key-value pairs from .env into os.environ if not already set."""
    if not env_path.is_file():
        return
    with env_path.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, _, val = stripped.partition("=")
            key = key.strip()
            val = val.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = val


# Load .env upfront before any subcommand logic
_load_env_file(ROOT / ".env")


def _is_port_in_use(host: str, port: int) -> bool:
    """Check if a local port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def _wait_for_socket(host: str, port: int, timeout_sec: float = 10.0) -> bool:
    """Poll a host:port until it accepts a TCP connection or times out."""
    start = time.time()
    while time.time() - start < timeout_sec:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect((host, port))
                return True
            except OSError:
                time.sleep(0.3)
    return False


def _ensure_docker_services() -> bool:
    """Attempt to bring up docker-compose services if docker is available."""
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return False
    try:
        res = subprocess.run(  # nosec: B603
            [docker_bin, "compose", "up", "-d"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        return res.returncode == 0
    except (FileNotFoundError, OSError):
        return False


def _build_env() -> dict[str, str]:
    """Build environment with full PYTHONPATH across all submodules."""
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    paths = [
        str(ROOT),
        str(ROOT / "apps" / "api"),
        str(ROOT / "apps" / "cli"),
        str(ROOT / "packages" / "contracts"),
    ]
    if existing_pythonpath:
        paths.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def _run_subcommand(cmd: list[str], *, cwd: Path | None = None) -> int:
    """Run an external command inheriting environment and I/O streams."""
    result = subprocess.run(  # nosec: B603
        cmd,
        cwd=cwd or ROOT,
        env=_build_env(),
        check=False,
    )
    return result.returncode


def cmd_migrate(args: argparse.Namespace) -> int:
    """Run database migrations via Alembic."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("[-] DATABASE_URL is not set. Ensure .env exists in project root.", file=sys.stderr)
        return 1

    print("[*] Running Alembic migrations (upgrade head)...")
    ini_path = ROOT / "apps" / "api" / "alembic.ini"
    code = _run_subcommand(
        [sys.executable, "-m", "alembic", "-c", str(ini_path), "upgrade", "head"],
        cwd=ROOT / "apps" / "api",
    )
    if code == 0:
        print("[+] Migrations applied successfully.")
    else:
        print("[-] Migration failed. Check if PostgreSQL container is running.", file=sys.stderr)
    return code


def cmd_server(args: argparse.Namespace) -> int:
    """Start the FastAPI backend with Uvicorn."""
    host = args.host
    port = args.port

    if _is_port_in_use(host, port):
        if getattr(args, "auto_port", True):
            fallback_port = 8001 if port == 8000 else port + 1
            print(
                f"[!] Port {port} is in use; auto-switching to port {fallback_port}.",
                file=sys.stderr,
            )
            port = fallback_port
        else:
            print(
                f"[-] Port {port} on {host} is already in use. Use --port to specify another port.",
                file=sys.stderr,
            )
            return 1

    print(f"[*] Starting VulnFlow API at http://{host}:{port} ...")
    print(f"    - Swagger Docs: http://{host}:{port}/docs")
    print(f"    - Healthcheck:  http://{host}:{port}/health")

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if getattr(args, "reload", True):
        cmd.append("--reload")

    return _run_subcommand(cmd, cwd=ROOT / "apps" / "api")


def cmd_worker(args: argparse.Namespace) -> int:
    """Start Celery report worker."""
    broker_url = os.environ.get("CELERY_BROKER_URL") or os.environ.get("REDIS_URL")
    if not broker_url:
        print("[-] CELERY_BROKER_URL or REDIS_URL not set in .env.", file=sys.stderr)
        return 1

    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "app.workers.celery_app",
        "worker",
        f"--loglevel={args.loglevel}",
    ]
    # On Windows, prefork is unsupported in Celery 5; use solo pool
    pool = "solo" if platform.system() == "Windows" else "prefork"
    if platform.system() == "Windows":
        cmd.extend(["-P", "solo"])

    print(f"[*] Starting Celery worker (pool: {pool})...")
    return _run_subcommand(cmd, cwd=ROOT / "apps" / "api")


def _run_e2e_setup(api_url: str, email: str, password: str) -> tuple[str, str] | None:
    """Register/login, create workspace + project + API key, and configure CLI."""
    import httpx

    client = httpx.Client(base_url=api_url, timeout=10.0)

    # 1. Health check
    try:
        r = client.get("/health")
        if r.status_code != 200:
            print(f"[-] API at {api_url} returned status {r.status_code}", file=sys.stderr)
            return None
    except Exception as exc:
        print(f"[-] Could not connect to API at {api_url}: {exc}", file=sys.stderr)
        return None

    # 2. Register or Login
    register_payload = {
        "email": email,
        "password": password,
        "full_name": "Dev Tester",
        "workspace_name": "Dev Test Agency",
    }
    resp = client.post("/api/v1/auth/register", json=register_payload)
    if resp.status_code == 201:
        data = resp.json()
        print(f"[+] Registered account: {email}")
        token = data["access_token"]
        workspace_id = data["workspace_id"]
    elif resp.status_code == 409:
        login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        login_resp.raise_for_status()
        login_data = login_resp.json()
        token = login_data["access_token"]
        workspace_id = login_data["workspaces"][0]["id"]
        print(f"[+] Account exists, logged in as: {email}")
    else:
        print(f"[-] Auth failed: {resp.status_code} - {resp.text}", file=sys.stderr)
        return None

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Project
    proj_resp = client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        headers=headers,
        json={
            "name": "E2E Test Project",
            "client_name": "Local Test Client",
            "target_scope": ["127.0.0.1", "localhost"],
            "roe_start_date": "2026-11-01T00:00:00Z",
            "roe_end_date": "2026-12-01T00:00:00Z",
        },
    )
    proj_resp.raise_for_status()
    project_id = str(proj_resp.json()["id"])
    print(f"[+] Project created: {project_id}")

    # 4. Issue API Key
    key_resp = client.post(
        f"/api/v1/workspaces/{workspace_id}/api-keys",
        headers=headers,
        json={"label": "E2E automated key"},
    )
    key_resp.raise_for_status()
    api_key = str(key_resp.json()["api_key"])
    print("[+] API Key issued.")

    # 5. Configure CLI
    sys.path.insert(0, str(ROOT / "apps" / "cli"))
    from vulnflow.config import CLIConfig, save_config

    config_path = save_config(
        CLIConfig(api_url=api_url, api_key=api_key, active_workspace_id=workspace_id)
    )
    print(f"[+] CLI configured at {config_path}")

    return project_id, workspace_id


def cmd_setup(args: argparse.Namespace) -> int:
    """Setup project credentials and configure vulnflow CLI."""
    res = _run_e2e_setup(args.api_url.rstrip("/"), args.email, args.password)
    if res is None:
        return 1
    project_id, _ = res
    print(f"PROJECT_ID={project_id}")
    return 0


def cmd_test_e2e(args: argparse.Namespace) -> int:
    """Run full automated E2E test: setup -> setup-tools -> scan -> push."""
    api_url = args.api_url.rstrip("/")
    target = args.target or api_url
    output_file = Path(args.output)

    print("[*] STEP 1/4: Setting up test account, project, and CLI config...")
    res = _run_e2e_setup(api_url, args.email, args.password)
    if res is None:
        return 1
    project_id, _ = res

    print("\n[*] STEP 2/4: Ensuring scanner binary (setup-tools)...")
    code = _run_subcommand([sys.executable, "-m", "vulnflow", "setup-tools"])
    if code != 0:
        print("[-] setup-tools failed.", file=sys.stderr)
        return code

    print(f"\n[*] STEP 3/4: Scanning target ({target}) ...")
    code = _run_subcommand(
        [
            sys.executable,
            "-m",
            "vulnflow",
            "scan",
            "--target",
            target,
            "--output",
            str(output_file),
        ]
    )
    if code != 0:
        print("[-] Scanning failed.", file=sys.stderr)
        return code

    print(f"\n[*] STEP 4/4: Pushing findings to project {project_id} ...")
    code = _run_subcommand(
        [
            sys.executable,
            "-m",
            "vulnflow",
            "push",
            "--project",
            project_id,
            "--type",
            "nuclei",
            "--file",
            str(output_file),
        ]
    )
    if code == 0:
        print("\n[+] SUCCESS: E2E pipeline completed successfully!")
    return code


def cmd_up(args: argparse.Namespace) -> int:
    """All-in-one command: Docker -> Migrate -> Celery Worker -> API Server."""
    print("=" * 60)
    print("  VulnFlow AI — Unified All-in-One Dev Runner")
    print("=" * 60)

    # 1. Docker compose check
    print("\n[*] Step 1/4: Checking Docker containers...")
    if not _wait_for_socket("127.0.0.1", 5432, timeout_sec=1.0):
        print("    -> Starting Docker services (PostgreSQL, Redis, MinIO)...")
        _ensure_docker_services()
        if not _wait_for_socket("127.0.0.1", 5432, timeout_sec=15.0):
            print("[-] Warning: PostgreSQL (5432) is not ready yet.", file=sys.stderr)
        else:
            print("    -> PostgreSQL is ready.")
    else:
        print("    -> Docker services are already running.")

    # 2. Database migrations
    print("\n[*] Step 2/4: Applying database migrations...")
    ini_path = ROOT / "apps" / "api" / "alembic.ini"
    mig_code = _run_subcommand(
        [sys.executable, "-m", "alembic", "-c", str(ini_path), "upgrade", "head"],
        cwd=ROOT / "apps" / "api",
    )
    if mig_code != 0:
        print("[-] Migration failed. Check database connection.", file=sys.stderr)
        return mig_code
    print("    -> Migrations up to date.")

    # 3. Port check for Server
    host = args.host
    port = args.port
    if _is_port_in_use(host, port):
        port = 8001 if port == 8000 else port + 1
        print(f"    -> Port {args.port} is busy, using port {port}.")

    # 4. Celery Worker (Background Process)
    worker_cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "app.workers.celery_app",
        "worker",
        "--loglevel=warning",
    ]
    if platform.system() == "Windows":
        worker_cmd.extend(["-P", "solo"])

    print("\n[*] Step 3/4: Spawning background Celery worker...")
    worker_proc = subprocess.Popen(  # nosec: B603
        worker_cmd,
        cwd=ROOT / "apps" / "api",
        env=_build_env(),
    )

    # 5. API Server (Foreground Process)
    print("\n[*] Step 4/4: Launching FastAPI API server...")
    print(f"\n{'=' * 60}")
    print(f"  VulnFlow AI API is LIVE at http://{host}:{port}")
    print(f"  - Swagger UI:   http://{host}:{port}/docs")
    print(f"  - Health check: http://{host}:{port}/health")
    print("  Press Ctrl+C to stop all services.")
    print(f"{'=' * 60}\n")

    server_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if getattr(args, "reload", True):
        server_cmd.append("--reload")

    try:
        server_proc = subprocess.Popen(  # nosec: B603
            server_cmd,
            cwd=ROOT / "apps" / "api",
            env=_build_env(),
        )
        server_proc.wait()
    except KeyboardInterrupt:
        print("\n[*] Stopping services...")
    finally:
        worker_proc.terminate()
        try:
            worker_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            worker_proc.kill()
        print("[+] All services stopped cleanly.")

    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """Full one-shot demo: Docker -> Migrate -> Server -> Test-E2E."""
    print("=" * 60)
    print("  VulnFlow AI — Automated End-to-End Demo")
    print("=" * 60)

    # 1. Docker check
    print("\n[*] Step 1/5: Checking Docker containers...")
    if not _wait_for_socket("127.0.0.1", 5432, timeout_sec=1.0):
        print("    -> Starting Docker services...")
        _ensure_docker_services()
        if not _wait_for_socket("127.0.0.1", 5432, timeout_sec=15.0):
            print("[-] PostgreSQL not reachable.", file=sys.stderr)
            return 1
    print("    -> Database ready.")

    # 2. Migrations
    print("\n[*] Step 2/5: Applying migrations...")
    ini_path = ROOT / "apps" / "api" / "alembic.ini"
    _run_subcommand(
        [sys.executable, "-m", "alembic", "-c", str(ini_path), "upgrade", "head"],
        cwd=ROOT / "apps" / "api",
    )

    # 3. Start server in background
    host = "127.0.0.1"
    port = args.port
    if _is_port_in_use(host, port):
        port = 8001 if port == 8000 else port + 1

    api_url = f"http://{host}:{port}"
    print(f"\n[*] Step 3/5: Starting API server on {api_url}...")

    server_proc = subprocess.Popen(  # nosec: B603
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", host, "--port", str(port)],
        cwd=ROOT / "apps" / "api",
        env=_build_env(),
    )

    try:
        # Wait for server /health
        print("    -> Waiting for server health check...")
        if not _wait_for_socket(host, port, timeout_sec=10.0):
            print("[-] Server failed to start.", file=sys.stderr)
            return 1
        time.sleep(1.0)

        # 4. Run E2E test
        print(f"\n[*] Step 4/5: Running automated scan & push against {api_url}...")
        test_args = argparse.Namespace(
            api_url=api_url,
            target=api_url,
            output="scan_demo.jsonl",
            email=args.email,
            password=args.password,
        )
        test_code = cmd_test_e2e(test_args)
        if test_code != 0:
            print("[-] E2E test encountered an error.", file=sys.stderr)
            return test_code

        print("\n" + "=" * 60)
        print("  [+] DEMO SELESAI: Seluruh alur berhasil dijalankan!")
        print(f"  Server API tetap aktif di {api_url}/docs")
        print("  Tekan Ctrl+C untuk menghentikan server.")
        print("=" * 60 + "\n")
        server_proc.wait()
    except KeyboardInterrupt:
        print("\n[*] Stopping server...")
    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        print("[+] Done.")

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Check connectivity to PostgreSQL, Redis, and MinIO."""
    print("[*] Checking VulnFlow AI environment and services...\n")

    env_file = ROOT / ".env"
    if env_file.is_file():
        print(f"  [✓] .env file: found at {env_file}")
    else:
        print("  [✗] .env file: NOT FOUND (copy from .env.example)")

    services = [
        ("PostgreSQL", "127.0.0.1", int(os.environ.get("POSTGRES_PORT", 5432))),
        ("Redis", "127.0.0.1", int(os.environ.get("REDIS_PORT", 6379))),
        ("MinIO API", "127.0.0.1", int(os.environ.get("MINIO_API_PORT", 9000))),
        ("MinIO Console", "127.0.0.1", int(os.environ.get("MINIO_CONSOLE_PORT", 9001))),
    ]
    for name, host, port in services:
        if _is_port_in_use(host, port):
            print(f"  [✓] {name}: listening on {host}:{port}")
        else:
            print(f"  [✗] {name}: not reachable on {host}:{port} (run 'docker compose up -d')")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # up (All-in-one runner)
    sub_up = subparsers.add_parser(
        "up", help="1-command to run everything: Docker + Migrate + Celery + API"
    )
    sub_up.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    sub_up.add_argument("--port", type=int, default=8000, help="Listen port (default: 8000)")
    sub_up.add_argument(
        "--no-reload", action="store_false", dest="reload", help="Disable auto-reload"
    )
    sub_up.set_defaults(reload=True, func=cmd_up)

    # demo (Full automated demo)
    sub_demo = subparsers.add_parser(
        "demo", help="1-command full demo: Docker + Migrate + Server + Scan + Push"
    )
    sub_demo.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    sub_demo.add_argument("--email", default="manualtest@example.com", help="Test user email")
    sub_demo.add_argument("--password", default="Str0ng!Passw0rd", help="Test user password")
    sub_demo.set_defaults(func=cmd_demo)

    # migrate
    sub_migrate = subparsers.add_parser("migrate", help="Apply Alembic database migrations")
    sub_migrate.set_defaults(func=cmd_migrate)

    # server
    sub_server = subparsers.add_parser("server", help="Start FastAPI API server (Uvicorn)")
    sub_server.add_argument(
        "--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)"
    )
    sub_server.add_argument("--port", type=int, default=8000, help="Listen port (default: 8000)")
    sub_server.add_argument(
        "--auto-port",
        action="store_true",
        default=True,
        help="Auto-switch to next port if occupied (default: True)",
    )
    sub_server.add_argument(
        "--no-reload", action="store_false", dest="reload", help="Disable auto-reload"
    )
    sub_server.set_defaults(reload=True, func=cmd_server)

    # worker
    sub_worker = subparsers.add_parser("worker", help="Start Celery report compilation worker")
    sub_worker.add_argument("--loglevel", default="info", help="Celery log level (default: info)")
    sub_worker.set_defaults(func=cmd_worker)

    # setup
    sub_setup = subparsers.add_parser(
        "setup", help="Register test account, project, and CLI credentials"
    )
    sub_setup.add_argument("--api-url", default="http://127.0.0.1:8000", help="Base API URL")
    sub_setup.add_argument("--email", default="manualtest@example.com", help="Test user email")
    sub_setup.add_argument("--password", default="Str0ng!Passw0rd", help="Test user password")
    sub_setup.set_defaults(func=cmd_setup)

    # test-e2e
    sub_e2e = subparsers.add_parser(
        "test-e2e", help="Run full pipeline: setup -> setup-tools -> scan -> push"
    )
    sub_e2e.add_argument("--api-url", default="http://127.0.0.1:8000", help="Base API URL")
    sub_e2e.add_argument("--target", default="", help="Target to scan (default: matches --api-url)")
    sub_e2e.add_argument("--output", default="scan_result.jsonl", help="Scan output file path")
    sub_e2e.add_argument("--email", default="manualtest@example.com", help="Test user email")
    sub_e2e.add_argument("--password", default="Str0ng!Passw0rd", help="Test user password")
    sub_e2e.set_defaults(func=cmd_test_e2e)

    # status
    sub_status = subparsers.add_parser(
        "status", help="Check local Docker services and connectivity"
    )
    sub_status.set_defaults(func=cmd_status)

    # If no arguments provided, default to 'up' (1-command to run everything)
    if len(sys.argv) == 1:
        default_args = parser.parse_args(["up"])
        return int(default_args.func(default_args))

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
