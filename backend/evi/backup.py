"""Consistent backup and verified restore of Evi state (database + immutable artifacts).

  python -m evi.backup create <dest_dir>      # online SQLite backup API (safe while API/worker run) + artifacts + manifest
  python -m evi.backup verify <backup_dir>    # recompute every hash
  python -m evi.backup restore <backup_dir> <empty_data_dir>   # verify, then restore; refuses a non-empty target

Sources (public/sources or EVI_SOURCES_DIR) are registered by hash and can be re-downloaded; they are copied too so a
restore is self-contained. The Docling model cache is not backed up (re-downloadable, ~0.5 GB).
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from .config import settings


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def create(dest: Path, data_dir: Path | None = None, sources_dir: Path | None = None) -> dict:
    data_dir = data_dir or settings.data_dir
    sources_dir = sources_dir or settings.sources_dir
    dest = dest / datetime.now(timezone.utc).strftime("evi-backup-%Y%m%dT%H%M%SZ")
    dest.mkdir(parents=True)
    src = sqlite3.connect(f"file:{(data_dir / 'evi.sqlite3').as_posix()}?mode=ro", uri=True)
    dst = sqlite3.connect(dest / "evi.sqlite3")
    src.backup(dst)
    dst.close()
    src.close()
    files = {"evi.sqlite3": _sha(dest / "evi.sqlite3")}
    for sub, base in (("artifacts", data_dir / "artifacts"), ("sources", sources_dir)):
        if base.exists():
            for p in sorted(base.rglob("*")):
                if p.is_file():
                    rel = Path(sub) / p.relative_to(base)
                    (dest / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, dest / rel)
                    files[rel.as_posix()] = _sha(dest / rel)
    integrity = sqlite3.connect(dest / "evi.sqlite3").execute("PRAGMA integrity_check").fetchone()[0]
    man = {"created_at": datetime.now(timezone.utc).isoformat(), "integrity_check": integrity, "files": files}
    (dest / "MANIFEST.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    return {"backup": str(dest), "files": len(files), "integrity_check": integrity}


def verify(bdir: Path) -> list[str]:
    man = json.loads((bdir / "MANIFEST.json").read_text(encoding="utf-8"))
    bad = [rel for rel, h in man["files"].items() if not (bdir / rel).exists() or _sha(bdir / rel) != h]
    if man.get("integrity_check") != "ok":
        bad.append("sqlite integrity_check was not ok at backup time")
    return bad


def restore(bdir: Path, data_dir: Path, sources_dir: Path | None = None) -> dict:
    bad = verify(bdir)
    if bad:
        raise SystemExit(f"backup verification failed: {bad[:5]}")
    if data_dir.exists() and any(data_dir.iterdir()):
        raise SystemExit(f"{data_dir} is not empty; refusing to overwrite")
    data_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bdir / "evi.sqlite3", data_dir / "evi.sqlite3")
    if (bdir / "artifacts").exists():
        shutil.copytree(bdir / "artifacts", data_dir / "artifacts")
    if sources_dir and (bdir / "sources").exists():
        sources_dir.mkdir(parents=True, exist_ok=True)
        for p in (bdir / "sources").iterdir():
            if not (sources_dir / p.name).exists():
                shutil.copy2(p, sources_dir / p.name)
    n = rebase(data_dir, force=True)
    c = sqlite3.connect(data_dir / "evi.sqlite3")
    ok = c.execute("PRAGMA integrity_check").fetchone()[0]
    c.close()
    return {"restored_to": str(data_dir), "integrity_check": ok, "parses_rebased": n}


def _basename(path: str) -> str:
    """Basename for paths recorded on ANY OS (a Windows path is not split by PurePosixPath on Linux)."""
    return re.split(r"[\\/]", path)[-1]


def rebase(data_dir: Path, force: bool = False) -> int:
    """Point parse artifact paths at data_dir/artifacts/parses. Idempotent: without force, only rows whose recorded
    file is missing AND whose basename exists under data_dir are updated. Returns the number of rows changed."""
    db_path = data_dir / "evi.sqlite3"
    if not db_path.exists():
        return 0
    c = sqlite3.connect(db_path)
    changed = 0
    for pid, path in c.execute("SELECT parse_id, artifact_path FROM parses").fetchall():
        new = data_dir / "artifacts" / "parses" / _basename(path)
        if str(new) != path and (force or (not Path(path).exists() and new.exists())):
            c.execute("UPDATE parses SET artifact_path=? WHERE parse_id=?", (str(new), pid))
            changed += 1
    c.commit()
    c.close()
    return changed


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "create":
        print(json.dumps(create(Path(a[1])), indent=1))
    elif a[0] == "verify":
        bad = verify(Path(a[1]))
        print("VERIFIED" if not bad else f"FAILED: {bad}")
        sys.exit(1 if bad else 0)
    elif a[0] == "rebase":
        print(json.dumps({"parses_rebased": rebase(Path(a[1]))}))
    elif a[0] == "restore":
        print(json.dumps(restore(Path(a[1]), Path(a[2]), Path(a[3]) if len(a) > 3 else None), indent=1))
