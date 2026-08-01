# Craftium SmallRoom development smoke test

Date: 2026-08-02 (Asia/Singapore)  
QuestPilot code commit under test: `54bbe0ad6027460f1b493dc7c4c28e36aa8e00d2`  
Craftium source: `https://github.com/mikelma/craftium` at
`8eb8707cb756df47e76131a0058ab724d2383c76`

## Scope and safety

This was a development-only, CPU-only infrastructure smoke test. It did **not**
train a policy, inspect held-out seeds, score the pre-registered claims, contact
a commercial game, use an account, expose a service, or make a paid API call.
The environment was `Craftium/SmallRoom-v0`, a local Luanti world. Ten fixed
development seeds (`1000`--`1009`) each received twenty deterministic actions.

## Worker and retention

The test used the already-running Vast.ai container `45525865` through its
direct SSH endpoint. It reported 56 vCPU, 64 GB RAM, four RTX 3060 GPUs, and
`workspace_is_volume=false`. GPU compute was not used. The worker began with
about 11 GB free and finished with 8.6 GB free. Because no volume was attached,
the two remote logs were copied back immediately after completion.

No worker was rented, created, started, stopped, resized, recycled, or
destroyed. Incremental project spend was US$0.00; the worker's pre-existing
provider billing is outside this smoke-test spend statement.

## Commands and build path

The bounded remote session was named
`questpilot-craftium-smoke-buildfix-20260802`. It used an automatic stop if
workspace free space fell below 4 GiB.

1. Install the documented Ubuntu build dependencies in an isolated ephemeral
   workspace.
2. Clone Craftium recursively, check out the pinned source SHA, and initialize
   submodules.
3. Create a Python 3.12 virtual environment and install the package
   dependencies.
4. Configure `cmake . -DRUN_IN_PLACE=TRUE -DCMAKE_BUILD_TYPE=Release
   -DUSE_SDL2_SHARED=TRUE`, then run `make -j12`.
5. Stage the generated Luanti `bin` and required assets into the Craftium Python
   package, write the package-data manifest, and reinstall the wheel.
6. Run ten `gymnasium.make("Craftium/SmallRoom-v0")` reset/step episodes.

The corrected packaged wheel SHA-256 was
`67c4ae6e2b808857017a986f24634ba24cc03726baab65d0ffe4b4965c83b0a3`.

## Result

PASS. All ten episodes initialized a `64 x 64 x 3` RGB observation and completed
twenty deterministic transitions, for 200 transitions total. Each episode
returned a reward sum of `-20.0`; none terminated or truncated during the
twenty-step smoke horizon. The game-environment portion took 4.319 seconds.

This validates only the engine, RGB observation, reset, and discrete-action
path. It is not evidence of PPO performance, QuestPilot safety performance, or
any SOTA comparison.

## Failure and recovery

The first `pip install .` produced a Python wheel without
`craftium/luanti/bin`, causing `FileNotFoundError` during environment creation.
The project includes a separate `build_craftium.sh` that compiles Luanti and
stages runtime assets before packaging. The successful retry performed that
documented staging process with a Linux-compatible CMake configuration.

Retrieved audit-log SHA-256 values:

- Initial failed build log:
  `11d08f20fcec77c2d8ddfeb5680dca1b7262fb0f467cdebc22f5539b3fcb2067`
- Successful retry log:
  `86d30bb54c87a9cc95b4e3780c0abb8527ed282e9efea92c93a86eebdd3a3475`

## Next action

Implement and freeze the PPO-CNN development baseline configuration on
development seeds only. Do not begin held-out SafeChores evaluation until source
and dependency lockfiles, action vocabulary, generated manifests, and evaluator
cost definitions are committed in a superseding protocol freeze.
