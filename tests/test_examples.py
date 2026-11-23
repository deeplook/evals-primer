"""Run every numbered lesson offline in a subprocess and require an OK: line."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = sorted((ROOT / "examples").glob("[0-9][0-9]_*.py"))


def test_lessons_exist() -> None:
    assert EXAMPLES, "no numbered lessons found"


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda path: path.name)
def test_lesson_runs_offline(example: Path, tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(example)],
        cwd=ROOT,
        env=os.environ
        | {
            "OPENAI_API_KEY": "",
            "INSPECT_LOG_DIR": str(tmp_path),
            "EVALS_SCORES": str(tmp_path / "scores.json"),
        },
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, f"{example.name}: {result.stderr}"
    assert "OK:" in result.stdout or "SKIP:" in result.stdout


def test_live_model_default_and_env_override() -> None:
    environment = os.environ | {"OPENAI_API_KEY": "unused-test-key"}
    environment.pop("EVALS_MODEL", None)
    command = [
        sys.executable,
        "-c",
        "from _shared import live_model; print(live_model())",
    ]
    for settings, expected in (
        (environment, "openai/gpt-6-luna"),
        (environment | {"EVALS_MODEL": "openai/gpt-6.1-terra"}, "openai/gpt-6.1-terra"),
    ):
        result = subprocess.run(
            command,
            cwd=ROOT / "examples",
            env=settings,
            text=True,
            capture_output=True,
            timeout=30,
            check=True,
        )
        assert result.stdout.strip() == expected


def test_gate_fails_the_build_on_a_regression(tmp_path: Path) -> None:
    command = [sys.executable, str(ROOT / "examples" / "21_ci_gate.py"), "--gate"]
    env = os.environ | {
        "OPENAI_API_KEY": "",
        "INSPECT_LOG_DIR": str(tmp_path),
        "EVALS_SCORES": str(tmp_path / "scores.json"),
    }
    passing = subprocess.run(
        command, cwd=ROOT, env=env, capture_output=True, text=True, check=False
    )
    failing = subprocess.run(
        [*command, "--regressed"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert passing.returncode == 0, passing.stderr
    assert failing.returncode == 1
    assert "FAIL: regressed misses the gate" in failing.stdout
