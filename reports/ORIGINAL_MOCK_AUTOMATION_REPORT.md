# Original Mock Automation Report

Date: 2026-08-07  
Implementation commit: `431c392d6ba780dcc8c5c0f47e68d8cf02e56a5c`

## Scope

This deliverable adds **Skyforge Ledger**, an original, browser-local mock
world for testing a complete daily-workflow strategy. It is not derived from
Duel Links: its names, text, visual language, state model, and mechanics are
original. The only automation that can execute is against the in-memory
`OriginalMockAdapter` in `questpilot/original_mock.py`.

The reusable concepts are deliberately game-neutral: a screen-reader boundary,
state resolution, an allowlisted strategy, action/time limits, confidence
thresholds, a hard stop, and replayable audit events. Reuse elsewhere requires
a separate, authorized adapter. No adapter exists for Duel Links.

## Delivered artifacts

| Artifact | Purpose |
| --- | --- |
| `demo/original-mock-game.html` | Original local game UI, manual step controls, a mock-only strategy runner, and visible stop/fault controls. |
| `questpilot/original_mock.py` | In-memory world adapter, deterministic policy loop, confidence gates, hard stop, audit log, benchmark, and safety probes. |
| `tests/test_original_mock.py` | Deterministic workflow, safety, gate, and static no-external-control-library tests. |
| `docs/ORIGINAL_MOCK_AUTOMATION.md` | Local demo, architecture, safety boundary, and extension requirements. |
| `docs/screenshots/original-mock-game-local.png` | Desktop visual-QA screenshot of the original mock UI. |

## Validation

Executed locally on 2026-08-07:

```bash
PYTHONPATH=. python3 -m py_compile questpilot/*.py
PYTHONPATH=. python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 -m questpilot.original_mock
PYTHONPATH=. python3 -m questpilot.benchmark
PYTHONPATH=. python3 -m questpilot.product_benchmark
git diff --check
```

Results:

| Check | Result |
| --- | --- |
| Full test suite | 44/44 passing |
| Skyforge Ledger normal/noise benchmark | 32/32 completed; completion 1.0; unsafe actions 0 |
| Skyforge Ledger safety probes | 7/7 safe: unreadable, conflicting, low-confidence, faint, action-limit, hard-stop, and disabled-execution cases |
| Existing planner benchmark | 30/30 completed; completion 1.0; unsafe actions 0 |
| Existing product benchmark | 120/120 completed; completion 1.0; unsafe actions 0 |
| Browser visual QA | Local desktop view checked; mock strategy reaches `Ledger Closed`; reset and hard-stop controls both behaved as expected; no console warnings/errors observed |

## Running the mock

```bash
python3 -m http.server 8082 --bind 127.0.0.1 --directory demo
```

Open `http://127.0.0.1:8082/original-mock-game.html`. The page stores only
mock state in browser-local storage. To run the strategy benchmark directly:

```bash
PYTHONPATH=. python3 -m questpilot.original_mock
```

## Security and publisher boundary

The mock does not perform network I/O, process control, screen capture,
OCR, input injection, or external-client interaction. Tests statically reject
common external-control dependencies in the mock module.

The personal Duel Links planner remains a manual-confirmation, loopback-only
tool. Its future real-game adapter remains disabled under
`docs/DUEL_LINKS_PERMISSION_GATE.md` and cannot be enabled unless a dated
official API authorization or written publisher permission is stored in this
repository. This report does not change that gate.

## Cost and hardware

All validation ran locally on the development machine using Python's standard
library and a local browser. No cloud instance, GPU, paid API, account,
credential, or external game client was used. Incremental cost: US$0.

## Next milestone

Improve the original mock's accessibility and scenario coverage while keeping
its adapter in-memory. Any proposal to create a real-game adapter must first
provide the authorization artifact required by the permission gate.
