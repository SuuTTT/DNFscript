# Original mock automation lane

Date: **2026-08-07**. `Skyforge Ledger` is an original, browser-local and
in-memory daily-loop game used only to test QuestPilot's reusable planning and
safety logic.

## What runs

`questpilot/original_mock.py` supplies both sides of the simulation:

- `OriginalMockAdapter` owns an original world with the Horizon Atrium, Scout
  Route, Sunglass Rift, Relic Shelf, and Star Seal Vault.
- `OriginalMockAutomation` can execute only the adapter's typed in-memory
  actions. It has no generic desktop, browser, mobile, capture, credential,
  input, network, or client integration.
- `MockScreenReader`, `MockStateResolver`, and `MockStrategy` are deliberately
  separable so another **authorized** developer-owned test adapter could reuse
  policy concepts without inheriting any external control capability.

The browser counterpart is `demo/original-mock-game.html`. It provides manual
steps, a visible mock-only strategy run, screen-condition probes, hard stop,
and browser-local audit history. Launch it only on loopback:

```bash
python3 -m http.server 8082 --bind 127.0.0.1 --directory demo
```

Open <http://127.0.0.1:8082/original-mock-game.html>.

## Deterministic loop

```text
Horizon Atrium → Scout Route → Field Cache → Horizon Atrium
                → Sunglass Rift → Relic Shelf → Horizon Atrium
                → Star Seal Vault → Ledger Closed
```

The default loop resolves two patrol echoes and three rift waves, then claims
an original mock reward. The fixed suite contains 32 variations with harmless
decorative noise. It is not a model of a publisher game or a transfer-ready
automation flow.

## Safety invariants

- A hard stop runs before every observation/action.
- Non-unique, unreadable, low-confidence, and uncertain-action mock screens
  safe-stop and add audit events.
- Action allowlists and a maximum action count are enforced.
- Disabling mock execution never mutates the adapter.
- Audit action records include a screen hash, action, mode, and adapter name.

Run the checks:

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 -m questpilot.original_mock
```

## Non-goal and future boundary

This module is not an adapter template for a commercial title. Any future real
integration stays disabled behind the repository's authorization gate and
requires dated official API authorization or written publisher permission,
plus a new scope and security review. Duel Links remains blocked.
