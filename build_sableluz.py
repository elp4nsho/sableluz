#!/usr/bin/env python3
"""Build script del mod 'sableluz' (Build 42).
Genera TODO dentro de la carpeta actual -> ./42
NO toca otros mods ni hace deploys externos.
Fuente de referencia (solo lectura): katana vanilla + arte saber1.png.
"""
import os
import json
import shutil
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Contents", "mods", "sableluz", "42")

VANILLA = "/Users/fcisternas/Library/Application Support/Steam/steamapps/common/ProjectZomboid/Project Zomboid.app/Contents/Java/media"
KATANA = os.path.join(VANILLA, "textures/weapons/2handed/Katana.png")
SABER1 = os.path.join(HERE, "saber1.png")

SIZE = 128
ICON_SIZE = 32

# Paleta sable de luz ROJO
BLADE_CORE = (255, 42, 30)     # núcleo rojo brillante
BLADE_RIM  = (200, 16, 12)     # borde rojo profundo (glow)
HILT       = (66, 66, 72)      # mango metálico oscuro genérico
GUARD      = (122, 122, 128)   # guarda / transición


def make_weapon_texture(katana_png, saber1_png, out_png):
    """Textura 128x128 del sable de luz.

    Los UV de la malla SableLuz.x son cilíndricos:
      - u = ángulo alrededor del eje (0..1, recorre el mango+hoja)
      - v = 1 en el mango (abajo) -> 0 en la punta de la hoja (arriba)

    De modo que en la textura:
      - arriba  = punta de la hoja (blanco caliente + halo rojizo)
      - centro  = cuerpo de la hoja (blanco frío)
      - abajo   = mango (metal oscuro genérico con finos detalles)
    """
    tex = Image.open(saber1_png).convert("RGBA")
    core = (255, 42, 30)        # núcleo rojo vivo
    edge = (200, 16, 12)        # borde rojo profundo
    warm = (255, 90, 40)        # cálido hacia el emisor (naranja-rojo)
    core_tip = (255, 70, 50)    # punta ligeramente más clara
    hilt = (70, 72, 78)
    hilt_hi = (98, 100, 108)

    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    p = out.load()
    for y in range(SIZE):
        v = 1.0 - y / (SIZE - 1)   # v: 1 abajo -> 0 arriba
        for x in range(SIZE):
            u = x / (SIZE - 1)     # ángulo alrededor (continuo)
            # margen: fuera del cilindro (transparente)
            # ---- mango: v en [0, 0.15] (abajo de la textura) ----
            if v < 0.12:
                col = hilt
                if u < 0.06 or u > 0.94:
                    col = hilt_hi
                # anillos de la empuñadura
                band = int(v * 100) % 14
                if band < 2:
                    col = hilt_hi
                p[x, y] = (col[0], col[1], col[2], 255)
            # ---- emisor (transición mango->hoja) ----
            elif v < 0.16:
                col = hilt_hi
                p[x, y] = (col[0], col[1], col[2], 255)
            # ---- hoja: rojo brillante con halo más profundo ----
            else:
                # y=0 es la punta (rojo más vivo), el emisor más profundo
                side = min(u, 1.0 - u)
                if side < 0.10:
                    col = edge
                else:
                    col = core
                if y < SIZE * 0.10:          # punta: rojo más claro/vivo
                    col = (255, 95, 55)
                elif y > SIZE * 0.80:        # junto al emisor: rojo profundo
                    col = (235, 30, 22)
                p[x, y] = (col[0], col[1], col[2], 255)
    out.save(out_png)
    return out


def make_icon(out_png):
    """Icono 32x32 estilizado de sable vertical."""
    im = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    p = im.load()
    cx = ICON_SIZE // 2
    blade_bottom = 15
    for y in range(ICON_SIZE):
        for x in range(ICON_SIZE):
            if y <= blade_bottom:  # hoja
                half = max(2 - (y // 6), 1)
                if abs(x - cx) <= half:
                    c = BLADE_CORE
                elif abs(x - cx) <= half + 1:
                    c = BLADE_RIM
                else:
                    continue
                p[x, y] = (c[0], c[1], c[2], 255)
            else:  # mango
                half = 3
                if abs(x - cx) <= half:
                    c = GUARD if y in (blade_bottom + 1, blade_bottom + 2) else HILT
                    p[x, y] = (c[0], c[1], c[2], 255)
    im.save(out_png)


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  write", os.path.relpath(path, HERE))


def package_sound():
    """Empaqueta sable_sonido.mp3 -> media/sound/SableLuzHit.wav.

    El juego (GameSounds.loadNonBankSounds) solo encuentra .ogg/.wav, y WAV PCM
    es el formato más seguro para FMOD. Se convierte con afconvert (macOS nativo).
    Si falla, cae a ffmpeg/.ogg y luego a copiar el mp3 crudo.
    Devuelve el archivo (relativo a media/) que referencian los clips, o None.
    """
    src = os.path.join(HERE, "sable_sonido.mp3")
    if not os.path.exists(src):
        print("  aviso: falta sable_sonido.mp3, dejo sonidos vanilla Katana*")
        return None

    snd_dir = os.path.join(OUT, "media/sound")
    os.makedirs(snd_dir, exist_ok=True)

    wav = os.path.join(snd_dir, "SableLuzHit.wav")
    try:
        import subprocess
        subprocess.run(
            ["afconvert", "-f", "WAVE", "-d", "LEI16@44100", "-c", "1", src, wav],
            check=True, capture_output=True,
        )
        print("  audio convertido a SableLuzHit.wav")
        return "media/sound/SableLuzHit.wav"
    except Exception as e:
        print("  afconvert fallo (%s), pruebo ffmpeg a ogg" % e)

    ogg = os.path.join(snd_dir, "SableLuzHit.ogg")
    try:
        import subprocess
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-i", src, "-codec:a", "libopus", "-b:a", "128k", ogg],
            check=True, capture_output=True,
        )
        print("  audio convertido a SableLuzHit.ogg")
        return "media/sound/SableLuzHit.ogg"
    except Exception as e:
        print("  ffmpeg fallo (%s), copio mp3 crudo" % e)

    mp3 = os.path.join(snd_dir, "SableLuzHit.mp3")
    shutil.copy2(src, mp3)
    return "media/sound/SableLuzHit.mp3"


# ============================================================================
#  Malla 3D del sable de luz (formato DirectX .x texto, como Katana.x).
#  Orientación: eje Y hacia arriba. Mango en Y bajo, hoja luminosa en Y alto.
# ============================================================================

X_HEADER = """xof 0303txt 0032
template ColorRGBA {
 <35ff44e0-6c7c-11cf-8f52-0040333594a3>
 FLOAT red;
 FLOAT green;
 FLOAT blue;
 FLOAT alpha;
}

template ColorRGB {
 <d3e16e81-7835-11cf-8f52-0040333594a3>
 FLOAT red;
 FLOAT green;
 FLOAT blue;
}

template Material {
 <3d82ab4d-62da-11cf-ab39-0020af71e433>
 ColorRGBA faceColor;
 FLOAT power;
 ColorRGB specularColor;
 ColorRGB emissiveColor;
 [TextureFilename <a42790e1-7810-11cf-8f52-0040333594a3>]
}

template TextureFilename {
 <a42790e1-7810-11cf-8f52-0040333594a3>
 STRING filename;
}

template Frame {
 <3d82ab46-62da-11cf-ab39-0020af71e433>
 Matrix4x4 frameTransformMatrix;
 [Mesh <3d82ab44-62da-11cf-ab39-0020af71e433>]
}

template Matrix4x4 {
 <f6f23f45-7686-11cf-8f52-0040333594a3>
 array FLOAT matrix[16];
}

template FrameTransformMatrix {
 <f6f23f41-7686-11cf-8f52-0040333594a3>
 Matrix4x4 frameMatrix;
}

template Vector {
 <3d82ab5e-62da-11cf-ab39-0020af71e433>
 FLOAT x;
 FLOAT y;
 FLOAT z;
}

template MeshFace {
 <3d82ab5f-62da-11cf-ab39-0020af71e433>
 DWORD nFaceVertexIndices;
 array DWORD faceVertexIndices[nFaceVertexIndices];
}

template Mesh {
 <3d82ab44-62da-11cf-ab39-0020af71e433>
 DWORD nVertices;
 array Vector vertices[nVertices];
 DWORD nFaces;
 array MeshFace faces[nFaces];
 [MeshNormals <f6f23f43-7686-11cf-8f52-0040333594a3>]
 MeshTextureCoords <f6f23f40-7686-11cf-8f52-0040333594a3>;
}

template MeshNormals {
 <f6f23f43-7686-11cf-8f52-0040333594a3>
 DWORD nNormals;
 array Vector normals[nNormals];
 DWORD nFaceNormals;
 array MeshFace faceNormals[nFaceNormals];
}

template MeshMaterialList {
 <f6f23f42-7686-11cf-8f52-0040333594a3>
 DWORD nMaterials;
 DWORD nFaceIndexes;
 array DWORD faceIndexes[nFaceIndexes];
 [Material <3d82ab4d-62da-11cf-ab39-0020af71e433>]
}

template Coords2d {
 <f6f23f44-7686-11cf-8f52-0040333594a3>
 FLOAT u;
 FLOAT v;
}

template MeshTextureCoords {
 <f6f23f40-7686-11cf-8f52-0040333594a3>
 DWORD nTextureCoords;
 array Coords2d textureCoords[nTextureCoords];
}

"""


def build_saber_mesh_segments(n_around=16):
    """Genera la geometría del sable: mango cilíndrico + hoja cilíndrica.

    Retorna (verts, faces, normals, uvs). Anillos a lo largo del eje Y:
      Y bajo  = pomo/mango,  Y alto = punta de la hoja.
    """
    import math
    t = 2 * math.pi / n_around

    # perfil: (yorigenY, radio) recorrido de abajo hacia arriba
    profile = [
        (0.00, 0.013),   # pomo
        (0.02, 0.015),   # base mango
        (0.10, 0.015),   # mango
        (0.12, 0.017),   # emisor
        (0.135, 0.010),  # hombro -> hoja (adelgaza)
        (0.16, 0.009),   # hoja
        (0.60, 0.0085),  # punta de la hoja
    ]
    y_min = profile[0][0]
    y_max = profile[-1][0]

    rings = []   # cada anillo: lista de (x,y,z,nx,ny,nz,u,v)
    for yi, r in profile:
        # v=1 en el mango (abajo de la textura) -> v=0 en la punta
        v = 1.0 - (yi - y_min) / (y_max - y_min)
        ring = []
        for a in range(n_around):
            ang = a * t
            x, z = math.cos(ang), math.sin(ang)
            u = a / n_around
            ring.append((r * x, yi, r * z, x, 0.0, z, u, v))
        rings.append(ring)
    rings.append(rings[-1])  # duplicado var. no usado

    verts = []
    uvs = []
    normals = []
    # bombeamos anillos en un solo array de vértices (normales = radiales)
    ring_offset = []
    for ring in rings[:len(profile)]:
        off = len(verts)
        ring_offset.append(off)
        for (x, y, z, nx, ny, nz, u, v) in ring:
            verts.append((x, y, z))
            normals.append((nx, ny, nz))
            uvs.append((u, v))

    def vidx(ring_i, a):
        return ring_offset[ring_i] + a

    faces = []
    for ri in range(len(profile) - 1):
        for a in range(n_around):
            a2 = (a + 1) % n_around
            i00 = vidx(ri, a);     i01 = vidx(ri, a2)
            i10 = vidx(ri + 1, a); i11 = vidx(ri + 1, a2)
            faces.append((i00, i10, i11))
            faces.append((i00, i11, i01))

    # tapas: centro inferior (mango) y centro superior (punta)
    ci = len(verts)
    verts.append((0.0, y_min, 0.0)); normals.append((0.0, -1.0, 0.0)); uvs.append((0.5, 1.0))
    for a in range(n_around):
        a2 = (a + 1) % n_around
        faces.append((ci, vidx(0, a2), vidx(0, a)))
    ct = len(verts)
    verts.append((0.0, y_max, 0.0)); normals.append((0.0, 1.0, 0.0)); uvs.append((0.5, 0.0))
    last = len(profile) - 1
    for a in range(n_around):
        a2 = (a + 1) % n_around
        faces.append((ct, vidx(last, a), vidx(last, a2)))

    return verts, faces, normals, uvs


def render_x_mesh(name, mat_name, texture_name, out_path):
    verts, faces, normals, uvs = build_saber_mesh_segments()

    def fmt3(vec):
        return "%.6f;%.6f;%.6f" % vec

    lines = [X_HEADER]
    lines.append("Material %s {" % mat_name)
    lines.append(" 1.000000;1.000000;1.000000;1.000000;;")
    lines.append(" 9.999999;")
    lines.append(" 0.000000;0.000000;0.000000;;")  # specular
    lines.append(" 0.350000;0.050000;0.020000;;")  # emissive rojo (brilla)
    lines.append(' TextureFilename { "%s"; }' % texture_name)
    lines.append("}")
    lines.append("")
    lines.append("Frame %s {" % name)
    lines.append(" FrameTransformMatrix {")
    lines.append("  1.000000,0.000000,0.000000,0.000000,0.000000,1.000000,0.000000,0.000000,0.000000,0.000000,1.000000,0.000000,0.000000,0.000000,0.000000,1.000000;;")
    lines.append(" }")
    lines.append("")
    lines.append(" Mesh %s {" % name)
    lines.append("  %d;" % len(verts))
    for i, v in enumerate(verts):
        sep = ";" if i == len(verts) - 1 else ","
        lines.append("  %s%s" % (fmt3(v), ";"))
        lines[-1] = "  %s;%s" % (fmt3(v), sep)
    lines.append("  %d;" % len(faces))
    for i, f in enumerate(faces):
        sep = ";" if i == len(faces) - 1 else ","
        lines.append("  3;%d,%d,%d%s" % (f[0], f[1], f[2], sep))
    lines.append("")
    lines.append("  MeshNormals {")
    lines.append("   %d;" % len(normals))
    for i, n in enumerate(normals):
        sep = ";" if i == len(normals) - 1 else ","
        lines.append("   %s;%s" % (fmt3(n), sep))
    lines.append("   %d;" % len(faces))
    for i, f in enumerate(faces):
        sep = ";" if i == len(faces) - 1 else ","
        lines.append("   3;%d,%d,%d%s" % (f[0], f[1], f[2], sep))
    lines.append("  }")
    lines.append("")
    lines.append("  MeshMaterialList {")
    lines.append("   1;")
    lines.append("   %d;" % len(faces))
    for i in range(len(faces)):
        sep = ";" if i == len(faces) - 1 else ","
        lines.append("   0%s" % sep)
    lines.append("   { %s }" % mat_name)
    lines.append("  }")
    lines.append("")
    lines.append("  MeshTextureCoords c1 {")
    lines.append("   %d;" % len(uvs))
    for i, (u, v) in enumerate(uvs):
        sep = ";" if i == len(uvs) - 1 else ","
        lines.append("   %.6f;%.6f%s" % (u, v, sep))
    lines.append("  }")
    lines.append(" }")
    lines.append("}")
    write_file(out_path, "\n".join(lines))


def main():
    if not os.path.exists(KATANA):
        print("ERROR: no encuentro Katana.png vanilla:", KATANA)
        raise SystemExit(1)
    if not os.path.exists(SABER1):
        print("ERROR: falta saber1.png en:", SABER1)
        raise SystemExit(1)

    tex_dir = os.path.join(OUT, "media/textures/weapons/2handed")
    os.makedirs(tex_dir, exist_ok=True)
    os.makedirs(os.path.join(OUT, "media/textures"), exist_ok=True)
    make_weapon_texture(KATANA, SABER1, os.path.join(tex_dir, "SableLuz.png"))
    make_icon(os.path.join(OUT, "media/textures/item_SableLuz.png"))
    print("  textura y icono generados")

    # ---- malla 3D propia (sable de luz) ----
    mesh_dir = os.path.join(OUT, "media/models_X/weapons/2handed")
    os.makedirs(mesh_dir, exist_ok=True)
    render_x_mesh("SableLuz", "SableMtl", "SableLuz.png",
                  os.path.join(mesh_dir, "SableLuz.x"))
    print("  malla 3D SableLuz.x generada")

    # ---- sonido custom del sable (sable_sonido.mp3 -> ogg) ----
    snd_file = package_sound()
    if snd_file:
        sounds = """module Base
{
    sound SableLuzHit
    {
        category = Item,
        clip
        {
            file = %s,
            distanceMax = 15,
            volume = 1.0,
        }
    }
    sound SableLuzSwing
    {
        category = Item,
        clip
        {
            file = %s,
            distanceMax = 25,
            volume = 1.0,
        }
    }
    sound SableLuzBreak
    {
        category = Item,
        clip
        {
            file = %s,
            distanceMax = 15,
            volume = 1.0,
        }
    }
    sound SableLuzDrop
    {
        category = Item,
        clip
        {
            file = %s,
            distanceMax = 15,
            volume = 1.0,
        }
    }
}
""" % (snd_file, snd_file, snd_file, snd_file)
        write_file(os.path.join(OUT, "media/scripts/generated/sableluz_Sounds.txt"), sounds)
        s_hit, s_swing, s_break, s_drop = "SableLuzHit", "SableLuzSwing", "SableLuzBreak", "SableLuzDrop"
    else:
        s_hit = s_swing = s_break = s_drop = None  # fallback a Katana*

    # ---- items ----
    item_snd = dict(
        BreakSound=s_break or "KatanaBreak",
        DoorHitSound=s_hit or "KatanaHit",
        DropSound=s_drop or "KatanaDrop",
        HitFloorSound=s_hit or "KatanaHit",
        HitSound=s_hit or "KatanaHit",
        ImpactSound=s_hit or "KatanaHit",
        SwingSound=s_swing or "KatanaSwing",
    )
    items = """module SL
{
    imports
    {
        Base,
    }
    item SableLuz
    {
        DisplayCategory = Weapon,
        ItemType = base:weapon,
        Weight = 1.5,
        Icon = SableLuz,
        AttachmentType = Sword,
        BaseSpeed = 1.0,
        BreakSound = %(BreakSound)s,
        Categories = LongBlade,
        ConditionLowerChanceOneIn = 1,
        ConditionMax = 20,
        CritDmgMultiplier = 9,
        CriticalChance = 35.0,
        DamageCategory = Slash,
        DamageMakeHole = true,
        DoorDamage = 8,
        DoorHitSound = %(DoorHitSound)s,
        DropSound = %(DropSound)s,
        HitAngleMod = -30.0,
        HitFloorSound = %(HitFloorSound)s,
        HitSound = %(HitSound)s,
        ImpactSound = %(ImpactSound)s,
        KnockBackOnNoDeath = true,
        KnockdownMod = 0.0,
        MaxDamage = 14,
        MaxHitCount = 10,
        MaxRange = 2.0,
        MinAngle = -0.3,
        MinDamage = 8,
        MinRange = 0.21,
        MinimumSwingTime = 3.0,
        PushBackMod = 0.5,
        RunAnim = Run_Weapon2,
        SubCategory = Swinging,
        SwingAmountBeforeImpact = 0.02,
        SwingAnim = Bat,
        SwingSound = %(SwingSound)s,
        SwingTime = 3.0,
        Tags = base:ignorezombiedensity;base:hasmetal;base:fullblade,
        TreeDamage = 1,
        TwoHandWeapon = true,
        WeaponLength = 0.4,
        WeaponSprite = SL.SableLuz,
        Sharpness = 5.0,
        OnBreak = OnBreak.Katana,
    }
}
""" % item_snd
    write_file(os.path.join(OUT, "media/scripts/generated/sableluz_Items.txt"), items)

    # ---- modelos ----
    models = """module SL
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
    write_file(os.path.join(OUT, "media/scripts/generated/sableluz_Models.txt"), models)

    # ---- traducciones ----
    for lang, name in (("EN", "Lightsaber"), ("ES", "Sable de Luz")):
        tr = {"SL.SableLuz": name}
        write_file(
            os.path.join(OUT, "media/lua/shared/Translate/%s/ItemName.json" % lang),
            json.dumps(tr, ensure_ascii=False, indent=4),
        )

    # ---- mod.info ----
    modinfo = """name=Sable de Luz
id=sableluz
modversion=1.0.0
description=Sable de luz fuerte. Build 42.
poster=poster.png
icon=icon.png
"""
    write_file(os.path.join(OUT, "mod.info"), modinfo)

    # ---- poster/icon del mod.info ----
    make_icon(os.path.join(OUT, "icon.png"))
    poster = make_weapon_texture(KATANA, SABER1, os.path.join(OUT, "poster.png"))
    # poster agrandado sobre fondo oscuro
    big = Image.new("RGBA", (SIZE, SIZE), (18, 18, 22, 255))
    big.paste(poster, (0, 0), poster)
    big.save(os.path.join(OUT, "poster.png"))

    print()
    print("Build OK ->", OUT)


if __name__ == "__main__":
    main()