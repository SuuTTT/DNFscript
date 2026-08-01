/*
 * QuestPilot Minecraft Education adapter (MakeCode JavaScript / TypeScript).
 *
 * Run only in a world you own or are authorized to use. This deliberately
 * uses the publisher-supported Agent API, not screen scraping or injected
 * input. It is human-stepped: one `qp_step` command performs at most two
 * allowlisted actions, so the learner can inspect the visible world each time.
 *
 * Setup: choose a flat, empty 8-block collection lane. Stand at its start,
 * open Code Builder, select JavaScript, paste this file, then type:
 *   qp_start
 *   qp_step   (repeat up to 8 times)
 *   qp_stop   (immediate safe stop between steps)
 */

const QP_MAX_ACTIONS = 16
const QP_MAX_STEPS = 8
let qpActive = false
let qpActions = 0
let qpSteps = 0

function qpAudit(message: string) {
    player.say("QuestPilot | " + message)
}

function qpSafeStop(reason: string) {
    qpActive = false
    qpAudit("SAFE_STOP | " + reason + " | actions=" + qpActions + " | steps=" + qpSteps)
}

function qpCanAct(requiredActions: number): boolean {
    if (!qpActive) {
        qpAudit("approval_required | run qp_start before qp_step")
        return false
    }
    if (qpActions + requiredActions > QP_MAX_ACTIONS) {
        qpSafeStop("action_limit")
        return false
    }
    return true
}

player.onChat("qp_start", function () {
    qpActive = true
    qpActions = 0
    qpSteps = 0
    agent.teleportToPlayer()
    qpAudit("READY | human approval required for each qp_step | max_actions=" + QP_MAX_ACTIONS)
})

player.onChat("qp_step", function () {
    if (!qpCanAct(2)) return
    if (qpSteps >= QP_MAX_STEPS) {
        qpSafeStop("collection_complete")
        return
    }
    // Native detection is the adapter's high-confidence observation. A block
    // in the lane is uncertain/unapproved for this collection scenario.
    if (agent.detect(AgentDetection.Block, SixDirection.Forward)) {
        qpSafeStop("blocked_path_requires_human_review")
        return
    }
    agent.move(SixDirection.Forward, 1)
    qpActions += 1
    agent.collectAll()
    qpActions += 1
    qpSteps += 1
    qpAudit("ACTION | move_forward + collect_nearby | step=" + qpSteps)
    if (qpSteps === QP_MAX_STEPS) qpSafeStop("collection_complete")
})

player.onChat("qp_stop", function () {
    qpSafeStop("hard_kill_switch")
})

player.onChat("qp_status", function () {
    qpAudit("STATUS | active=" + qpActive + " | actions=" + qpActions + " | steps=" + qpSteps)
})
