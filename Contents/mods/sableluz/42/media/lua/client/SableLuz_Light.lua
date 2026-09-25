-- Sable de Luz: el sable encendido en la mano ilumina con su color alrededor de quien lo lleva.
-- Se usa una luz de cell (addLamppost) que sigue al jugador casilla a casilla.
-- Generado por build_sableluz.py.

local SABER = "SL.SableLuz"
local R, G, B = 1.00, 0.16, 0.10
local RADIUS = 4

local lights = {}

local function holding(player)
    if not player or player:isDead() then return false end
    for _, item in ipairs({ player:getPrimaryHandItem(), player:getSecondaryHandItem() }) do
        if item and item:getFullType() == SABER and item:getCondition() > 0 then
            return true
        end
    end
    return false
end

local function removeLight(key)
    local d = lights[key]
    if d then
        pcall(function() getCell():removeLamppost(d.light) end)
        lights[key] = nil
    end
end

local function update(player)
    if holding(player) then
        local x, y, z = math.floor(player:getX()), math.floor(player:getY()), math.floor(player:getZ())
        local d = lights[player]
        if not d or d.x ~= x or d.y ~= y or d.z ~= z then
            removeLight(player)
            local ok, light = pcall(function() return getCell():addLamppost(x, y, z, R, G, B, RADIUS) end)
            if ok and light then
                lights[player] = { light = light, x = x, y = y, z = z }
            end
        end
    else
        removeLight(player)
    end
end

local function players()
    local list = {}
    if isClient() then
        local online = getOnlinePlayers()
        if online then
            for i = 0, online:size() - 1 do list[#list + 1] = online:get(i) end
        end
    else
        for i = 0, getNumActivePlayers() - 1 do
            local p = getSpecificPlayer(i)
            if p then list[#list + 1] = p end
        end
    end
    return list
end

local tick = 0
local function onTick()
    tick = tick + 1
    if tick % 5 ~= 0 then return end
    local seen = {}
    for _, p in ipairs(players()) do
        seen[p] = true
        update(p)
    end
    for key in pairs(lights) do
        if not seen[key] then removeLight(key) end
    end
end

-- al guardar se apagan (se vuelven a encender solas en el siguiente tick)
local function clearAll()
    for key in pairs(lights) do removeLight(key) end
end

Events.OnTick.Add(onTick)
Events.OnSave.Add(clearAll)
Events.OnPlayerDeath.Add(function(player) removeLight(player) end)
