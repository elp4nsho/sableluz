-- Sable de Luz encendido: mientras alguien lo tiene en la mano
--   * ilumina con el color de SU cristal alrededor (una luz de cell que lo sigue casilla a casilla)
--   * zumba (loop) y suena al encenderse / apagarse
-- Generado por build_sableluz.py.

-- fulltype -> color/alcance de la luz. Cubre todos los colores y los dos largos de sable.
local SABERS = {
    ["SL.SableLuz"] = { r=1.00, g=0.12, b=0.09, radius=4 },
    ["SL.SableLuzDoble"] = { r=1.00, g=0.12, b=0.09, radius=5 },
    ["SL.SableLuz_Blue"] = { r=0.24, g=0.55, b=1.00, radius=4 },
    ["SL.SableLuzDoble_Blue"] = { r=0.24, g=0.55, b=1.00, radius=5 },
    ["SL.SableLuz_Green"] = { r=0.24, g=0.82, b=0.35, radius=4 },
    ["SL.SableLuzDoble_Green"] = { r=0.24, g=0.82, b=0.35, radius=5 },
    ["SL.SableLuz_Purple"] = { r=0.67, g=0.31, b=0.92, radius=4 },
    ["SL.SableLuzDoble_Purple"] = { r=0.67, g=0.31, b=0.92, radius=5 },
    ["SL.SableLuz_Yellow"] = { r=0.98, g=0.80, b=0.16, radius=4 },
    ["SL.SableLuzDoble_Yellow"] = { r=0.98, g=0.80, b=0.16, radius=5 },
    ["SL.SableLuz_Orange"] = { r=1.00, g=0.55, b=0.16, radius=4 },
    ["SL.SableLuzDoble_Orange"] = { r=1.00, g=0.55, b=0.16, radius=5 },
    ["SL.SableLuz_White"] = { r=0.92, g=0.92, b=0.94, radius=4 },
    ["SL.SableLuzDoble_White"] = { r=0.92, g=0.92, b=0.94, radius=5 },
}

local state = {}      -- jugador -> { light, x, y, z, hum, col }

local function saberColor(item)
    if not item or item:getCondition() <= 0 then return nil end
    return SABERS[item:getFullType()]
end

local function heldColor(player)
    if not player or player:isDead() then return nil end
    -- ojo: ipairs({a, b}) se corta en el primer nil; se revisan las dos manos por separado
    return saberColor(player:getPrimaryHandItem()) or saberColor(player:getSecondaryHandItem())
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
    local col = heldColor(player)
    if not col then
        if d then switchOff(player, d, not player:isDead()) end
        return
    end
    if not d then                                   -- recien encendido
        d = {}
        state[player] = d
        play(player, "SableLuzOn")
    end
    -- luz: se mueve cuando cambia la casilla, o se vuelve a crear si cambio el color del cristal
    local x, y, z = math.floor(player:getX()), math.floor(player:getY()), math.floor(player:getZ())
    if not d.light or d.x ~= x or d.y ~= y or d.z ~= z or d.col ~= col then
        removeLight(d)
        local ok, light = pcall(function() return getCell():addLamppost(x, y, z, col.r, col.g, col.b, col.radius) end)
        if ok and light then d.light, d.x, d.y, d.z, d.col = light, x, y, z, col end
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
