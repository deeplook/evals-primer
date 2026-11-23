# Architecture decision records

Short records of decisions that shape more than one lesson. Lesson-level detail
belongs in the lesson docstring.

| ADR | Decision |
|---|---|
| [0001](0001-inspect-as-harness.md) | Use Inspect as the eval harness |
| [0002](0002-offline-lessons-test-the-scorer.md) | Offline lessons plant failures and test the scorer |
| [0003](0003-agents-sdk-as-system-under-test.md) | The Agents SDK is the system under test; ownership among primers |
| [0004](0004-garak-via-uvx.md) | Run garak through uvx, not as a dependency |
| [0005](0005-script-only-primer-layout.md) | Script-only primer layout and local endpoints |
| [0006](0006-run-modes-and-assertions.md) | What each run mode asserts |
| [0007](0007-fixtures-inline-and-non-actionable.md) | Fixtures are inline, hand-written, and never actionable |
| [0008](0008-grade-effects-and-report-trade-offs.md) | Grade executed effects, and never report a safety number alone |
| [0009](0009-model-roles.md) | Target, judge, and attacker are separate model roles |
