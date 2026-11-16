"""Reference labels must not be reachable from any inference path (docs/20 §4)."""
from pathlib import Path

INFERENCE = ["extraction.py", "revision.py", "evaluation.py", "binding.py", "providers.py", "worker.py", "api.py", "parsing.py", "checks.py", "certify.py"]


def test_inference_modules_never_mention_reference_labels():
    root = Path(__file__).resolve().parents[1] / "evi"
    for name in INFERENCE:
        src = (root / name).read_text(encoding="utf-8").lower()
        assert "references-v1" not in src and "data/references" not in src and ".scoring" not in src and "import scoring" not in src, name


def test_experiment_only_hashes_reference_file():
    src = (Path(__file__).resolve().parents[1] / "evi" / "experiment.py").read_text(encoding="utf-8")
    uses = [l for l in src.splitlines() if "REFERENCES" in l and not l.strip().startswith("#")]
    assert all("_sha(REFERENCES)" in l or l.startswith("REFERENCES =") for l in uses), uses
