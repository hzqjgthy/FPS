#!/usr/bin/env python3

import base64
import copy
import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from pygltflib import GLTF2


ROOT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = ROOT_DIR.parent / "枪的模型"
OUTPUT_DIR = ROOT_DIR

BODY_TEXTURE_NAME = "T_XCR_Iron_Rouge_body_B.png"
BODY_TEXTURE_BACKUP_NAME = "T_XCR_Iron_Rouge_body_B.original.png"
COMPARE_IMAGE_NAME = "dragon_visual_compare.png"

REQUIRED_FILES = [
    "model.gltf",
    "buffer.bin",
    "glass.png",
    "EM_Orange.png",
    "T_XCR_Iron_Rouge_scope02_B.png",
    "T_XCR_Iron_Rouge_magazine_B.png",
    BODY_TEXTURE_NAME,
    "T_XCR_Iron_Rouge_scope01_B.png",
    "weapon03_meta.json",
]

VIEWER_FILES = ["viewer.html"]
VIEWER_DIRS = ["viewer-assets"]

IMAGE_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def copy_base_assets():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for filename in REQUIRED_FILES:
        shutil.copy2(SOURCE_DIR / filename, OUTPUT_DIR / filename)

    for filename in VIEWER_FILES:
        shutil.copy2(SOURCE_DIR / filename, OUTPUT_DIR / filename)

    for dirname in VIEWER_DIRS:
        source_path = SOURCE_DIR / dirname
        target_path = OUTPUT_DIR / dirname
        if target_path.exists():
            shutil.rmtree(target_path)
        shutil.copytree(source_path, target_path)


def normalize_gltf_image_uris():
    gltf_path = OUTPUT_DIR / "model.gltf"
    gltf = json.loads(gltf_path.read_text(encoding="utf-8"))
    for image in gltf.get("images", []):
        uri = image.get("uri")
        if not uri or uri.startswith("data:"):
            continue
        image["uri"] = Path(uri).name
        image["name"] = Path(uri).name
    gltf_path.write_text(json.dumps(gltf, ensure_ascii=False, indent=2), encoding="utf-8")
    return gltf


def backup_original_body_texture():
    shutil.copy2(SOURCE_DIR / BODY_TEXTURE_NAME, OUTPUT_DIR / BODY_TEXTURE_BACKUP_NAME)


def polyline_points(points, segments_per_step=12):
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


def build_red_mask(base_image):
    pixels = np.asarray(base_image.convert("RGBA"), dtype=np.uint8)
    red_mask = (
        (pixels[..., 0] > pixels[..., 1] * 1.1)
        & (pixels[..., 0] > pixels[..., 2] * 1.1)
        & (pixels[..., 0] > 70)
        & (pixels[..., 3] > 0)
    )
    mask = Image.fromarray((red_mask.astype(np.uint8) * 255), mode="L")
    return mask.filter(ImageFilter.GaussianBlur(1.5))


def apply_mask(image, mask):
    red, green, blue, alpha = image.split()
    alpha = ImageChops.multiply(alpha, mask)
    return Image.merge("RGBA", (red, green, blue, alpha))


def draw_scale_band(draw, sampled_points, color):
    for t in np.linspace(0.08, 0.92, 15):
        x, y, angle = point_and_angle(sampled_points, float(t))
        normal_angle = angle + math.pi * 0.5
        scale_length = 18
        base_width = 14
        tip = (x + math.cos(normal_angle) * scale_length, y + math.sin(normal_angle) * scale_length)
        left = (x - math.cos(angle) * base_width, y - math.sin(angle) * base_width)
        right = (x + math.cos(angle) * base_width, y + math.sin(angle) * base_width)
        draw.polygon([left, tip, right], fill=color)


def draw_dragon_head(draw, anchor, angle):
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
        (-8, -6),
        (18, -18),
        (44, -20),
        (72, -10),
        (58, 4),
        (82, 18),
        (62, 18),
        (28, 12),
        (14, 22),
        (-12, 18),
    ]
    horn_top = [(-2, -4), (22, -30), (34, -28), (16, -10)]
    horn_lower = [(4, 6), (28, 32), (40, 28), (18, 12)]
    eye = [(24, -1), (38, -5), (30, 8)]

    draw.polygon([transform(point) for point in head_outline], fill=(234, 184, 70, 220))
    draw.polygon([transform(point) for point in horn_top], fill=(255, 222, 150, 210))
    draw.polygon([transform(point) for point in horn_lower], fill=(198, 76, 28, 190))
    draw.polygon([transform(point) for point in eye], fill=(92, 8, 0, 220))
    draw.line([transform((12, 10)), transform((34, 3)), transform((52, 10))], fill=(75, 10, 6, 160), width=4)


def create_dragon_overlay(base_image):
    size = base_image.size
    red_mask = build_red_mask(base_image)

    shadow_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    glow_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    line_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    detail_layer = Image.new("RGBA", size, (0, 0, 0, 0))

    shadow_draw = ImageDraw.Draw(shadow_layer)
    glow_draw = ImageDraw.Draw(glow_layer)
    line_draw = ImageDraw.Draw(line_layer)
    detail_draw = ImageDraw.Draw(detail_layer)

    main_spine = [
        (170, 874),
        (410, 804),
        (690, 728),
        (980, 640),
        (1240, 474),
        (1520, 300),
        (1805, 228),
    ]
    lower_band = [
        (180, 934),
        (345, 900),
        (560, 886),
        (792, 914),
        (1002, 962),
    ]
    mid_band = [
        (220, 562),
        (380, 530),
        (582, 544),
        (760, 596),
    ]

    for points, shadow_width, glow_width, line_width in [
        (main_spine, 46, 30, 14),
        (lower_band, 34, 24, 10),
        (mid_band, 28, 18, 8),
    ]:
        shadow_draw.line(points, fill=(40, 7, 5, 110), width=shadow_width, joint="curve")
        glow_draw.line(points, fill=(255, 116, 36, 118), width=glow_width, joint="curve")
        line_draw.line(points, fill=(230, 176, 64, 214), width=line_width, joint="curve")
        line_draw.line(points, fill=(255, 227, 158, 120), width=max(2, line_width // 3), joint="curve")

    sampled_main = polyline_points(main_spine)
    sampled_lower = polyline_points(lower_band)
    sampled_mid = polyline_points(mid_band)

    draw_scale_band(detail_draw, sampled_main, (205, 78, 22, 120))
    draw_scale_band(detail_draw, sampled_lower, (210, 90, 24, 110))
    draw_scale_band(detail_draw, sampled_mid, (255, 208, 122, 84))

    x, y, angle = point_and_angle(sampled_main, 0.94)
    draw_dragon_head(detail_draw, (x, y), angle)

    rune_positions = [(1330, 380), (1460, 346), (1610, 314), (1770, 284)]
    for px, py in rune_positions:
        detail_draw.line([(px - 20, py + 10), (px + 10, py - 10), (px + 24, py + 12)], fill=(255, 231, 174, 132), width=5)

    shadow_layer = apply_mask(shadow_layer, red_mask)
    glow_layer = apply_mask(glow_layer.filter(ImageFilter.GaussianBlur(7)), red_mask)
    line_layer = apply_mask(line_layer, red_mask)
    detail_layer = apply_mask(detail_layer.filter(ImageFilter.GaussianBlur(0.3)), red_mask)

    combined = Image.alpha_composite(base_image, shadow_layer)
    combined = Image.alpha_composite(combined, glow_layer)
    combined = Image.alpha_composite(combined, detail_layer)
    combined = Image.alpha_composite(combined, line_layer)
    return combined


def save_compare_preview(original_image, modified_image):
    width, height = original_image.size
    padding = 36
    label_bar = 72
    canvas = Image.new("RGBA", (width * 2 + padding * 3, height + padding * 2 + label_bar), (239, 232, 222, 255))
    draw = ImageDraw.Draw(canvas)

    left_x = padding
    right_x = width + padding * 2
    image_y = padding + label_bar

    draw.rounded_rectangle([left_x - 12, image_y - 12, left_x + width + 12, image_y + height + 12], radius=18, fill=(250, 246, 240, 255), outline=(196, 179, 158, 255), width=3)
    draw.rounded_rectangle([right_x - 12, image_y - 12, right_x + width + 12, image_y + height + 12], radius=18, fill=(250, 246, 240, 255), outline=(196, 179, 158, 255), width=3)
    draw.text((left_x, padding + 18), "Original Body Texture", fill=(86, 67, 51, 255))
    draw.text((right_x, padding + 18), "V01 Pure Visual Dragon", fill=(134, 51, 22, 255))

    canvas.alpha_composite(original_image, (left_x, image_y))
    canvas.alpha_composite(modified_image, (right_x, image_y))
    canvas.convert("RGB").save(OUTPUT_DIR / COMPARE_IMAGE_NAME)


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
        material_entries.append(
            {
                "name": material.get("name", f"Material {material_index}"),
                "alphaMode": material.get("alphaMode", "OPAQUE"),
                "baseColorTexture": image_label(texture_info["index"]) if texture_info else "",
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
        "title": "Weapon03 / Pure Visual Dragon V01",
        "subtitle": "Receiver body texture variant with non-destructive dragon-pattern styling",
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


def main():
    copy_base_assets()
    gltf = normalize_gltf_image_uris()
    backup_original_body_texture()

    original_body = Image.open(OUTPUT_DIR / BODY_TEXTURE_BACKUP_NAME).convert("RGBA")
    modified_body = create_dragon_overlay(original_body)
    modified_body.save(OUTPUT_DIR / BODY_TEXTURE_NAME)
    save_compare_preview(original_body, modified_body)

    buffer_data = (OUTPUT_DIR / "buffer.bin").read_bytes()
    write_glb(gltf, buffer_data)
    write_viewer_data(gltf)

    print(OUTPUT_DIR / "model.gltf")
    print(OUTPUT_DIR / "model.glb")
    print(OUTPUT_DIR / BODY_TEXTURE_NAME)
    print(OUTPUT_DIR / COMPARE_IMAGE_NAME)
    print(OUTPUT_DIR / "viewer.html")


if __name__ == "__main__":
    main()
