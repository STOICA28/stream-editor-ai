"""
Unit tests for causal negative controls (EXP-002).
Automated executable assertions ensuring that CandidateRelationClassifier
and EventClusterer never merge unrelated events even within temporal bounds.
"""
import importlib.util
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT_PATH = ROOT_DIR / "scripts" / "test_causal_controls.py"

spec = importlib.util.spec_from_file_location("causal_controls_runner", str(SCRIPT_PATH))
assert spec is not None and spec.loader is not None
causal_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(causal_mod)


def test_causal_controls_executable_assertions():
    """Run all 8 automated causal relation assertions."""
    verdicts = causal_mod.run_all_causal_controls()
    assert len(verdicts) == 8
    for name, result in verdicts.items():
        assert result == "PASSED", f"Control {name} failed: {result}"
