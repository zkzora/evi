"""Server-side configuration. Secrets are read from the environment / backend/.env only and never logged."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(BACKEND / ".env")


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.environ.get("EVI_DATA_DIR", str(ROOT / "data" / "runs")))
    sources_dir: Path = Path(os.environ.get("EVI_SOURCES_DIR", str(ROOT / "public" / "sources")))
    serv_api_key: str = os.environ.get("SERV_API_KEY", "")
    serv_base_url: str = os.environ.get("SERV_BASE_URL", "https://inference-api.openserv.ai/v1")
    serv_model: str = os.environ.get("SERV_MODEL", "gpt-5.4-mini")
    serv_timeout_s: int = _int("SERV_TIMEOUT_S", 180)
    serv_max_completion_tokens: int = _int("SERV_MAX_COMPLETION_TOKENS", 6000)
    reppo_api_key: str = os.environ.get("REPPO_API_KEY", "")
    reppo_base_url: str = os.environ.get("REPPO_BASE_URL", "https://eval.reppo.xyz/api/v1")
    reppo_timeout_s: int = _int("REPPO_TIMEOUT_S", 30)
    # Server-wide execution switch. Default OFF: provider calls and new public jobs need EVI_EXECUTION_ENABLED=true.
    execution_enabled: bool = os.environ.get("EVI_EXECUTION_ENABLED", "false").strip().lower() in ("1", "true", "yes")
    # Public compute bounds
    max_revisions_per_run: int = _int("EVI_MAX_REVISIONS_PER_RUN", 2)
    max_evaluations_per_run: int = _int("EVI_MAX_EVALUATIONS_PER_RUN", 2)
    session_jobs_per_hour: int = _int("EVI_SESSION_JOBS_PER_HOUR", 12)
    global_serv_calls_per_day: int = _int("EVI_GLOBAL_SERV_CALLS_PER_DAY", 40)
    global_reppo_evals_per_day: int = _int("EVI_GLOBAL_REPPO_EVALS_PER_DAY", 10)
    worker_lease_s: int = _int("EVI_WORKER_LEASE_S", 120)
    job_max_attempts: int = _int("EVI_JOB_MAX_ATTEMPTS", 3)
    allowed_origins: tuple[str, ...] = tuple(o for o in os.environ.get(
        "EVI_ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:4173").split(",") if o)

    @property
    def db_path(self) -> Path:
        return self.data_dir / "evi.sqlite3"

    @property
    def artifacts_dir(self) -> Path:
        return self.data_dir / "artifacts"


settings = Settings()
