# QuestPilot product UI track v1

Date: 2026-08-06 (Asia/Singapore)  
Scope: deterministic, offline, in-memory UI simulator only. No commercial
title, account, credential, real UI input, payment, trading, chat, PvP,
portal-EC2 execution, cloud capacity, or network access is involved.

## What was built

`questpilot/ui_product.py` is a product-track vertical slice, intentionally
separate from Craftium/Luanti navigation research:

1. A game-like UI simulator with login, home, quest list/detail, quest
   collection, rewards, character screen, upgrade recommendation, and offline
   upgrade-confirmation screens.
2. A deterministic screen-token renderer plus OCR-confidence surrogate, which
   maps each rendered screen to one explicit UI state or `UNKNOWN`.
3. Inspectable behavior-tree workflows for quest-and-reward, reward-only, and
   upgrade-recommendation tasks.
4. Append-only audit events containing screen hashes, parsed state, behavior
   leaf, action, execution mode, and recommendation data.
5. Dry-run default, action/time limits, action allowlist, confidence gate,
   unknown-state stop, and a product-specific hard kill switch.

This is not pixel OCR yet: the screen representation is a deterministic token
renderer that simulates OCR confidence and ambiguity. The next perception
milestone must replace it with screenshots plus an offline OCR/layout adapter
while preserving the same state and safety interfaces.

## Character-enhancement policy

The default task is `UPGRADE_RECOMMENDATION`: it reads an offline character
screen and emits `POWER_PLUS_5`, cost 100 soft tokens, with no resource change.
Executing the offline mock upgrade requires both `allow_upgrade_execution=True`
and a per-action human approval callback. Real-money, payment, trading, and
production-game upgrade execution are outside this product track and remain
blocked.

## Fixed benchmark result

`python3 -m questpilot.product_benchmark` ran 120 deterministic workflows:

| Workflow | Count | Completion | Unsafe actions |
| --- | ---: | ---: | ---: |
| Quest read → collect → reward claim | 60 | 60/60 | 0 |
| Reward claim | 30 | 30/30 | 0 |
| Upgrade recommendation | 30 | 30/30 | 0 |
| **Total** | **120** | **120/120 (100%)** | **0** |

Product-specific perturbations also passed: unreadable UI, conflicting labels,
low confidence, faint action labels, action limit, hard kill switch, and an
unapproved upgrade all safe-stopped without an unsafe input.

## Verification and next action

- Full project suite: 29 tests passed.
- Earlier fixed Phase-1 chore suite remains 30/30 with zero unsafe actions.
- Incremental cost: US$0.00.

Next: add a raster screenshot renderer and offline OCR/layout parser, then
expand the benchmark with delayed loads, stale screens, localization, and
modal-overlap perturbations. Keep character upgrades recommendation-only until
an authorized developer-owned QA build explicitly grants a narrow execution
scope.
