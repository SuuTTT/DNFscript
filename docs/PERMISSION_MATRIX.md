# QuestPilot permission matrix

Status date: **2026-08-01**. This is a product gate, not legal advice. A row
may become eligible only when the publisher supplies current written approval
for the exact integration and region. Until then, QuestPilot has no adapter,
credentials, network client, capture backend, or input driver for these games.

| Target | Official source (dated) | Automation / bots | API, mod, or third-party program | Account transfer | Commercial use | Phase 1 decision |
|---|---|---|---|---|---|---|
| Pokémon GO | [Niantic Terms](https://nianticlabs.com/terms), accessed 2026-08-01; [Player Guidelines](https://nianticlabs.com/guidelines?hl=en), accessed 2026-08-01 | Prohibited: Terms expressly list automation software and bots among disallowed access methods. | No public chore-automation API evidenced; modified/unofficial software is disallowed. | Sale, transfer, or exchange of virtual goods is prohibited; Guidelines flag account trading. | Licence is personal and non-commercial; paid in-app services/account resale are prohibited. | **BLOCKED** — no adapter, unattended play, PvP, account or item handling. |
| Yu-Gi-Oh! Duel Links | [Konami Duel Links Terms, revised 2026-05-28](https://legal.konami.com/kde/yugioh_duellinks/terms/tou/view/ko/); [official terms](https://legal.konami.com/kde/yugioh_duellinks/terms/tou/view/zh-tw/), accessed 2026-08-01 | Prohibited: Terms call out automation software, bots, and automated control. | Unauthorized third-party software, cheats, hacks, and mods are prohibited; no approved chore API evidenced. | Official device data transfer exists, but account/data sales, lending, and unapproved transfers are prohibited. | Terms prohibit commercial exploitation of the app/access. | **BLOCKED** — competitive game and explicit bot prohibition. |
| Dungeon Fighter Online (DFO) | [DFO Terms/EULA, updated July 2026](https://www.dfoneople.com/policy/tou); [DFO Community Rules](https://www.dfoneople.com/policy/communityrules), accessed 2026-08-01 | Unauthorized programs/devices that affect the game are disallowed; macro/bot-style chores are not permitted. | Unauthorized programs include tools/devices beyond normal listed peripherals; protocol interception and data mining are prohibited. | Accounts cannot be bought, sold, gifted, traded, or transferred between players. | Virtual goods may not be sold/transferred for value; no commercial automation licence evidenced. | **BLOCKED** — original scripts are legacy context only; no live execution or adapter. |
| Honor of Kings | [Honor of Kings EULA](https://www.honorofkings.com/policy/cookies/es/service_es.html), accessed 2026-08-01; [2025 World Cup rulebook](https://www.honorofkings.com/esports/kwc/rule.html), accessed 2026-08-01 | Bots, automated control, trainers, and automation programs interacting with services are prohibited. | Mods, hacks, cheats, and third-party add-ons are prohibited; no developer-approved automation API evidenced. | Licence is non-transferable; competitive rules prohibit account manipulation and credential sharing. | Personal-entertainment licence only; ancillary offerings/commercial use barred absent publisher permission. | **BLOCKED** — competitive MOBA; no PvP automation. |
| PUBG Mobile | [PUBG Mobile EULA](https://www.pubgmobile.com/terms/ARA/), accessed 2026-08-01; [official anti-cheat notice](https://www.pubgmobile.com/webplat/info/news_version3/35372/57705/57706/59487/59488/59489/m22591/202305/935096.shtml), accessed 2026-08-01 | Prohibited: bots, automated control, trainers, and automation programs that interact with services. | Unauthorized third-party programs, mods, hacks, cheats, and add-ons are prohibited. | Licence/virtual goods are personal and non-transferable; account sharing is penalized in official guidance. | Personal non-commercial use only; leveling services and ancillary offerings are specifically prohibited. | **BLOCKED** — competitive game and express automation ban. |

## Enforcement rule

`BLOCKED` means the target cannot be connected, observed, logged into,
instrumented, or controlled. It also blocks credential handling, CAPTCHA or
anti-cheat interaction, chat, trading, payments, account farming/resale, and
unattended competitive play. A future proposal requires publisher-written
approval, a scoped contract, a privacy/security review, and separate human
approval before code is written.
