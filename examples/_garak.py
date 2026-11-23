"""Read a garak report into attack-success numbers this repo can gate on.

garak writes one JSON object per line to `<prefix>.report.jsonl`. Each `eval`
entry summarises one probe/detector pair: `fails` counts attempts where the
detector found the attack's goal in the reply (a hit), `passed` counts the
attempts the model resisted, and `confidence_lower`/`confidence_upper` bound
the hit rate (garak bootstraps them). Checked against garak 0.17.1.

`SAMPLE_REPORT` is a hand-written report in that shape, with summary lines
only and no attack text (ADR 0007), so the parser is tested offline.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

GARAK_DIR = Path(__file__).resolve().parents[1] / "out" / "garak"


@dataclass(frozen=True)
class ProbeResult:
    probe: str
    detector: str
    hits: int
    total: int
    ci_low: float | None
    ci_high: float | None

    @property
    def attack_success(self) -> float:
        return self.hits / self.total if self.total else 0.0


def read_report(lines: Iterable[str]) -> list[ProbeResult]:
    """Every probe/detector summary in a garak report, in file order."""
    results = []
    for line in lines:
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("entry_type") != "eval":
            continue
        results.append(
            ProbeResult(
                probe=str(entry["probe"]),
                detector=str(entry["detector"]),
                hits=int(entry["fails"]),
                total=int(entry["total_evaluated"]),
                ci_low=entry.get("confidence_lower"),
                ci_high=entry.get("confidence_upper"),
            )
        )
    return results


def read_report_file(path: Path) -> list[ProbeResult]:
    with path.open(encoding="utf-8") as handle:
        return read_report(handle)


def latest_report(directory: Path = GARAK_DIR) -> Path | None:
    """The newest `*.report.jsonl` that `make redteam` wrote, if any."""
    reports = sorted(directory.glob("*.report.jsonl"), key=lambda p: p.stat().st_mtime)
    return reports[-1] if reports else None


def _eval_line(probe: str, detector: str, passed: int, fails: int) -> str:
    total = passed + fails
    return json.dumps(
        {
            "entry_type": "eval",
            "probe": probe,
            "detector": detector,
            "passed": passed,
            "fails": fails,
            "nones": 0,
            "total_evaluated": total,
            "total_processed": total,
            "confidence_lower": None,
            "confidence_upper": None,
        }
    )


SAMPLE_REPORT = "\n".join(
    [
        json.dumps({"entry_type": "init", "garak_version": "0.17.1"}),
        json.dumps({"entry_type": "attempt", "probe_classname": "sample.Marker"}),
        _eval_line(
            "promptinject.HijackHateHumans", "promptinject.AttackRogueString", 60, 40
        ),
        _eval_line("dan.DanInTheWild", "mitigation.MitigationBypass", 45, 5),
        json.dumps({"entry_type": "completion"}),
    ]
)
