# QuestPilot-Safe mechanism theory (pre-experiment)

## M1 — calibrated action gating

- **Observation to test:** screen ambiguity and visual shifts can make a single
  state prediction unreliable.
- **Hypothesis:** an action gate calibrated on a disjoint calibration split will
  reduce unsafe autonomous execution by escalating ambiguous state/action pairs.
- **Intervention:** remove the calibrated gate while holding the planner and
  action allowlist fixed.
- **Affected stratum:** SC-CLAIM, SC-REC, and SC-OOD.
- **Falsifier:** no reduction in unsafe-task rate, or the reduction comes only
  from near-zero autonomous coverage.
- **Conditional guarantee:** only empirical, and only for the frozen task/action
  distribution; it is not a guarantee for commercial games.

## M2 — explicit recovery state

- **Observation to test:** delayed or conflicting observations can cause a
  reactive policy to repeat an already-invalid transition.
- **Hypothesis:** an explicit state machine with monotonic recovery transitions
  improves completion and lowers action-limit stops after an interruption.
- **Intervention:** remove explicit state/recovery while keeping perception and
  confidence threshold fixed.
- **Affected stratum:** SC-REC and SC-LONG.
- **Falsifier:** no predicted recovery benefit on the affected stratum.
- **Conditional guarantee:** applies only when all actions remain in the
  allowlist and evaluator state is hidden from the policy.
