# Aetherfold Arena: original card-duel playground

`demo/skyforge-card-duel.html` is a self-contained, original browser card
game. It is a play surface for turn sequencing and deterministic opponent
logic—not a client, clone, adapter, or guide for a commercial title.

## Play

1. Select one card from **Your hand**.
2. Click an empty friendly lane to deploy it, paying its displayed energy cost.
3. Click **End round**. The deterministic practice rival renews energy, may
   summon one original unit, and resolves its lane attacks.
4. On your next turn, click a ready friendly unit. It attacks the rival unit in
   the same lane, or the rival core if that lane is clear.
5. Reduce the rival core from 20 to zero. **New practice duel** resets only the
   synthetic browser-local state.

Rules are intentionally compact and original: three lanes, six maximum energy,
unit power/guard, same-lane exchanges, and core damage through an open lane.
The opponent is a deterministic local function, not unattended play against a
real service.

## Boundary

The page contains no network request, account, login, game capture/OCR,
keyboard/mouse bridge, protocol inspection, or external-game adapter. It uses
original Aetherfold card names and rules. It must not be used to control Duel
Links or another commercial game.

The matching deterministic rules model is `questpilot/card_duel_mock.py` and
its tests are `tests/test_card_duel_mock.py`.
