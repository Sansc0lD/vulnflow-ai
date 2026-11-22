#!/usr/bin/env python3
"""Container entrypoint for VulnFlow AI API and Celery worker."""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec: B404
import sys
import time
from pathlib import Path

MAX_RETRIES = 5
RETRY_DELAY = 2.0

# Ensure virtualenv bin directory is in PATH
_VENV_BIN = Path("/app/.venv/bin")
if _VENV_BIN.is_dir() and str(_VENV_BIN) not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{_VENV_BIN}:{os.environ.get('PATH', '')}"


def _run_migrations() -> None:
    print("[*] Applying Alembic database migrations...", flush=True)
    ini_path = "apps/api/alembic.ini" if Path("apps/api/alembic.ini").is_file() else "alembic.ini"

    # Prefer direct binary, fall back to sys.executable -m alembic
    resolved = shutil.which("alembic")
    if not resolved and (_VENV_BIN / "alembic").is_file():
        resolved = str(_VENV_BIN / "alembic")

    alembic_cmd = [resolved] if resolved else [sys.executable, "-m", "alembic"]

    for attempt in range(1, MAX_RETRIES + 1):
        res = subprocess.run(  # nosec: B603
            [*alembic_cmd, "-c", ini_path, "upgrade", "head"],
            check=False,
        )
        if res.returncode == 0:
            print("[+] Migrations applied successfully.", flush=True)
            return
        if attempt < MAX_RETRIES:
            print(
                f"[!] Migration attempt {attempt}/{MAX_RETRIES} failed. "
                f"Retrying in {RETRY_DELAY}s...",
                flush=True,
            )
            time.sleep(RETRY_DELAY)
        else:
            print("[-] FATAL: Failed to apply migrations after max attempts.", flush=True)
            sys.exit(res.returncode)


def main() -> None:
    raw_cmd = (
        sys.argv[1:]
        if len(sys.argv) > 1
        else ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]  # nosec: B104
    )
    if raw_cmd[0] in {"uvicorn", "gunicorn"} or "uvicorn" in raw_cmd[0]:
        _run_migrations()

    target = raw_cmd[0]
    resolved = shutil.which(target)
    if not resolved and (_VENV_BIN / target).is_file():
        resolved = str(_VENV_BIN / target)

    exec_args = [resolved, *raw_cmd[1:]] if resolved else [sys.executable, "-m", *raw_cmd]

    # Hand off execution directly to target process
    os.execvp(exec_args[0], exec_args)  # nosec: B606


if __name__ == "__main__":
    main()


