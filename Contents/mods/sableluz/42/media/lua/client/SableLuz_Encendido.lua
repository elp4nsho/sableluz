-- Sable de Luz encendido: mientras alguien lo tiene en la mano
--   * ilumina con su color alrededor (una luz de cell que lo sigue casilla a casilla)
--   * zumba (loop) y suena al encenderse / apagarse
-- Generado por build_sableluz.py.

local SABER = "SL.SableLuz"
local R, G, B = 1.00, 0.16, 0.10
local RADIUS = 4

local state = {}      -- jugador -> { light, x, y, z, hum }

local function isSaber(item)
    return item and item:getFullType() == SABER and item:getCondition() > 0
end

local function holding(player)
    if not player or player:isDead() then return false end
    -- ojo: ipairs({a, b}) se corta en el primer nil; se revisan las dos manos por separado
    return isSaber(player:getPrimaryHandItem()) or isSaber(player:getSecondaryHandItem())
end

local function emitter(player)
    local ok, e = pcall(function() return player:getEmitter() end)
    return ok and e or nil
end

local function play(player, name)
    local e = emitter(player)
    if not e then return nil end
    local ok, id = pcall(function() return e:playSound(name) end)
    return ok and id or nil
end

local function removeLight(d)
    if d.light then
        pcall(function() getCell():removeLamppost(d.light) end)
        d.light = nil
    end
end

local function switchOff(player, d, sound)
    removeLight(d)
    if d.hum then
        local e = emitter(player)
        if e then pcall(function() e:stopSound(d.hum) end) end
        d.hum = nil
    end
    if sound then play(player, "SableLuzOff") end
    state[player] = nil
end

local function update(player)
    local d = state[player]
    if not holding(player) then
        if d then switchOff(player, d, not player:isDead()) end
        return
    end
    if not d then                                   -- recien encendido
        d = {}
        state[player] = d
        play(player, "SableLuzOn")
    end
    -- luz: se mueve cuando cambia la casilla
    local x, y, z = math.floor(player:getX()), math.floor(player:getY()), math.floor(player:getZ())
    if not d.light or d.x ~= x or d.y ~= y or d.z ~= z then
        removeLight(d)
        local ok, light = pcall(function() return getCell():addLamppost(x, y, z, R, G, B, RADIUS) end)
        if ok and light then d.light, d.x, d.y, d.z = light, x, y, z end
    end
    -- zumbido: si termino (o el juego no lo repite solo), se vuelve a lanzar
    local e = emitter(player)
    if e then
        local playing = false
        if d.hum then
            local ok, p = pcall(function() return e:isPlaying(d.hum) end)
            playing = ok and p
        end
        if not playing then d.hum = play(player, "SableLuzHum") end
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
    for p, d in pairs(state) do
        if not seen[p] then switchOff(p, d, false) end
    end
end

-- al guardar se quitan las luces (para que no queden grabadas en el mapa); el siguiente tick las
-- vuelve a poner. El estado se mantiene: no suena de nuevo el encendido y el zumbido sigue.
local function clearAll()
    for _, d in pairs(state) do removeLight(d) end
end

Events.OnTick.Add(onTick)
Events.OnSave.Add(clearAll)
Events.OnPlayerDeath.Add(function(player)
    local d = state[player]
    if d then switchOff(player, d, false) end
end)
