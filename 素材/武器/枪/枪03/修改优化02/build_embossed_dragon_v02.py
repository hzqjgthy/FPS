#!/usr/bin/env python3

import base64
import copy
import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps
from pygltflib import GLTF2


ROOT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = ROOT_DIR.parent / "枪的模型"
OUTPUT_DIR = ROOT_DIR

BODY_TEXTURE_NAME = "T_XCR_Iron_Rouge_body_B.png"
BODY_TEXTURE_BACKUP_NAME = "T_XCR_Iron_Rouge_body_B.original.png"
HEIGHT_TEXTURE_NAME = "T_XCR_Iron_Rouge_body_height_dragonEmboss_v02.png"
NORMAL_TEXTURE_NAME = "T_XCR_Iron_Rouge_body_normal_dragonEmboss_v02.png"
ORM_TEXTURE_NAME = "T_XCR_Iron_Rouge_body_orm_dragonEmboss_v02.png"
COMPARE_IMAGE_NAME = "dragon_emboss_compare.png"

BASE_FILES = [
    "model.gltf",
    "buffer.bin",
    "glass.png",
    "EM_Orange.png",
    "T_XCR_Iron_Rouge_scope02_B.png",
    "T_XCR_Iron_Rouge_magazine_B.png",
    BODY_TEXTURE_NAME,
    "T_XCR_Iron_Rouge_scope01_B.png",
    "weapon03_meta.json",
    "viewer.html",
]

BASE_DIRS = ["viewer-assets"]

IMAGE_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def copy_base_assets():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for filename in BASE_FILES:
        shutil.copy2(SOURCE_DIR / filename, OUTPUT_DIR / filename)

    for dirname in BASE_DIRS:
        source_path = SOURCE_DIR / dirname
        target_path = OUTPUT_DIR / dirname
        if target_path.exists():
            shutil.rmtree(target_path)
        shutil.copytree(source_path, target_path)


def load_gltf():
    gltf_path = OUTPUT_DIR / "model.gltf"
    gltf = json.loads(gltf_path.read_text(encoding="utf-8"))
    for image in gltf.get("images", []):
        uri = image.get("uri")
        if not uri or uri.startswith("data:"):
            continue
        filename = Path(uri).name
        image["uri"] = filename
        image["name"] = filename
    return gltf


def save_gltf(gltf):
    gltf_path = OUTPUT_DIR / "model.gltf"
    gltf_path.write_text(json.dumps(gltf, ensure_ascii=False, indent=2), encoding="utf-8")


def backup_original_body():
    shutil.copy2(SOURCE_DIR / BODY_TEXTURE_NAME, OUTPUT_DIR / BODY_TEXTURE_BACKUP_NAME)


def build_red_mask(base_image):
    pixels = np.asarray(base_image.convert("RGBA"), dtype=np.uint8)
    red_mask = (
        (pixels[..., 0] > pixels[..., 1] * 1.08)
        & (pixels[..., 0] > pixels[..., 2] * 1.08)
        & (pixels[..., 0] > 72)
        & (pixels[..., 3] > 0)
    )
    mask = Image.fromarray((red_mask.astype(np.uint8) * 255), mode="L")
    return mask.filter(ImageFilter.GaussianBlur(2.0))


def polyline_points(points, segments_per_step=16):
    sampled = []
    for index in range(len(points) - 1):
        ax, ay = points[index]
        bx, by = points[index + 1]
        for step in range(segments_per_step):
            t = step / segments_per_step
            sampled.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    sampled.append(points[-1])
    return sampled


def point_and_angle(sampled_points, t):
    position = t * (len(sampled_points) - 1)
    index = min(int(position), len(sampled_points) - 2)
    local_t = position - index
    ax, ay = sampled_points[index]
    bx, by = sampled_points[index + 1]
    x = ax + (bx - ax) * local_t
    y = ay + (by - ay) * local_t
    angle = math.atan2(by - ay, bx - ax)
    return x, y, angle


def draw_relief_head(draw, anchor, angle, relief_fill, groove_fill):
    ax, ay = anchor
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    def transform(point):
        x, y = point
        return (
            ax + x * cos_a - y * sin_a,
            ay + x * sin_a + y * cos_a,
        )

    head_outline = [
        (-10, -8),
        (18, -22),
        (52, -24),
        (88, -10),
        (68, 4),
        (96, 22),
        (66, 20),
        (32, 12),
        (14, 26),
        (-14, 20),
    ]
    horn_upper = [(6, -8), (28, -42), (42, -38), (18, -14)]
    horn_lower = [(8, 8), (32, 34), (46, 30), (20, 12)]
    eye_slot = [(22, 0), (44, -4), (30, 10)]

    draw.polygon([transform(point) for point in head_outline], fill=relief_fill)
    draw.polygon([transform(point) for point in horn_upper], fill=relief_fill)
    draw.polygon([transform(point) for point in horn_lower], fill=relief_fill)
    draw.polygon([transform(point) for point in eye_slot], fill=groove_fill)
    draw.line([transform((8, 12)), transform((34, 6)), transform((58, 12))], fill=groove_fill, width=6)


def draw_scale_ridges(draw, sampled_points, fill, count=18, size=16):
    for t in np.linspace(0.08, 0.94, count):
        x, y, angle = point_and_angle(sampled_points, float(t))
        normal_angle = angle + math.pi * 0.5
        half_width = size * 0.56
        length = size * 1.05
        tip = (x + math.cos(normal_angle) * length, y + math.sin(normal_angle) * length)
        left = (x - math.cos(angle) * half_width, y - math.sin(angle) * half_width)
        right = (x + math.cos(angle) * half_width, y + math.sin(angle) * half_width)
        draw.polygon([left, tip, right], fill=fill)


def create_height_map(base_image):
    size = base_image.size
    red_mask = build_red_mask(base_image)
    mask_array = np.asarray(red_mask, dtype=np.float32) / 255.0

    relief_layer = Image.new("L", size, 0)
    groove_layer = Image.new("L", size, 0)
    scale_layer = Image.new("L", size, 0)
    relief_draw = ImageDraw.Draw(relief_layer)
    groove_draw = ImageDraw.Draw(groove_layer)
    scale_draw = ImageDraw.Draw(scale_layer)

    main_spine = [
        (210, 914),
        (470, 842),
        (770, 762),
        (1070, 664),
        (1370, 474),
        (1680, 296),
        (1892, 236),
    ]
    lower_band = [
        (190, 984),
        (388, 942),
        (620, 934),
        (880, 962),
        (1120, 1004),
    ]
    upper_band = [
        (1132, 392),
        (1328, 360),
        (1510, 332),
        (1712, 302),
    ]
    belly_cut = [
        (266, 826),
        (458, 776),
        (688, 738),
        (932, 720),
    ]

    relief_draw.line(main_spine, fill=230, width=44, joint="curve")
    relief_draw.line(lower_band, fill=196, width=38, joint="curve")
    relief_draw.line(upper_band, fill=188, width=30, joint="curve")
    relief_draw.line(belly_cut, fill=164, width=26, joint="curve")

    groove_draw.line(main_spine, fill=184, width=14, joint="curve")
    groove_draw.line(lower_band, fill=154, width=12, joint="curve")
    groove_draw.line(upper_band, fill=138, width=10, joint="curve")

    sampled_main = polyline_points(main_spine)
    sampled_lower = polyline_points(lower_band)
    sampled_upper = polyline_points(upper_band)
    draw_scale_ridges(scale_draw, sampled_main, 188, count=20, size=18)
    draw_scale_ridges(scale_draw, sampled_lower, 142, count=16, size=14)
    draw_scale_ridges(scale_draw, sampled_upper, 126, count=9, size=12)

    head_x, head_y, head_angle = point_and_angle(sampled_main, 0.95)
    draw_relief_head(relief_draw, (head_x, head_y), head_angle, 232, 170)
    draw_relief_head(groove_draw, (head_x, head_y), head_angle, 0, 152)

    rune_positions = [(1210, 600), (1380, 548), (1520, 516), (1648, 478)]
    for px, py in rune_positions:
        relief_draw.line([(px - 18, py + 12), (px + 12, py - 12), (px + 26, py + 8)], fill=152, width=10)
        groove_draw.line([(px - 10, py + 8), (px + 10, py - 8), (px + 16, py + 6)], fill=120, width=4)

    relief_layer = relief_layer.filter(ImageFilter.GaussianBlur(6))
    groove_layer = groove_layer.filter(ImageFilter.GaussianBlur(2.6))
    scale_layer = scale_layer.filter(ImageFilter.GaussianBlur(2.0))

    relief = np.asarray(relief_layer, dtype=np.float32) / 255.0
    grooves = np.asarray(groove_layer, dtype=np.float32) / 255.0
    scales = np.asarray(scale_layer, dtype=np.float32) / 255.0

    height = np.full((size[1], size[0]), 0.5, dtype=np.float32)
    height += relief * 0.34
    height += scales * 0.12
    height -= grooves * 0.26
    height = 0.5 * (1.0 - mask_array) + height * mask_array
    height = np.clip(height, 0.0, 1.0)
    return height, mask_array


def create_modified_base_color(base_image, height_map, red_mask):
    rgba = np.asarray(base_image.convert("RGBA"), dtype=np.float32) / 255.0
    rgb = rgba[..., :3]
    alpha = rgba[..., 3:]

    pattern = np.clip(np.abs(height_map - 0.5) * 3.0, 0.0, 1.0) * red_mask
    dx = np.gradient(height_map, axis=1)
    dy = np.gradient(height_map, axis=0)

    nx = -dx * 18.0
    ny = -dy * 18.0
    nz = np.ones_like(height_map)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx /= norm
    ny /= norm
    nz /= norm

    light = np.array([-0.58, -0.44, 0.68], dtype=np.float32)
    light /= np.linalg.norm(light)
    shade = np.clip(nx * light[0] + ny * light[1] + nz * light[2], 0.0, 1.0)

    ridge = np.clip((height_map - 0.5) * 3.2, 0.0, 1.0) * pattern
    cavity = np.clip((0.5 - height_map) * 3.6, 0.0, 1.0) * pattern
    glow = np.clip(shade * pattern, 0.0, 1.0)

    rgb[..., 0] += ridge * 0.18 + glow * 0.08
    rgb[..., 1] += ridge * 0.12 + glow * 0.06
    rgb[..., 2] += ridge * 0.04

    rgb[..., 0] -= cavity * 0.22
    rgb[..., 1] -= cavity * 0.15
    rgb[..., 2] -= cavity * 0.09

    gold = np.clip(ridge * 0.42 + glow * 0.24, 0.0, 1.0)
    rgb[..., 0] = np.clip(rgb[..., 0] * (1.0 - gold * 0.12) + gold * 0.95, 0.0, 1.0)
    rgb[..., 1] = np.clip(rgb[..., 1] * (1.0 - gold * 0.10) + gold * 0.70, 0.0, 1.0)
    rgb[..., 2] = np.clip(rgb[..., 2] * (1.0 - gold * 0.04) + gold * 0.22, 0.0, 1.0)

    modified = np.dstack((np.clip(rgb, 0.0, 1.0), alpha))
    return Image.fromarray((modified * 255.0).astype(np.uint8), mode="RGBA")


def create_normal_map(height_map):
    dx = np.gradient(height_map, axis=1)
    dy = np.gradient(height_map, axis=0)

    strength = 18.0
    nx = -dx * strength
    ny = dy * strength
    nz = np.ones_like(height_map)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx /= norm
    ny /= norm
    nz /= norm

    normal_rgb = np.dstack(
        (
            (nx * 0.5 + 0.5) * 255.0,
            (ny * 0.5 + 0.5) * 255.0,
            (nz * 0.5 + 0.5) * 255.0,
        )
    ).astype(np.uint8)
    return Image.fromarray(normal_rgb, mode="RGB")


def create_orm_map(height_map, red_mask):
    dx = np.gradient(height_map, axis=1)
    dy = np.gradient(height_map, axis=0)
    gradient = np.clip(np.sqrt(dx * dx + dy * dy) * 14.0, 0.0, 1.0) * red_mask
    ridge = np.clip((height_map - 0.5) * 3.0, 0.0, 1.0) * red_mask
    cavity = np.clip((0.5 - height_map) * 3.4, 0.0, 1.0) * red_mask

    occlusion = np.clip(1.0 - (cavity * 0.52 + gradient * 0.18), 0.48, 1.0)
    roughness = np.clip(0.38 + cavity * 0.36 + gradient * 0.20 - ridge * 0.10, 0.18, 0.88)
    metallic = np.clip(0.42 + ridge * 0.18 - cavity * 0.04, 0.24, 0.78)

    orm = np.dstack((occlusion, roughness, metallic))
    return Image.fromarray((orm * 255.0).astype(np.uint8), mode="RGB")


def save_compare_image(original_base, modified_base, height_map_image, normal_map_image, orm_map_image):
    previews = [
        ("Original", original_base.convert("RGB")),
        ("Embossed Base", modified_base.convert("RGB")),
        ("Height Map", ImageOps.colorize(height_map_image, black="#2f241f", white="#f3e3ca")),
        ("Normal Map", normal_map_image.convert("RGB")),
        ("ORM Map", orm_map_image.convert("RGB")),
    ]

    thumb_width = 640
    thumb_height = 320
    padding = 28
    title_h = 62
    canvas = Image.new("RGB", (padding + len(previews) * (thumb_width + padding), thumb_height + padding * 2 + title_h), (239, 232, 222))
    draw = ImageDraw.Draw(canvas)

    for index, (label, image) in enumerate(previews):
        card_x = padding + index * (thumb_width + padding)
        card_y = padding + title_h
        draw.rounded_rectangle([card_x - 10, card_y - 10, card_x + thumb_width + 10, card_y + thumb_height + 10], radius=18, fill=(250, 246, 240), outline=(196, 179, 158), width=3)
        draw.text((card_x, padding + 18), label, fill=(90, 73, 57))

        preview = image.copy()
        preview.thumbnail((thumb_width, thumb_height))
        offset_x = card_x + (thumb_width - preview.width) // 2
        offset_y = card_y + (thumb_height - preview.height) // 2
        canvas.paste(preview, (offset_x, offset_y))

    canvas.save(OUTPUT_DIR / COMPARE_IMAGE_NAME)


def append_image_and_texture(gltf, filename):
    for image_index, image in enumerate(gltf.get("images", [])):
        if image.get("uri") == filename:
            for texture_index, texture in enumerate(gltf.get("textures", [])):
                if texture.get("source") == image_index:
                    return image_index, texture_index
            texture_index = len(gltf.setdefault("textures", []))
            gltf["textures"].append({"source": image_index, "sampler": 0})
            return image_index, texture_index

    image_index = len(gltf.setdefault("images", []))
    gltf["images"].append({"uri": filename, "name": filename})
    texture_index = len(gltf.setdefault("textures", []))
    gltf["textures"].append({"source": image_index, "sampler": 0})
    return image_index, texture_index


def update_receiver_material(gltf):
    _, normal_texture_index = append_image_and_texture(gltf, NORMAL_TEXTURE_NAME)
    _, orm_texture_index = append_image_and_texture(gltf, ORM_TEXTURE_NAME)

    receiver_material = None
    for material in gltf.get("materials", []):
        if material.get("name") == "ReceiverBody":
            receiver_material = material
            break

    if receiver_material is None:
        raise KeyError("ReceiverBody material was not found in model.gltf")

    pbr = receiver_material.setdefault("pbrMetallicRoughness", {})
    pbr["roughnessFactor"] = 1.0
    pbr["metallicFactor"] = 1.0
    pbr["metallicRoughnessTexture"] = {"index": orm_texture_index}
    receiver_material["normalTexture"] = {"index": normal_texture_index, "scale": 1.35}
    receiver_material["occlusionTexture"] = {"index": orm_texture_index, "strength": 0.72}
    receiver_material.setdefault("extras", {})["variant"] = "embossed_dragon_v02"


def update_meta():
    meta_path = OUTPUT_DIR / "weapon03_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["variant"] = "modification_optimization_02_embossed_dragon"
    meta["detail_strategy"] = "receiver_body_basecolor_plus_generated_normal_and_orm"
    meta["modifications"] = {
        "target_component": "ReceiverBody",
        "variant_goal": "embossed_dragon",
        "generated_textures": [
            BODY_TEXTURE_NAME,
            HEIGHT_TEXTURE_NAME,
            NORMAL_TEXTURE_NAME,
            ORM_TEXTURE_NAME,
        ],
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def build_viewer_manifest(gltf):
    nodes = gltf.get("nodes", [])
    meshes = gltf.get("meshes", [])
    materials = gltf.get("materials", [])
    textures = gltf.get("textures", [])
    images = gltf.get("images", [])
    accessors = gltf.get("accessors", [])
    animations = gltf.get("animations", [])

    parents = {}
    for node_index, node in enumerate(nodes):
        for child_index in node.get("children", []):
            parents[child_index] = node_index

    def build_hierarchy(node_index):
        node = nodes[node_index]
        return {
            "index": node_index,
            "name": node.get("name", f"Node {node_index}"),
            "children": [build_hierarchy(child_index) for child_index in node.get("children", [])],
        }

    def image_label(texture_index):
        if texture_index is None or texture_index >= len(textures):
            return ""
        source_index = textures[texture_index]["source"]
        if source_index >= len(images):
            return ""
        image = images[source_index]
        return image.get("name") or image.get("uri") or f"Image {source_index}"

    components = []
    total_vertices = 0
    total_triangles = 0
    for node_index, node in enumerate(nodes):
        mesh_index = node.get("mesh")
        if mesh_index is None:
            continue
        mesh = meshes[mesh_index]
        primitive = mesh["primitives"][0]
        material_index = primitive["material"]
        position_accessor = accessors[primitive["attributes"]["POSITION"]]
        index_accessor = accessors[primitive["indices"]]
        vertices = int(position_accessor["count"])
        triangles = int(index_accessor["count"] // 3)
        total_vertices += vertices
        total_triangles += triangles
        parent_index = parents.get(node_index)
        parent_name = nodes[parent_index]["name"] if parent_index is not None else ""
        material_name = materials[material_index]["name"] if material_index < len(materials) else f"Material {material_index}"
        components.append(
            {
                "nodeName": node.get("name", f"Node {node_index}"),
                "meshName": mesh.get("name", f"Mesh {mesh_index}"),
                "groupName": parent_name,
                "materialName": material_name,
                "vertices": vertices,
                "triangles": triangles,
            }
        )

    material_entries = []
    for material_index, material in enumerate(materials):
        pbr = material.get("pbrMetallicRoughness", {})
        texture_info = pbr.get("baseColorTexture")
        mr_info = pbr.get("metallicRoughnessTexture")
        normal_info = material.get("normalTexture")
        material_entries.append(
            {
                "name": material.get("name", f"Material {material_index}"),
                "alphaMode": material.get("alphaMode", "OPAQUE"),
                "baseColorTexture": image_label(texture_info["index"]) if texture_info else "",
                "metallicRoughnessTexture": image_label(mr_info["index"]) if mr_info else "",
                "normalTexture": image_label(normal_info["index"]) if normal_info else "",
                "emissiveFactor": material.get("emissiveFactor", []),
            }
        )

    animation_entries = [
        {
            "name": animation.get("name", f"Animation {index}"),
            "loop": bool(animation.get("extras", {}).get("loop")),
        }
        for index, animation in enumerate(animations)
    ]

    scene_index = gltf.get("scene", 0)
    hierarchy = [build_hierarchy(root_index) for root_index in gltf["scenes"][scene_index]["nodes"]]

    return {
        "title": "Weapon03 / Embossed Dragon V02",
        "subtitle": "Receiver body updated with embossed dragon base, normal, and ORM textures",
        "stats": {
            "nodes": len(nodes),
            "meshes": len(meshes),
            "materials": len(materials),
            "textures": len(textures),
            "animations": len(animations),
            "vertices": total_vertices,
            "triangles": total_triangles,
        },
        "animations": animation_entries,
        "components": components,
        "materials": material_entries,
        "hierarchy": hierarchy,
    }


def write_glb(gltf, buffer_data):
    glb_dict = copy.deepcopy(gltf)
    binary_blob = bytearray(buffer_data)

    for image in glb_dict.get("images", []):
        uri = image.pop("uri", None)
        if uri is None:
            continue
        image_path = OUTPUT_DIR / uri
        image_bytes = image_path.read_bytes()
        if len(binary_blob) % 4:
            binary_blob.extend(b"\x00" * (4 - (len(binary_blob) % 4)))
        offset = len(binary_blob)
        binary_blob.extend(image_bytes)
        view_index = len(glb_dict["bufferViews"])
        glb_dict["bufferViews"].append({"buffer": 0, "byteOffset": offset, "byteLength": len(image_bytes)})
        image["bufferView"] = view_index
        image["mimeType"] = IMAGE_MIME_TYPES.get(image_path.suffix.lower(), "application/octet-stream")

    glb_dict["buffers"] = [{"byteLength": len(binary_blob)}]
    model = GLTF2.from_dict(glb_dict)
    model.set_binary_blob(bytes(binary_blob))
    model.save_binary(str(OUTPUT_DIR / "model.glb"))


def write_viewer_data(gltf):
    glb_data = (OUTPUT_DIR / "model.glb").read_bytes()
    payload = {
        "manifest": build_viewer_manifest(gltf),
        "modelBase64": base64.b64encode(glb_data).decode("ascii"),
    }
    viewer_data = "window.WEAPON_VIEWER_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (OUTPUT_DIR / "viewer-data.js").write_text(viewer_data, encoding="utf-8")


def write_readme():
    readme = """# 修改优化02 - 有浮雕感的龙纹

## 1. 版本目标

这是基于原版 `武器/枪/枪03/枪的模型` 制作的第二个独立优化版本。

- 只针对 `ReceiverBody` 枪体主体做升级
- 保留模型结构、动画、节点和其他贴图
- 在原枪体贴图基础上加入更有浮雕感的龙纹
- 额外生成 `Normal` 和 `ORM` 贴图来增强金属雕纹、刻线和压纹效果

## 2. 主要文件

- `model.gltf`
- `model.glb`
- `T_XCR_Iron_Rouge_body_B.png`
- `T_XCR_Iron_Rouge_body_height_dragonEmboss_v02.png`
- `T_XCR_Iron_Rouge_body_normal_dragonEmboss_v02.png`
- `T_XCR_Iron_Rouge_body_orm_dragonEmboss_v02.png`
- `dragon_emboss_compare.png`
- `build_embossed_dragon_v02.py`
- `纯浮雕龙纹_实现过程.md`

## 3. 重新生成

```bash
python3 build_embossed_dragon_v02.py
```

## 4. 查看

- 直接双击 `viewer.html`
- 或导入 `model.glb` 到 Blender / Babylon / glTF 查看器
"""
    (OUTPUT_DIR / "README.md").write_text(readme, encoding="utf-8")


def main():
    copy_base_assets()
    backup_original_body()

    original_body = Image.open(OUTPUT_DIR / BODY_TEXTURE_BACKUP_NAME).convert("RGBA")
    height_map, red_mask = create_height_map(original_body)
    modified_body = create_modified_base_color(original_body, height_map, red_mask)
    normal_map = create_normal_map(height_map)
    orm_map = create_orm_map(height_map, red_mask)

    Image.fromarray((height_map * 255.0).astype(np.uint8), mode="L").save(OUTPUT_DIR / HEIGHT_TEXTURE_NAME)
    modified_body.save(OUTPUT_DIR / BODY_TEXTURE_NAME)
    normal_map.save(OUTPUT_DIR / NORMAL_TEXTURE_NAME)
    orm_map.save(OUTPUT_DIR / ORM_TEXTURE_NAME)
    save_compare_image(
        original_body,
        modified_body,
        Image.open(OUTPUT_DIR / HEIGHT_TEXTURE_NAME).convert("L"),
        normal_map,
        orm_map,
    )

    gltf = load_gltf()
    update_receiver_material(gltf)
    save_gltf(gltf)
    update_meta()
    write_readme()

    buffer_data = (OUTPUT_DIR / "buffer.bin").read_bytes()
    write_glb(gltf, buffer_data)
    write_viewer_data(gltf)

    print(OUTPUT_DIR / "model.gltf")
    print(OUTPUT_DIR / "model.glb")
    print(OUTPUT_DIR / BODY_TEXTURE_NAME)
    print(OUTPUT_DIR / NORMAL_TEXTURE_NAME)
    print(OUTPUT_DIR / ORM_TEXTURE_NAME)
    print(OUTPUT_DIR / COMPARE_IMAGE_NAME)


if __name__ == "__main__":
    main()
