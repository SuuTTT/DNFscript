# QuestPilot-Safe claim/evidence map

Status: pre-experiment. No result claim is currently supported.

| Claim | Required evidence | Current status | Prohibited shortcut |
| --- | --- | --- | --- |
| C1: safer under visual shift without unacceptable completion loss | Held-out paired episode records, prespecified PPO-CNN and CPO-vision comparisons, 95% paired-bootstrap intervals, raw audit logs, and frozen policy/checkpoint provenance | Not run | Quoting Craftium, Voyager, or Horizon Imagination scores from their different interfaces |
| C2: calibration escalates rather than guessing | Held-out SC-CLAIM/SC-REC/SC-OOD logs with autonomous coverage, approvals, conditional unsafe execution, and the prespecified threshold | Not run | Reporting zero unsafe actions by abstaining on every episode |
| Mechanism: explicit state improves recovery | Prespecified removal ablation on SC-REC/SC-LONG with per-episode failures | Not run | Calling a debugging observation a causal mechanism |

Every future headline number must link to a `RESULTS_LEDGER.jsonl` record,
the raw episode logs, aggregation command, source commit, dataset manifest,
and output table/figure.
