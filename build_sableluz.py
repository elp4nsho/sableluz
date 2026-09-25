#!/usr/bin/env python3
"""Build del mod 'sableluz' (Project Zomboid Build 42).

Genera todo dentro de Contents/mods/sableluz/42:
  - malla 3D del sable (.x) y su textura
  - iconos (sable, cristal kyber, empunadura), poster e icono del mod
  - scripts: items, modelo, sonidos, recetas (craftRecipe) y reparacion (fixing)
  - Lua: luz de color del sable encendido y loot
  - traducciones EN/ES (JSON de B42)

Uso:  python3 build_sableluz.py        (requiere Pillow y numpy)
El sonido se toma de media/sound/SableLuzHit.wav si ya existe; si no, se intenta convertir
sable_sonido.mp3 con ffmpeg (o afconvert en macOS).
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'tools'))

import icons      # noqa: E402
import saber      # noqa: E402
import xfile      # noqa: E402

OUT = os.path.join(HERE, 'Contents', 'mods', 'sableluz', '42')
MEDIA = os.path.join(OUT, 'media')
VERSION = '1.1.0'

# Color del cristal (y de la hoja). Mas adelante: mas colores = mas cristales.
RED = (255, 30, 24)
LIGHT_RGB = (1.0, 0.16, 0.10)   # luz que proyecta el sable encendido
LIGHT_RADIUS = 4


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print('  write', os.path.relpath(path, HERE))


# --------------------------------------------------------------------------- sonido
def package_sound():
    snd_dir = os.path.join(MEDIA, 'sound')
    wav = os.path.join(snd_dir, 'SableLuzHit.wav')
    if os.path.exists(wav):
        return 'media/sound/SableLuzHit.wav'
    src = os.path.join(HERE, 'sable_sonido.mp3')
    if not os.path.exists(src):
        return None
    os.makedirs(snd_dir, exist_ok=True)
    for cmd in (['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-ac', '1', '-ar', '44100', wav],
                ['afconvert', '-f', 'WAVE', '-d', 'LEI16@44100', '-c', '1', src, wav]):
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return 'media/sound/SableLuzHit.wav'
        except Exception:
            continue
    return None


SOUNDS = """module Base
{
    sound SableLuzHit
    {
        category = Item,
        clip { file = %(f)s, distanceMax = 15, volume = 1.0, }
    }
    sound SableLuzSwing
    {
        category = Item,
        clip { file = %(f)s, distanceMax = 20, volume = 0.8, }
    }
    sound SableLuzBreak
    {
        category = Item,
        clip { file = %(f)s, distanceMax = 15, volume = 1.0, }
    }
    sound SableLuzDrop
    {
        category = Item,
        clip { file = %(f)s, distanceMax = 10, volume = 0.6, }
    }
}
"""

# --------------------------------------------------------------------------- items
ITEMS = """module SL
{
    imports
    {
        Base,
    }

    /* El sable. Mismo golpe 'fuerte' de la v1.0, pero ya no se rompe a los ~20 golpes
       (antes perdia durabilidad en CADA golpe) y el swing es menos lento. */
    item SableLuz
    {
        DisplayCategory = Weapon,
        ItemType = base:weapon,
        Weight = 1.2,
        Icon = SableLuz,
        Tooltip = Tooltip_SL_SableLuz,
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
        DoorDamage = 12,
        DoorHitSound = SableLuzHit,
        DropSound = SableLuzDrop,
        HitAngleMod = -30.0,
        HitFloorSound = SableLuzHit,
        HitSound = SableLuzHit,
        ImpactSound = SableLuzHit,
        KnockBackOnNoDeath = true,
        KnockdownMod = 0.0,
        MaxDamage = 14,
        MaxHitCount = 10,
        MaxRange = 2.0,
        MinAngle = -0.3,
        MinDamage = 8,
        MinRange = 0.21,
        MinimumSwingTime = 2.2,
        PushBackMod = 0.5,
        RunAnim = Run_Weapon2,
        SubCategory = Swinging,
        SwingAmountBeforeImpact = 0.02,
        SwingAnim = Bat,
        SwingSound = SableLuzSwing,
        SwingTime = 2.2,
        Tags = base:ignorezombiedensity;base:hasmetal;base:fullblade,
        TreeDamage = 8,
        TwoHandWeapon = true,
        WeaponLength = 0.4,
        WeaponSprite = SL.SableLuz,
        Sharpness = 5.0,
    }

    /* El corazon del sable. Raro: joyerias, casas de empeno, antiguedades, laboratorios. */
    item CristalKyber
    {
        DisplayCategory = Material,
        ItemType = base:normal,
        Weight = 0.1,
        Icon = CristalKyber,
        Tooltip = Tooltip_SL_CristalKyber,
    }

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
}
"""

MODELS = """module SL
{
    imports
    {
        Base,
    }
    model SableLuz
    {
        mesh = weapons/2handed/SableLuz,
        texture = weapons/2handed/SableLuz,
    }
}
"""

# --------------------------------------------------------------------------- recetas
RECIPES = """module SL
{
    imports
    {
        Base,
    }

    /* 1) Empunadura: un tubo de metal como cuerpo, electronica y cable para el emisor. */
    craftRecipe SLArmarEmpunadura
    {
        timedAction = MakingElectrical,
        time = 300,
        Tags = AnySurfaceCraft,
        category = Electrical,
        SkillRequired = Electricity:2,
        xpAward = Electricity:15,

        inputs
        {
            item 1 tags[base:screwdriver] mode:keep,
            item 1 [Base.MetalPipe],
            item 2 [Base.ElectronicsScrap],
            item 1 [Base.ElectricWire],
            item 1 [Base.DuctTape],
        }

        outputs
        {
            item 1 SL.EmpunaduraSable,
        }
    }

    /* 2) Sable: empunadura + cristal + dos baterias para encenderlo. */
    craftRecipe SLEnsamblarSable
    {
        timedAction = MakingElectrical,
        time = 400,
        Tags = AnySurfaceCraft,
        category = Electrical,
        SkillRequired = Electricity:3,
        xpAward = Electricity:30,

        inputs
        {
            item 1 tags[base:screwdriver] mode:keep,
            item 1 [SL.EmpunaduraSable],
            item 1 [SL.CristalKyber],
            item 2 [Base.Battery] mode:destroy,
        }

        outputs
        {
            item 1 SL.SableLuz,
        }
    }

    /* 3) Desarmar: recuperar la empunadura y el cristal (para cambiar de cristal/color). */
    craftRecipe SLDesarmarSable
    {
        timedAction = MakingElectrical,
        time = 200,
        Tags = AnySurfaceCraft,
        category = Electrical,
        SkillRequired = Electricity:1,
        xpAward = Electricity:5,

        inputs
        {
            item 1 tags[base:screwdriver] mode:keep,
            item 1 [SL.SableLuz] mode:destroy,
        }

        outputs
        {
            item 1 SL.EmpunaduraSable,
            item 1 SL.CristalKyber,
        }
    }
}
"""

FIXING = """module SL
{
    imports
    {
        Base,
    }

    /* Reparar: cambiar las baterias o reemplazar componentes quemados. */
    fixing Fix Sable de Luz
    {
        Require : SableLuz,

        Fixer : Battery; Electricity=2,
        Fixer : ElectronicsScrap=2; Electricity=3,
    }
}
"""

# --------------------------------------------------------------------------- loot
LOOT = [
    # cristal kyber: gemas y rarezas
    ('JewelryGems', 'SL.CristalKyber', 0.6),
    ('PawnShopCases', 'SL.CristalKyber', 0.4),
    ('Antiques', 'SL.CristalKyber', 0.3),
    ('LaboratoryLockers', 'SL.CristalKyber', 0.5),
    ('UniversityStorageScience', 'SL.CristalKyber', 0.3),
    # empunadura: replicas de coleccion y prototipos
    ('ComicStoreCounter', 'SL.EmpunaduraSable', 0.4),
    ('ElectronicStoreMisc', 'SL.EmpunaduraSable', 0.2),
    ('CrateElectronics', 'SL.EmpunaduraSable', 0.2),
    ('ArmyStorageElectronics', 'SL.EmpunaduraSable', 0.3),
    ('LaboratoryLockers', 'SL.EmpunaduraSable', 0.4),
    # el sable armado: muy raro
    ('LaboratoryLockers', 'SL.SableLuz', 0.05),
    ('ArmyBunkerLockers', 'SL.SableLuz', 0.05),
    ('ArmyStorageGuns', 'SL.SableLuz', 0.03),
    ('PawnShopCases', 'SL.SableLuz', 0.03),
]


def loot_lua():
    rows = '\n'.join('    { "%s", "%s", %s },' % r for r in LOOT)
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
''' % rows


LIGHT_LUA = '''-- Sable de Luz: el sable encendido en la mano ilumina con su color alrededor de quien lo lleva.
-- Se usa una luz de cell (addLamppost) que sigue al jugador casilla a casilla.
-- Generado por build_sableluz.py.

local SABER = "SL.SableLuz"
local R, G, B = %(r).2f, %(g).2f, %(b).2f
local RADIUS = %(rad)d

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
    if tick %% 5 ~= 0 then return end
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
''' % dict(r=LIGHT_RGB[0], g=LIGHT_RGB[1], b=LIGHT_RGB[2], rad=LIGHT_RADIUS)

# --------------------------------------------------------------------------- textos
TEXTS = {
    'EN': {
        'ItemName': {
            'SL.SableLuz': 'Lightsaber',
            'SL.CristalKyber': 'Kyber Crystal (Red)',
            'SL.EmpunaduraSable': 'Lightsaber Hilt',
        },
        'Tooltip': {
            'Tooltip_SL_SableLuz': 'Glows when held. Repair it with batteries or scrap electronics.',
            'Tooltip_SL_CristalKyber': 'A warm, humming red crystal. The heart of a lightsaber.',
            'Tooltip_SL_EmpunaduraSable': 'An empty hilt. It needs a crystal and power to ignite.',
        },
        'Recipes': {
            'SLArmarEmpunadura': 'Build Lightsaber Hilt',
            'SLEnsamblarSable': 'Assemble Lightsaber',
            'SLDesarmarSable': 'Disassemble Lightsaber',
        },
    },
    'ES': {
        'ItemName': {
            'SL.SableLuz': 'Sable de Luz',
            'SL.CristalKyber': 'Cristal Kyber (rojo)',
            'SL.EmpunaduraSable': 'Empuñadura de Sable de Luz',
        },
        'Tooltip': {
            'Tooltip_SL_SableLuz': 'Brilla al empuñarlo. Se repara con baterías o chatarra electrónica.',
            'Tooltip_SL_CristalKyber': 'Un cristal rojo, tibio, que zumba. El corazón de un sable de luz.',
            'Tooltip_SL_EmpunaduraSable': 'Una empuñadura vacía. Le falta un cristal y energía para encenderse.',
        },
        'Recipes': {
            'SLArmarEmpunadura': 'Armar empuñadura de sable',
            'SLEnsamblarSable': 'Ensamblar sable de luz',
            'SLDesarmarSable': 'Desarmar sable de luz',
        },
    },
}

MODINFO = """name=Sable de Luz
id=sableluz
modversion=%s
versionMin=42.15.0
description=Sable de luz que brilla de verdad, con cristal kyber, empunadura, recetas, reparacion y loot. Build 42.
poster=poster.png
icon=icon.png
""" % VERSION


def main():
    tex_dir = os.path.join(MEDIA, 'textures')
    wtex = os.path.join(tex_dir, 'weapons', '2handed')
    os.makedirs(wtex, exist_ok=True)

    # malla y textura del sable
    verts, faces, normals, uvs = saber.build_mesh()
    mesh_dir = os.path.join(MEDIA, 'models_X', 'weapons', '2handed')
    os.makedirs(mesh_dir, exist_ok=True)
    xfile.write_x(os.path.join(mesh_dir, 'SableLuz.x'), 'SableLuz', 'SableMtl', 'SableLuz.png',
                  verts, faces, normals, uvs, emissive=(0.6, 0.1, 0.08))
    saber.make_texture(os.path.join(wtex, 'SableLuz.png'), RED)
    print('  malla: %d vertices, %d caras' % (len(verts), len(faces)))

    # iconos
    icons.saber_icon(RED).save(os.path.join(tex_dir, 'item_SableLuz.png'))
    icons.crystal_icon(RED).save(os.path.join(tex_dir, 'item_CristalKyber.png'))
    icons.hilt_icon().save(os.path.join(tex_dir, 'item_EmpunaduraSable.png'))
    icons.saber_icon(RED).save(os.path.join(OUT, 'icon.png'))
    saber.make_poster(os.path.join(OUT, 'poster.png'), RED, size=512)
    saber.make_poster(os.path.join(HERE, 'preview.png'), RED, size=512)

    # scripts
    snd = package_sound()
    gen = os.path.join(MEDIA, 'scripts', 'generated')
    if snd:
        write(os.path.join(gen, 'sableluz_Sounds.txt'), SOUNDS % {'f': snd})
    write(os.path.join(gen, 'sableluz_Items.txt'), ITEMS)
    write(os.path.join(gen, 'sableluz_Models.txt'), MODELS)
    write(os.path.join(gen, 'sableluz_Recipes.txt'), RECIPES)
    write(os.path.join(gen, 'sableluz_Fixing.txt'), FIXING)

    # lua
    write(os.path.join(MEDIA, 'lua', 'client', 'SableLuz_Light.lua'), LIGHT_LUA)
    write(os.path.join(MEDIA, 'lua', 'server', 'Items', 'SableLuz_Distributions.lua'), loot_lua())

    # traducciones
    for lang, files in TEXTS.items():
        for fname, data in files.items():
            write(os.path.join(MEDIA, 'lua', 'shared', 'Translate', lang, fname + '.json'),
                  json.dumps(data, ensure_ascii=False, indent=4) + '\n')

    write(os.path.join(OUT, 'mod.info'), MODINFO)
    print('\nBuild OK ->', OUT)


if __name__ == '__main__':
    main()
