#!/usr/bin/env python3
"""Build del mod 'sableluz' (Project Zomboid Build 42).

Genera todo dentro de Contents/mods/sableluz/42:
  - malla 3D del sable (sencillo y de doble hoja) y sus texturas, una por color de cristal
  - iconos (sables, cristales, empunaduras), poster e icono del mod
  - scripts: items, modelos, sonidos, recetas (craftRecipe) y reparacion (fixing)
  - Lua: luz de color (segun el cristal) + sonido del sable encendido, y loot
  - traducciones EN/ES (JSON de B42)

Uso:  python3 build_sableluz.py        (requiere Pillow y numpy)
El sonido de swing se toma de media/sound/SableLuzSwing.wav si ya existe; si no, se convierte
sable_sonido.mp3 con ffmpeg (o afconvert en macOS). El resto de los sonidos se sintetiza
(tools/sounds.py).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'tools'))

import icons      # noqa: E402
import saber      # noqa: E402
import sounds     # noqa: E402
import xfile      # noqa: E402

OUT = os.path.join(HERE, 'Contents', 'mods', 'sableluz', '42')
MEDIA = os.path.join(OUT, 'media')
VERSION = '1.3.0'

LIGHT_RADIUS = 4
LIGHT_RADIUS_DOBLE = 5    # dos hojas: un poco mas de alcance

# ---------------------------------------------------------------------------------- colores
# suffix='' es el cristal/sable clasico (rojo): mantiene los nombres de item de la v1.x
# (SL.SableLuz, SL.CristalKyber) para no romper partidas/recetas ya guardadas.
# weight: que tan comun es el color en el loot (1.0 = tan comun como el rojo original).
COLORS = [
    dict(suffix='', name_en='Red', name_es='Rojo', rgb=(255, 30, 24), weight=1.0),
    dict(suffix='Blue', name_en='Blue', name_es='Azul', rgb=(60, 140, 255), weight=1.0),
    dict(suffix='Green', name_en='Green', name_es='Verde', rgb=(60, 210, 90), weight=1.0),
    dict(suffix='Purple', name_en='Purple', name_es='Púrpura', rgb=(170, 80, 235), weight=0.6),
    dict(suffix='Yellow', name_en='Yellow', name_es='Amarillo', rgb=(250, 205, 40), weight=0.5),
    dict(suffix='Orange', name_en='Orange', name_es='Naranja', rgb=(255, 140, 40), weight=0.4),
    dict(suffix='White', name_en='White', name_es='Blanco', rgb=(235, 235, 240), weight=0.3),
]


def sid(base, suffix):
    """Id de item/receta/modelo: sin sufijo para el color clasico (compatibilidad), con
    sufijo '_Color' para el resto."""
    return base if not suffix else '%s_%s' % (base, suffix)


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print('  write', os.path.relpath(path, HERE))


# --------------------------------------------------------------------------- sonido
def package_sound():
    """El 'vuuum' del swing es el audio original del mod (sable_sonido.mp3); el resto se sintetiza
    (tools/sounds.py): zumbido en loop, encendido, apagado y choque. Un solo juego de sonidos
    para todos los colores y los dos largos de sable."""
    snd_dir = os.path.join(MEDIA, 'sound')
    sounds.write_all(snd_dir)
    wav = os.path.join(snd_dir, 'SableLuzSwing.wav')
    if os.path.exists(wav):
        return
    src = os.path.join(HERE, 'sable_sonido.mp3')
    for cmd in (['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-ac', '1', '-ar', '44100', wav],
                ['afconvert', '-f', 'WAVE', '-d', 'LEI16@44100', '-c', '1', src, wav]):
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return
        except Exception:
            continue
    raise SystemExit('No se pudo convertir sable_sonido.mp3 (instala ffmpeg)')


def _sound(name, wav, dist, vol, loop=False):
    return ('    sound %s\n    {\n        category = Item,\n%s'
            '        clip { file = media/sound/%s.wav, distanceMax = %d, volume = %.2f, }\n    }\n'
            % (name, '        loop = true,\n' if loop else '', wav, dist, vol))


SOUNDS = ('module Base\n{\n'
          + _sound('SableLuzSwing', 'SableLuzSwing', 20, 0.8)
          + _sound('SableLuzHit', 'SableLuzClash', 18, 1.0)
          + _sound('SableLuzBreak', 'SableLuzOff', 15, 1.0)
          + _sound('SableLuzDrop', 'SableLuzOff', 10, 0.5)
          + _sound('SableLuzOn', 'SableLuzOn', 15, 0.9)
          + _sound('SableLuzOff', 'SableLuzOff', 15, 0.8)
          + _sound('SableLuzHum', 'SableLuzHum', 8, 0.35, loop=True)
          + '}\n')


# --------------------------------------------------------------------------- items, modelos
def saber_item(item_id, model_id, weight, min_range, max_range, weapon_length, swing_time,
               max_hit_count, tree_damage, door_damage):
    return '''
    item %(id)s
    {
        DisplayCategory = Weapon,
        ItemType = base:weapon,
        Weight = %(weight).1f,
        Icon = %(id)s,
        Tooltip = Tooltip_SL_%(id)s,
        AttachmentType = Sword,
        BaseSpeed = 1.0,
        BreakSound = SableLuzBreak,
        Categories = LongBlade,
        ConditionLowerChanceOneIn = 30,
        ConditionMax = 30,
        CritDmgMultiplier = 9,
        CriticalChance = 35.0,
        DamageCategory = Slash,
        DamageMakeHole = true,
        DoorDamage = %(door)d,
        DoorHitSound = SableLuzHit,
        DropSound = SableLuzDrop,
        HitAngleMod = -30.0,
        HitFloorSound = SableLuzHit,
        HitSound = SableLuzHit,
        ImpactSound = SableLuzHit,
        KnockBackOnNoDeath = true,
        KnockdownMod = 0.0,
        MaxDamage = 14,
        MaxHitCount = %(hits)d,
        MaxRange = %(maxr).1f,
        MinAngle = -0.3,
        MinDamage = 8,
        MinRange = %(minr).2f,
        MinimumSwingTime = %(swing).1f,
        PushBackMod = 0.5,
        RunAnim = Run_Weapon2,
        SubCategory = Swinging,
        SwingAmountBeforeImpact = 0.02,
        SwingAnim = Bat,
        SwingSound = SableLuzSwing,
        SwingTime = %(swing).1f,
        Tags = base:ignorezombiedensity;base:hasmetal;base:fullblade,
        TreeDamage = %(tree)d,
        TwoHandWeapon = true,
        WeaponLength = %(len).1f,
        WeaponSprite = SL.%(model)s,
        Sharpness = 5.0,
    }
''' % dict(id=item_id, model=model_id, weight=weight, minr=min_range, maxr=max_range,
           len=weapon_length, swing=swing_time, hits=max_hit_count, tree=tree_damage, door=door_damage)


def crystal_item(item_id, tooltip_id):
    return '''
    /* El corazon del sable. Raro: joyerias, casas de empeno, antiguedades, laboratorios. */
    item %s
    {
        DisplayCategory = Material,
        ItemType = base:normal,
        Weight = 0.1,
        Icon = %s,
        Tooltip = %s,
    }
''' % (item_id, item_id, tooltip_id)


HILT_ITEMS = '''
    /* Empunadura sin cristal: se arma con chatarra electronica o se encuentra (replicas de
       coleccion en tiendas de comics, prototipos en laboratorios y el ejercito). */
    item EmpunaduraSable
    {
        DisplayCategory = Electronics,
        ItemType = base:normal,
        Weight = 0.8,
        Icon = EmpunaduraSable,
        Tooltip = Tooltip_SL_EmpunaduraSable,
    }

    /* Empunadura larga para el sable de doble hoja: dos emisores, uno en cada punta. */
    item EmpunaduraDobleSable
    {
        DisplayCategory = Electronics,
        ItemType = base:normal,
        Weight = 1.4,
        Icon = EmpunaduraDobleSable,
        Tooltip = Tooltip_SL_EmpunaduraDobleSable,
    }
'''


def build_items_and_models():
    items, models = [], []
    for c in COLORS:
        cid = sid('CristalKyber', c['suffix'])
        items.append(crystal_item(cid, 'Tooltip_SL_%s' % cid))

        # sable sencillo: malla compartida (SableLuz.x), una textura por color
        single_id = sid('SableLuz', c['suffix'])
        items.append(saber_item(single_id, single_id, weight=1.2, min_range=0.21, max_range=2.0,
                                 weapon_length=0.4, swing_time=2.2, max_hit_count=10,
                                 tree_damage=8, door_damage=12))
        models.append('''
    model %s
    {
        mesh = weapons/2handed/SableLuz,
        texture = weapons/2handed/%s,
    }
''' % (single_id, single_id))

        # sable de doble hoja: malla compartida (SableLuzDoble.x), mas pesado y de mas alcance,
        # golpea a mas enemigos por lo largo (hasta 14) pero es un poco mas lento de blandir.
        double_id = sid('SableLuzDoble', c['suffix'])
        items.append(saber_item(double_id, double_id, weight=2.1, min_range=0.21, max_range=2.4,
                                 weapon_length=0.55, swing_time=2.6, max_hit_count=14,
                                 tree_damage=10, door_damage=14))
        models.append('''
    model %s
    {
        mesh = weapons/2handed/SableLuzDoble,
        texture = weapons/2handed/%s,
    }
''' % (double_id, double_id))

    ITEMS = 'module SL\n{\n    imports\n    {\n        Base,\n    }\n' + HILT_ITEMS + ''.join(items) + '}\n'
    MODELS = 'module SL\n{\n    imports\n    {\n        Base,\n    }\n' + ''.join(models) + '}\n'
    return ITEMS, MODELS


# --------------------------------------------------------------------------- recetas
def _recipe(name, time, skill, xp, inputs, outputs):
    return '''
    craftRecipe %s
    {
        timedAction = MakingElectrical,
        time = %d,
        Tags = AnySurfaceCraft,
        category = Electrical,
        SkillRequired = Electricity:%d,
        xpAward = Electricity:%d,

        inputs
        {
%s
        }

        outputs
        {
%s
        }
    }
''' % (name, time, skill, xp, ''.join('            %s,\n' % i for i in inputs),
       ''.join('            %s,\n' % o for o in outputs))


def build_recipes():
    out = ['''
    /* 1) Empunadura: un tubo de metal como cuerpo, electronica y cable para el emisor. */''' +
           _recipe('SLArmarEmpunadura', 300, 2, 15,
                   ['item 1 tags[base:screwdriver] mode:keep', 'item 1 [Base.MetalPipe]',
                    'item 2 [Base.ElectronicsScrap]', 'item 1 [Base.ElectricWire]', 'item 1 [Base.DuctTape]'],
                   ['item 1 SL.EmpunaduraSable']),
           '''
    /* 1b) Empunadura doble: se sueldan dos empunaduras por el centro con un tubo mas y cinta. */''' +
           _recipe('SLArmarEmpunaduraDoble', 400, 3, 25,
                   ['item 1 tags[base:screwdriver] mode:keep', 'item 2 [SL.EmpunaduraSable] mode:destroy',
                    'item 1 [Base.MetalPipe]', 'item 2 [Base.DuctTape]'],
                   ['item 1 SL.EmpunaduraDobleSable'])]

    for c in COLORS:
        s = c['suffix']
        cid = sid('CristalKyber', s)
        single_id = sid('SableLuz', s)
        double_id = sid('SableLuzDoble', s)
        name = c['name_es']

        out.append('\n    /* Sable (%s): empunadura + cristal + dos baterias para encenderlo. */' % name)
        out.append(_recipe(sid('SLEnsamblarSable', s), 400, 3, 30,
                            ['item 1 tags[base:screwdriver] mode:keep', 'item 1 [SL.EmpunaduraSable]',
                             'item 1 [%s]' % cid, 'item 2 [Base.Battery] mode:destroy'],
                            ['item 1 %s' % single_id]))
        out.append('\n    /* Desarmar (%s): recuperar la empunadura y el cristal. */' % name)
        out.append(_recipe(sid('SLDesarmarSable', s), 200, 1, 5,
                            ['item 1 tags[base:screwdriver] mode:keep', 'item 1 [%s] mode:destroy' % single_id],
                            ['item 1 SL.EmpunaduraSable', 'item 1 %s' % cid]))

        out.append('\n    /* Sable de doble hoja (%s): empunadura doble + dos cristales + cuatro baterias. */' % name)
        out.append(_recipe(sid('SLEnsamblarSableDoble', s), 500, 4, 45,
                            ['item 1 tags[base:screwdriver] mode:keep', 'item 1 [SL.EmpunaduraDobleSable]',
                             'item 2 [%s]' % cid, 'item 4 [Base.Battery] mode:destroy'],
                            ['item 1 %s' % double_id]))
        out.append('\n    /* Desarmar la doble hoja (%s). */' % name)
        out.append(_recipe(sid('SLDesarmarSableDoble', s), 250, 2, 8,
                            ['item 1 tags[base:screwdriver] mode:keep', 'item 1 [%s] mode:destroy' % double_id],
                            ['item 1 SL.EmpunaduraDobleSable', 'item 2 %s' % cid]))

    return 'module SL\n{\n    imports\n    {\n        Base,\n    }\n' + ''.join(out) + '}\n'


def build_fixing():
    out = []
    for c in COLORS:
        s = c['suffix']
        for base, battery, scrap in ((sid('SableLuz', s), 1, 2), (sid('SableLuzDoble', s), 2, 3)):
            out.append('''
    /* Reparar %s: cambiar las baterias o reemplazar componentes quemados. */
    fixing Fix %s
    {
        Require : %s,

        Fixer : Battery=%d; Electricity=2,
        Fixer : ElectronicsScrap=%d; Electricity=3,
    }
''' % (base, base, base, battery, scrap))
    return 'module SL\n{\n    imports\n    {\n        Base,\n    }\n' + ''.join(out) + '}\n'


# --------------------------------------------------------------------------- loot
def build_loot():
    rows = []
    for c in COLORS:
        s = c['suffix']
        w = c['weight']
        cid = sid('CristalKyber', s)
        rows += [
            ('JewelryGems', cid, round(0.6 * w, 3)),
            ('PawnShopCases', cid, round(0.4 * w, 3)),
            ('Antiques', cid, round(0.3 * w, 3)),
            ('LaboratoryLockers', cid, round(0.5 * w, 3)),
            ('UniversityStorageScience', cid, round(0.3 * w, 3)),
        ]
        single_id = sid('SableLuz', s)
        rows += [
            ('LaboratoryLockers', single_id, round(0.05 * w, 4)),
            ('ArmyBunkerLockers', single_id, round(0.05 * w, 4)),
            ('ArmyStorageGuns', single_id, round(0.03 * w, 4)),
            ('PawnShopCases', single_id, round(0.03 * w, 4)),
        ]
        double_id = sid('SableLuzDoble', s)
        rows += [   # la de doble hoja es mas rara todavia: solo en los escondites mas dificiles
            ('LaboratoryLockers', double_id, round(0.02 * w, 4)),
            ('ArmyBunkerLockers', double_id, round(0.02 * w, 4)),
        ]
    rows += [   # empunaduras: no dependen del color
        ('ComicStoreCounter', 'SL.EmpunaduraSable', 0.4),
        ('ElectronicStoreMisc', 'SL.EmpunaduraSable', 0.2),
        ('CrateElectronics', 'SL.EmpunaduraSable', 0.2),
        ('ArmyStorageElectronics', 'SL.EmpunaduraSable', 0.3),
        ('LaboratoryLockers', 'SL.EmpunaduraSable', 0.4),
        ('LaboratoryLockers', 'SL.EmpunaduraDobleSable', 0.15),
        ('ArmyStorageElectronics', 'SL.EmpunaduraDobleSable', 0.1),
        ('ComicStoreCounter', 'SL.EmpunaduraDobleSable', 0.1),
    ]
    return rows


def loot_lua(rows):
    rows_txt = '\n'.join('    { "%s", "SL.%s", %s },' % (cont, item, w) for cont, item, w in rows)
    return '''-- Sable de Luz: loot. Generado por build_sableluz.py.
require "Items/ProceduralDistributions"

local LOOT = {
%s
}

local function addLoot()
    for _, row in ipairs(LOOT) do
        local list = ProceduralDistributions.list[row[1]]
        if list and list.items then
            table.insert(list.items, row[2])
            table.insert(list.items, row[3])
        else
            print("[SableLuz] contenedor de loot no encontrado: " .. tostring(row[1]))
        end
    end
end

Events.OnPreDistributionMerge.Add(addLoot)
''' % rows_txt


def encendido_lua():
    entries = []
    for c in COLORS:
        r, g, b = (v / 255 for v in c['rgb'])
        for base, rad in ((sid('SableLuz', c['suffix']), LIGHT_RADIUS),
                           (sid('SableLuzDoble', c['suffix']), LIGHT_RADIUS_DOBLE)):
            entries.append('    ["SL.%s"] = { r=%.2f, g=%.2f, b=%.2f, radius=%d },' % (base, r, g, b, rad))
    saber_table = '\n'.join(entries)
    return '''-- Sable de Luz encendido: mientras alguien lo tiene en la mano
--   * ilumina con el color de SU cristal alrededor (una luz de cell que lo sigue casilla a casilla)
--   * zumba (loop) y suena al encenderse / apagarse
-- Generado por build_sableluz.py.

-- fulltype -> color/alcance de la luz. Cubre todos los colores y los dos largos de sable.
local SABERS = {
%s
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
    if tick %% 5 ~= 0 then return end
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
''' % saber_table


# --------------------------------------------------------------------------- textos
def build_texts():
    en = dict(ItemName={}, Tooltip={}, Recipes={})
    es = dict(ItemName={}, Tooltip={}, Recipes={})

    en['ItemName']['SL.EmpunaduraSable'] = 'Lightsaber Hilt'
    es['ItemName']['SL.EmpunaduraSable'] = 'Empuñadura de Sable de Luz'
    en['Tooltip']['Tooltip_SL_EmpunaduraSable'] = 'An empty hilt. It needs a crystal and power to ignite.'
    es['Tooltip']['Tooltip_SL_EmpunaduraSable'] = 'Una empuñadura vacía. Le falta un cristal y energía para encenderse.'
    en['ItemName']['SL.EmpunaduraDobleSable'] = 'Double-Bladed Lightsaber Hilt'
    es['ItemName']['SL.EmpunaduraDobleSable'] = 'Empuñadura de Sable de Doble Hoja'
    en['Tooltip']['Tooltip_SL_EmpunaduraDobleSable'] = 'A long hilt with an emitter on each end. Needs two crystals and power.'
    es['Tooltip']['Tooltip_SL_EmpunaduraDobleSable'] = 'Una empuñadura larga con un emisor en cada punta. Necesita dos cristales y energía.'
    en['Recipes']['SLArmarEmpunadura'] = 'Build Lightsaber Hilt'
    es['Recipes']['SLArmarEmpunadura'] = 'Armar empuñadura de sable'
    en['Recipes']['SLArmarEmpunaduraDoble'] = 'Build Double-Bladed Lightsaber Hilt'
    es['Recipes']['SLArmarEmpunaduraDoble'] = 'Armar empuñadura de sable doble'

    for c in COLORS:
        s = c['suffix']
        cid = sid('CristalKyber', s)
        single_id = sid('SableLuz', s)
        double_id = sid('SableLuzDoble', s)
        en_name, es_name = c['name_en'], c['name_es']

        en['ItemName']['SL.%s' % cid] = 'Kyber Crystal (%s)' % en_name
        es['ItemName']['SL.%s' % cid] = 'Cristal Kyber (%s)' % es_name
        en['Tooltip']['Tooltip_SL_%s' % cid] = 'A warm, humming %s crystal. The heart of a lightsaber.' % en_name.lower()
        es['Tooltip']['Tooltip_SL_%s' % cid] = 'Un cristal %s, tibio, que zumba. El corazón de un sable de luz.' % es_name.lower()

        en['ItemName']['SL.%s' % single_id] = 'Lightsaber (%s)' % en_name
        es['ItemName']['SL.%s' % single_id] = 'Sable de Luz (%s)' % es_name
        en['Tooltip']['Tooltip_SL_%s' % single_id] = 'Glows %s when held. Repair it with batteries or scrap electronics.' % en_name.lower()
        es['Tooltip']['Tooltip_SL_%s' % single_id] = 'Brilla %s al empuñarlo. Se repara con baterías o chatarra electrónica.' % es_name.lower()

        en['ItemName']['SL.%s' % double_id] = 'Double-Bladed Lightsaber (%s)' % en_name
        es['ItemName']['SL.%s' % double_id] = 'Sable de Luz de Doble Hoja (%s)' % es_name
        en['Tooltip']['Tooltip_SL_%s' % double_id] = 'Two %s blades, one hilt. Heavier and slower, hits everything around you.' % en_name.lower()
        es['Tooltip']['Tooltip_SL_%s' % double_id] = 'Dos hojas %s, una empuñadura. Más pesado y lento, pega a todo tu alrededor.' % es_name.lower()

        en['Recipes'][sid('SLEnsamblarSable', s)] = 'Assemble Lightsaber (%s)' % en_name
        es['Recipes'][sid('SLEnsamblarSable', s)] = 'Ensamblar sable de luz (%s)' % es_name
        en['Recipes'][sid('SLDesarmarSable', s)] = 'Disassemble Lightsaber (%s)' % en_name
        es['Recipes'][sid('SLDesarmarSable', s)] = 'Desarmar sable de luz (%s)' % es_name
        en['Recipes'][sid('SLEnsamblarSableDoble', s)] = 'Assemble Double-Bladed Lightsaber (%s)' % en_name
        es['Recipes'][sid('SLEnsamblarSableDoble', s)] = 'Ensamblar sable de doble hoja (%s)' % es_name
        en['Recipes'][sid('SLDesarmarSableDoble', s)] = 'Disassemble Double-Bladed Lightsaber (%s)' % en_name
        es['Recipes'][sid('SLDesarmarSableDoble', s)] = 'Desarmar sable de doble hoja (%s)' % es_name

    return {'EN': en, 'ES': es}


MODINFO = """name=Sable de Luz
id=sableluz
modversion=%s
versionMin=42.15.0
description=Sable de luz que brilla y zumba de verdad, en 7 colores de cristal, con version de doble hoja, recetas, reparacion y loot. Build 42.
poster=poster.png
icon=icon.png
""" % VERSION


def main():
    tex_dir = os.path.join(MEDIA, 'textures')
    wtex = os.path.join(tex_dir, 'weapons', '2handed')
    os.makedirs(wtex, exist_ok=True)

    # mallas: una para el sable sencillo y otra para el de doble hoja; el color va solo en
    # la textura (el modelo de cada item indica que textura usar sobre la misma malla).
    mesh_dir = os.path.join(MEDIA, 'models_X', 'weapons', '2handed')
    os.makedirs(mesh_dir, exist_ok=True)
    v, f, n, uv = saber.build_mesh()
    xfile.write_x(os.path.join(mesh_dir, 'SableLuz.x'), 'SableLuz', 'SableMtl', 'SableLuz.png',
                  v, f, n, uv, emissive=(0.3, 0.3, 0.3))
    vd, fd, nd, uvd = saber.build_mesh_double()
    xfile.write_x(os.path.join(mesh_dir, 'SableLuzDoble.x'), 'SableLuzDoble', 'SableMtl', 'SableLuzDoble.png',
                  vd, fd, nd, uvd, emissive=(0.3, 0.3, 0.3))
    print('  malla sencilla: %d vertices, %d caras' % (len(v), len(f)))
    print('  malla doble: %d vertices, %d caras' % (len(vd), len(fd)))

    icons.hilt_icon().save(os.path.join(tex_dir, 'item_EmpunaduraSable.png'))
    icons.double_hilt_icon().save(os.path.join(tex_dir, 'item_EmpunaduraDobleSable.png'))

    for c in COLORS:
        s, rgb = c['suffix'], c['rgb']
        single_id, double_id, cid = sid('SableLuz', s), sid('SableLuzDoble', s), sid('CristalKyber', s)

        saber.make_texture(os.path.join(wtex, '%s.png' % single_id), rgb)
        saber.make_texture_double(os.path.join(wtex, '%s.png' % double_id), rgb)

        icons.saber_icon(rgb).save(os.path.join(tex_dir, 'item_%s.png' % single_id))
        icons.double_saber_icon(rgb).save(os.path.join(tex_dir, 'item_%s.png' % double_id))
        icons.crystal_icon(rgb).save(os.path.join(tex_dir, 'item_%s.png' % cid))

        if not s:   # el rojo clasico es el que aparece en el icono/poster del mod
            icons.saber_icon(rgb).save(os.path.join(OUT, 'icon.png'))
            saber.make_poster(os.path.join(OUT, 'poster.png'), rgb, size=512)
            saber.make_poster(os.path.join(HERE, 'preview.png'), rgb, size=512)

    # scripts
    package_sound()
    gen = os.path.join(MEDIA, 'scripts', 'generated')
    write(os.path.join(gen, 'sableluz_Sounds.txt'), SOUNDS)
    ITEMS, MODELS = build_items_and_models()
    write(os.path.join(gen, 'sableluz_Items.txt'), ITEMS)
    write(os.path.join(gen, 'sableluz_Models.txt'), MODELS)
    write(os.path.join(gen, 'sableluz_Recipes.txt'), build_recipes())
    write(os.path.join(gen, 'sableluz_Fixing.txt'), build_fixing())

    # lua
    write(os.path.join(MEDIA, 'lua', 'client', 'SableLuz_Encendido.lua'), encendido_lua())
    write(os.path.join(MEDIA, 'lua', 'server', 'Items', 'SableLuz_Distributions.lua'), loot_lua(build_loot()))

    # traducciones
    for lang, files in build_texts().items():
        for fname, data in files.items():
            write(os.path.join(MEDIA, 'lua', 'shared', 'Translate', lang, fname + '.json'),
                  json.dumps(data, ensure_ascii=False, indent=4) + '\n')

    write(os.path.join(OUT, 'mod.info'), MODINFO)
    print('\nBuild OK -> %s  (%d colores x 2 largos = %d sables, %d cristales)'
          % (OUT, len(COLORS), len(COLORS) * 2, len(COLORS)))


if __name__ == '__main__':
    main()
