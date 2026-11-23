"""Exact match: score recorded answers against a labelled set, no model at all.

An eval needs labelled inputs, answers, and a scorer that compares them. Here
the answers are a fixed recorded list, so the only thing under test is the
scorer. Two answers are wrong on purpose and one right answer is wrapped in a
sentence. A strict scorer flags all three; a scorer that first extracts the
value with a regex flags only the two real errors. The lesson raises unless
each scorer flags exactly what it should.

agents-primer lessons 36–38 measure routing on three fixed cases; this lesson
starts there and tests the scorer itself before trusting its numbers.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from _qa import FORMAT_ONLY, ITEMS, LAST_TOKEN, PLANTED

Scorer = Callable[[str, str], bool]


def exact(answer: str, target: str) -> bool:
    return answer.strip() == target


def extracted(answer: str, target: str) -> bool:
    found = re.search(LAST_TOKEN, answer)
    return found is not None and found.group(1).casefold() == target.casefold()


def flagged(scorer: Scorer) -> set[str]:
    return {item.id for item in ITEMS if not scorer(item.scripted, item.target)}


def main() -> None:
    by_exact = flagged(exact)
    by_regex = flagged(extracted)
    if by_exact != PLANTED | FORMAT_ONLY:
        raise AssertionError(f"exact flagged {sorted(by_exact)}")
    if by_regex != PLANTED:
        raise AssertionError(f"regex flagged {sorted(by_regex)}, planted {PLANTED}")
    accuracy = 1 - len(by_regex) / len(ITEMS)
    print(
        f"OK: exact flagged {len(by_exact)}, regex flagged {len(by_regex)}; "
        f"caught {len(PLANTED)}/{len(PLANTED)} planted errors, "
        f"accuracy={accuracy:.2f}"
    )


if __name__ == "__main__":
    main()
