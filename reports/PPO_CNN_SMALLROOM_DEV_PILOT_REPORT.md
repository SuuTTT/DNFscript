# PPO-CNN SmallRoom development pilot

Date: 2026-08-02 (Asia/Singapore)
Scope: development only; no held-out SafeChores seeds, commercial game, account,
GPU compute, paid API, new rental, or instance lifecycle action.

## Frozen configuration

- Runner/config commit: `69587bf3993f37ae368f1526e022fb728c6dc5bf`
- Training-model commit: `57861173802e460b7f25e02f6a3803d8fc1e3482`
- Evaluation-adapter commit: `f852a3dd3b60a8cefbc2c2448a9c87817f6d57af`
- Craftium: `8eb8707cb756df47e76131a0058ab724d2383c76`
- Environment: `Craftium/SmallRoom-v0`, RGB `64 x 64 x 3`, native four-action
  vocabulary (`nop`, `forward`, `mouse x+`, `mouse x-`)
- Device: CPU; `torch 2.6.0+cpu`, `torch.cuda.is_available() == false`
- PPO: requested 10,000 steps; Stable-Baselines3 collected 10,240 because
  `n_steps=256`; five evaluation seeds: 10--14 (all development seeds)

## Worker and data handling

The run used existing Vast.ai container `45525865` through direct SSH in tmux
sessions `questpilot-ppo-smallroom-pilot-20260802`,
`questpilot-ppo-smallroom-retry-20260802`, and
`questpilot-ppo-smallroom-eval-20260802`. The worker reported 56 vCPU, 64 GB
RAM, and `workspace_is_volume=false`; GPU hardware was allocated by the existing
instance but never used. A 128 MiB workspace write test and the CPU PyTorch host
probe passed. Free space stayed above the 4 GiB stop threshold (7.5--7.6 GB at
the pilot/evaluation stages). Logs, manifest, model, and evaluation JSON were
copied back immediately.

No capacity was rented, created, started, stopped, resized, recycled, or
destroyed. Incremental project spend was US$0.00; existing instance billing is
not represented as new project spend.

## Result

Training completed at roughly 121--135 steps/second. The saved model was then
evaluated deterministically on seeds 10--14. All five episodes truncated at the
500-step limit with reward `-500.0`; no episode terminated. Mean return was
`-500.0`, completion was `0/5`, and there is no learning-performance claim.

This is a valid negative development pilot: the runner, model save, CPU
execution, RGB environment, and evidence-copy path work, but the frozen 10k-step
configuration does not solve SmallRoom.

## Failures and recovery

1. Commit `69587bf`: after 10,240 training steps, evaluation passed a
   zero-dimensional NumPy action to Craftium's wrapper, which attempted to
   iterate it. The manifest and log were preserved.
2. Commit `5786117`: the first compatibility fix converted that action to a
   list. Craftium accepts a scalar discrete action for one environment, so the
   underlying environment rejected the list. The model had already been saved.
3. Commit `f852a3d`: evaluation converts one-element predictions to a Python
   integer. The saved model then evaluated successfully without retraining.

Retrieved evidence SHA-256 values:

- First training attempt log: `86734e26a32dc06d05d1dfc60c33f8e490e855fe9a42758115a5f28d096c7b3d`
- Second training attempt log: `3cd31c541c9cba5c695e48a23666ad2a54da2a18ffdac713829ffea664605b09`
- Saved model: `aa2340ff752d6eabfed08781077b9c7f83695c51faf41ede2859bfb56a4a636d`
- Final evaluation JSON: `b2f085601461dec28dd968c3acb768ff6720d01fc4a78387d8d02608d9268f63`
- Final evaluation log: `d988357411245fad4160f4a1517c657c7b722fb23cc07ed9c8e0fe3bfd9e47f1`

## Next action

Tune only on development seeds: record a bounded learning-curve sweep and a
separate random-policy control, then freeze the selected PPO-CNN configuration
before comparing PPO+LSTM, CPO-vision, or QuestPilot-Safe. Do not inspect the
held-out split during this work.
