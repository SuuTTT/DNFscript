# Luanti local test-world adapter

Luanti (formerly Minetest) is a free, open-source voxel-game platform with a
publisher-supported Lua mod API. This adapter is the zero-cost runnable target
for QuestPilot; it does **not** run Minecraft Education code and it does not
attach to any commercial game.

## Install and enable

1. Install Luanti from its official download page and create a **local
   singleplayer** world. Do not join a public server.
2. Copy this whole `questpilot_luanti` folder to Luanti's user `mods/` folder
   (the engine's documented user path contains locally installed mods/worlds).
3. In the world creation or configuration screen, enable
   `questpilot_luanti`, then enter the local world.
4. Stand on a flat, clear, eight-node lane and face down the lane. Use:

   ```text
   /qp_seed
   /qp_start
   /qp_step     # repeat manually up to eight times
   /qp_status
   /qp_stop     # hard kill switch
   ```

`/qp_seed` creates only eight non-solid, invisible test tokens. `/qp_step`
removes only the next expected test token. A missing/unexpected node, the
16-action cap, completion, or `/qp_stop` produces `SAFE_STOP` and disables the
session. The commands refuse to run outside a singleplayer world.

## Why this is safe to test

The mod uses Luanti's documented server-side Lua API and local command system;
there is no screen scraper, credential storage, web request, anti-cheat,
payment, chat automation, trading, PvP, or public-server path. Its visible
messages are local operator status, not player-chat automation.

- [Official Luanti documentation](https://docs.luanti.org/)
- [Official modding guide](https://docs.luanti.org/for-creators/creating-mods/)
- [Official Lua API](https://api.luanti.org/)
