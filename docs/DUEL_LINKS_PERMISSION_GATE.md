# Duel Links permission gate

Status date: **2026-08-07**. This is a product-scope control, not legal advice.

QuestPilot’s Duel Links feature is a **private, local-first manual planner**.
It stores user-entered chores, reset times, rewards, streaks, and manual
completion confirmations in the local browser only. It does not communicate
with, observe, log into, or control Duel Links.

## Phase 1 allowed surface

- Manually entered daily and weekly checklist items.
- Local reminders, reset calculations, streaks, rewards, unfinished tasks, and
  a shortest-duration suggested order.
- A human pressing a local **Confirm manually** button after doing a task.
- An original offline synthetic workflow simulator and deterministic tests.

## Hard boundary

The following remain prohibited: credentials or login handling; live-client
capture or OCR; clicks, keyboard events, duels, farming, or unattended play;
protocol inspection, reverse engineering, memory access, packet interception,
anti-cheat/CAPTCHA bypass or evasion; purchases, trading, resale, or a
commercial service. Konami artwork, UI, text, and assets are not copied.

## Disabled future-adapter gate

There is no Duel Links adapter in this repository. The only placeholder is
`DuelLinksPermissionGate`, which returns disabled by default. A future adapter
may be considered only after a repository file under
`docs/authorizations/duel_links/` contains both:

1. a dated (`YYYY-MM-DD`) primary authorization record; and
2. either `OFFICIAL_API_AUTHORIZATION` or
   `WRITTEN_PUBLISHER_PERMISSION` describing the exact permitted integration,
   region, environment, and capability scope.

Even then, the gate merely makes evidence review possible. It does not enable
credentials, live input, capture, or a production adapter without a separate
implementation and human-approval review.
