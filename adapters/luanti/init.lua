-- QuestPilot Luanti adapter: local, singleplayer test-world only.
-- It registers local control commands, never connects to a server, and only
-- removes its own questpilot_luanti:token nodes from a seeded test lane.

local mt = core
local QP_MAX_ACTIONS = 16
local QP_MAX_STEPS = 8
local sessions = {}

mt.log("action", "[questpilot_luanti] loaded; local singleplayer guard active")

mt.register_node("questpilot_luanti:token", {
    description = "QuestPilot Test Token",
    drawtype = "airlike",
    walkable = false,
    pointable = false,
    diggable = false,
    buildable_to = true,
    paramtype = "light",
    sunlight_propagates = true,
    groups = {not_in_creative_inventory = 1},
})

local function tell(name, message)
    mt.log("action", "[questpilot_luanti] " .. name .. " | " .. message)
    mt.chat_send_player(name, "QuestPilot | " .. message)
end

local function local_world_only(name)
    if mt.is_singleplayer() then return true end
    tell(name, "SAFE_STOP | local singleplayer world required")
    return false
end

local function horizontal_direction(player)
    local look = player:get_look_dir()
    if math.abs(look.x) >= math.abs(look.z) then
        return {x = look.x >= 0 and 1 or -1, y = 0, z = 0}
    end
    return {x = 0, y = 0, z = look.z >= 0 and 1 or -1}
end

local function next_pos(session)
    return vector.add(session.cursor, session.direction)
end

local function safe_stop(name, reason)
    local session = sessions[name]
    if session then session.active = false end
    tell(name, "SAFE_STOP | " .. reason)
end

mt.register_chatcommand("qp_seed", {
    description = "Create an eight-token QuestPilot test lane in front of you.",
    func = function(name)
        if not local_world_only(name) then return false end
        local player = mt.get_player_by_name(name)
        if not player then return false, "player not found" end
        local origin = vector.round(player:get_pos())
        local direction = horizontal_direction(player)
        for step = 1, QP_MAX_STEPS do
            local position = vector.add(origin, vector.multiply(direction, step))
            if mt.get_node(position).name ~= "air" then
                return false, "SAFE_STOP | lane must be clear before qp_seed"
            end
            mt.set_node(position, {name = "questpilot_luanti:token"})
        end
        tell(name, "READY | seeded 8 invisible non-solid test tokens; run /qp_start")
        return true
    end,
})

mt.register_chatcommand("qp_start", {
    description = "Start a bounded QuestPilot test-lane collection session.",
    func = function(name)
        if not local_world_only(name) then return false end
        local player = mt.get_player_by_name(name)
        if not player then return false, "player not found" end
        sessions[name] = {
            active = true,
            actions = 0,
            steps = 0,
            cursor = vector.round(player:get_pos()),
            direction = horizontal_direction(player),
        }
        tell(name, "READY | run /qp_step one time at a time; /qp_stop ends immediately")
        return true
    end,
})

mt.register_chatcommand("qp_step", {
    description = "Human-approved QuestPilot collection step (maximum eight).",
    func = function(name)
        if not local_world_only(name) then return false end
        local session = sessions[name]
        if not session or not session.active then
            tell(name, "approval_required | run /qp_start before /qp_step")
            return false
        end
        if session.actions + 2 > QP_MAX_ACTIONS then
            safe_stop(name, "action_limit")
            return false
        end
        if session.steps >= QP_MAX_STEPS then
            safe_stop(name, "collection_complete")
            return true
        end
        local position = next_pos(session)
        local node = mt.get_node_or_nil(position)
        if not node or node.name ~= "questpilot_luanti:token" then
            safe_stop(name, "unexpected_or_missing_test_token_requires_human_review")
            return false
        end
        mt.remove_node(position)
        session.cursor = position
        session.actions = session.actions + 2 -- observe + allowlisted collect
        session.steps = session.steps + 1
        tell(name, "ACTION | collect_test_token | step=" .. session.steps)
        if session.steps == QP_MAX_STEPS then safe_stop(name, "collection_complete") end
        return true
    end,
})

mt.register_chatcommand("qp_stop", {
    description = "QuestPilot hard kill switch.",
    func = function(name)
        safe_stop(name, "hard_kill_switch")
        return true
    end,
})

mt.register_chatcommand("qp_status", {
    description = "Show the bounded QuestPilot session state.",
    func = function(name)
        local session = sessions[name]
        if not session then return false, "QuestPilot | no active session" end
        tell(name, "STATUS | active=" .. tostring(session.active) .. " | actions=" .. session.actions .. " | steps=" .. session.steps)
        return true
    end,
})
