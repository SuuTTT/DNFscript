# QuestPilot business gate

Phase 1 is an offline safety prototype, not a consumer game-automation
service. No commercial-game connector may be sold, piloted, or published
without a publisher-approved integration and separate human approval.

| Option | Allowed discovery now | Gate to proceed | Excluded scope | Phase 1 disposition |
|---|---|---|---|---|
| Accessibility subscription | Test accessibility UX in the local mock: enlarged labels, narrated state, consent and stop controls. | Written publisher permission for game/region; accessibility/privacy review; opt-in assistive interaction that never evades anti-cheat. | Unattended completion, farming, ranked/PvP play, credentials, payments, chat, trading. | **Research only; no sale or integration.** |
| B2B QA automation | Use the deterministic mock and test harness for a studio's own pre-release build. | Contract from build owner; isolated test environment; studio-owned test accounts; allowlists and audit retention. | Live public shards, player accounts, economy manipulation, anti-cheat bypass. | **Most viable path** after a studio contract. |
| Developer-approved integrations | Design an adapter contract around an official API or explicit written approval. | Publisher agreement defining endpoints, rate limits, data handling, permitted actions, and revocation. | Screen scraping/input injection against commercial games, reverse engineering, mods, non-approved APIs. | **Blocked pending approval.** |

## Non-negotiable exclusions

QuestPilot will not support account farming, account resale/transfer, boosting,
unattended competitive play, PvP automation, payments, chat, trading,
credential collection, CAPTCHA/anti-cheat bypass, paid APIs, or rented
compute. The $0 Phase 1 budget is satisfied solely by local Python standard
library execution.

## Decision

Do not commercialize a game chore assistant. Develop only the offline mock and
QA-oriented safety tooling until a developer-owned test build or official
publisher integration supplies written authority.
