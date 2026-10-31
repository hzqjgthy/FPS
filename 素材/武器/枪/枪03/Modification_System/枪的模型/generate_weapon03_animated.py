#!/usr/bin/env python3

import base64
import copy
import json
import math
import shutil
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from PIL import Image, ImageDraw
from pygltflib import GLTF2


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR
PRIMARY_SOURCE_DIR = SCRIPT_DIR.parent / "【CG】枪  科技枪  现代科技枪  狙击步枪  游戏装备  红龙枪械_gltf_515270"

FLOAT = 5126
UNSIGNED_SHORT = 5123
ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963

COMPONENT_DTYPE = {
    5120: np.dtype("i1"),
    5121: np.dtype("u1"),
    5122: np.dtype("<i2"),
    5123: np.dtype("<u2"),
    5125: np.dtype("<u4"),
    5126: np.dtype("<f4"),
}

ACCESSOR_COMPONENTS = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}

IMAGE_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

VIEWER_RUNTIME_FILES = {
    "viewer-assets/babylon.js": "https://cdn.babylonjs.com/babylon.js",
    "viewer-assets/babylonjs.loaders.min.js": "https://cdn.babylonjs.com/loaders/babylonjs.loaders.min.js",
}

MESH_RULES = {
    "MT_XCR_Iron_Rouge_body": {
        "mesh_name": "receiver_body",
        "node_name": "receiver_body_node",
        "group": "receiver",
        "material_name": "ReceiverBody",
    },
    "MT_XCR_Iron_Rouge_magazine": {
        "mesh_name": "magazine_body",
        "node_name": "magazine_body_node",
        "group": "magazine",
        "material_name": "MagazineBody",
    },
    "MT_XCR_Iron_Rouge_scope01": {
        "mesh_name": "scope_upper",
        "node_name": "scope_upper_node",
        "group": "receiver",
        "material_name": "ScopeUpper",
    },
    "MT_XCR_Iron_Rouge_scope02": {
        "mesh_name": "scope_lower",
        "node_name": "scope_lower_node",
        "group": "receiver",
        "material_name": "ScopeLower",
    },
    "MT_Xmas_Glass_Dup": {
        "mesh_name": "scope_glass",
        "node_name": "scope_glass_node",
        "group": "receiver",
        "material_name": "ScopeGlass",
    },
    "MT_XCR_Iron_Rouge_EM_orange_Dup": {
        "mesh_name": "scope_emissive_panel",
        "node_name": "scope_emissive_panel_node",
        "group": "receiver",
        "material_name": "ScopeEmissivePanel",
    },
    "MT_RobinsonXCR_Premium_EM_orang": {
        "mesh_name": "scope_emissive_core",
        "node_name": "scope_emissive_core_node",
        "group": "receiver",
        "material_name": "ScopeEmissiveCore",
    },
}


def resolve_source_gltf():
    candidate_dirs = [PRIMARY_SOURCE_DIR, OUTPUT_DIR]
    for candidate_dir in candidate_dirs:
        matches = sorted(candidate_dir.glob("*.gltf"))
        if matches:
            return candidate_dir, matches[0]
    raise FileNotFoundError("No source glTF file was found for weapon03.")


SOURCE_DIR, SOURCE_GLTF = resolve_source_gltf()


def normalize_quat(q):
    q = np.asarray(q, dtype=np.float64)
    norm = np.linalg.norm(q)
    if norm == 0.0:
        return np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)
    return q / norm


def quat_mul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array(
        [
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz,
        ],
        dtype=np.float64,
    )


def quat_from_axis_angle(axis, angle_deg):
    angle_rad = math.radians(angle_deg) * 0.5
    s = math.sin(angle_rad)
    c = math.cos(angle_rad)
    ax, ay, az = axis
    return np.array([ax * s, ay * s, az * s, c], dtype=np.float64)


def quat_from_euler_xyz(x_deg, y_deg, z_deg):
    qx = quat_from_axis_angle((1.0, 0.0, 0.0), x_deg)
    qy = quat_from_axis_angle((0.0, 1.0, 0.0), y_deg)
    qz = quat_from_axis_angle((0.0, 0.0, 1.0), z_deg)
    return normalize_quat(quat_mul(quat_mul(qz, qy), qx))


def rotate_vectors(q, vectors):
    q = normalize_quat(q)
    x, y, z, w = q
    matrix = np.array(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )
    return np.asarray(vectors, dtype=np.float64) @ matrix.T


def load_source():
    source = json.loads(SOURCE_GLTF.read_text(encoding="utf-8"))
    buffer_uri = source["buffers"][0]["uri"]
    buffer_path = SOURCE_DIR / buffer_uri
    return source, buffer_path.read_bytes()


def read_accessor_array(source, buffer_blob, accessor_index):
    accessor = source["accessors"][accessor_index]
    view = source["bufferViews"][accessor["bufferView"]]
    dtype = COMPONENT_DTYPE[accessor["componentType"]]
    components = ACCESSOR_COMPONENTS[accessor["type"]]
    component_size = dtype.itemsize
    stride = view.get("byteStride", component_size * components)
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    count = accessor["count"]

    if stride == component_size * components:
        raw = buffer_blob[offset : offset + count * stride]
        array = np.frombuffer(raw, dtype=dtype, count=count * components)
        if components == 1:
            return array.copy()
        return array.reshape(count, components).copy()

    output = np.empty((count, components), dtype=dtype)
    for index in range(count):
        start = offset + index * stride
        chunk = buffer_blob[start : start + component_size * components]
        output[index] = np.frombuffer(chunk, dtype=dtype, count=components)
    if components == 1:
        return output.reshape(count).copy()
    return output.copy()


class BufferBuilder:
    def __init__(self):
        self.data = bytearray()
        self.buffer_views = []
        self.accessors = []

    def add_blob(self, blob, target=None):
        if len(self.data) % 4:
            self.data.extend(b"\x00" * (4 - (len(self.data) % 4)))
        offset = len(self.data)
        self.data.extend(blob)
        view = {"buffer": 0, "byteOffset": offset, "byteLength": len(blob)}
        if target is not None:
            view["target"] = target
        self.buffer_views.append(view)
        return len(self.buffer_views) - 1

    def add_accessor(self, array, component_type, accessor_type, target=None):
        arr = np.asarray(array)
        if component_type == FLOAT:
            arr = arr.astype("<f4")
        elif component_type == UNSIGNED_SHORT:
            arr = arr.astype("<u2")
        else:
            raise ValueError(f"Unsupported component type: {component_type}")

        view_index = self.add_blob(arr.tobytes(), target=target)
        accessor = {
            "bufferView": view_index,
            "componentType": component_type,
            "count": int(arr.shape[0]),
            "type": accessor_type,
        }
        if accessor_type == "SCALAR":
            accessor["min"] = [int(arr.min()) if component_type == UNSIGNED_SHORT else float(arr.min())]
            accessor["max"] = [int(arr.max()) if component_type == UNSIGNED_SHORT else float(arr.max())]
        else:
            flat = arr.reshape(arr.shape[0], ACCESSOR_COMPONENTS[accessor_type])
            accessor["min"] = [float(value) for value in flat.min(axis=0)]
            accessor["max"] = [float(value) for value in flat.max(axis=0)]
        self.accessors.append(accessor)
        return len(self.accessors) - 1


def classify_mesh(material_name):
    if material_name not in MESH_RULES:
        raise KeyError(f"Unexpected material: {material_name}")
    return MESH_RULES[material_name]


def build_materials(source):
    images = copy.deepcopy(source.get("images", []))
    textures = copy.deepcopy(source.get("textures", []))
    samplers = copy.deepcopy(source.get("samplers", []))
    materials = copy.deepcopy(source.get("materials", []))

    for image in images:
        uri = image.get("uri")
        if not uri or uri.startswith("data:"):
            continue
        image["uri"] = Path(uri).name

    emissive_texture_index = None
    for texture_index, texture in enumerate(textures):
        image = images[texture["source"]]
        if image.get("uri") == "EM_Orange.png":
            emissive_texture_index = texture_index
            break

    for material in materials:
        source_name = material.get("name", "")
        rule = classify_mesh(source_name)
        material["name"] = rule["material_name"]
        material.setdefault("extras", {})["source_material_name"] = source_name

        if "Glass" in material["name"]:
            material["alphaMode"] = "BLEND"
            material["doubleSided"] = False
            material.setdefault("pbrMetallicRoughness", {}).setdefault("baseColorFactor", [1.0, 1.0, 1.0, 0.72])
            material["pbrMetallicRoughness"]["metallicFactor"] = 0.0
            material["pbrMetallicRoughness"]["roughnessFactor"] = 0.08

        if "Emissive" in material["name"] and emissive_texture_index is not None:
            material["emissiveTexture"] = {"index": emissive_texture_index}
            material["emissiveFactor"] = [1.0, 0.38, 0.08]
            material.setdefault("pbrMetallicRoughness", {}).setdefault("roughnessFactor", 0.2)

    return images, textures, samplers, materials


def build_mesh_records(source, buffer_blob):
    records = []
    source_scene = source.get("scene", 0)
    root_indices = source["scenes"][source_scene]["nodes"]

    for root_index in root_indices:
        root_node = source["nodes"][root_index]
        for child_index in root_node.get("children", []):
            child = source["nodes"][child_index]
            if "mesh" not in child:
                continue

            mesh = source["meshes"][child["mesh"]]
            primitive = mesh["primitives"][0]
            material_index = primitive["material"]
            material_name = source["materials"][material_index]["name"]
            rule = classify_mesh(material_name)

            positions = read_accessor_array(source, buffer_blob, primitive["attributes"]["POSITION"]).astype(np.float32)
            normals = read_accessor_array(source, buffer_blob, primitive["attributes"]["NORMAL"]).astype(np.float32)
            texcoords = read_accessor_array(source, buffer_blob, primitive["attributes"]["TEXCOORD_0"]).astype(np.float32)
            indices = read_accessor_array(source, buffer_blob, primitive["indices"]).astype(np.uint16)

            rotation = child.get("rotation", [0.0, 0.0, 0.0, 1.0])
            positions = rotate_vectors(rotation, positions).astype(np.float32)
            normals = rotate_vectors(rotation, normals)
            normal_lengths = np.linalg.norm(normals, axis=1, keepdims=True)
            normals = (normals / np.where(normal_lengths == 0.0, 1.0, normal_lengths)).astype(np.float32)

            records.append(
                {
                    "group": rule["group"],
                    "mesh_name": rule["mesh_name"],
                    "node_name": rule["node_name"],
                    "material_index": material_index,
                    "positions": positions,
                    "normals": normals,
                    "texcoords": texcoords,
                    "indices": indices,
                }
            )

    return records


def build_animations(node_lookup):
    def trans_track(node_name, times, values):
        return {
            "node": node_lookup[node_name],
            "path": "translation",
            "times": np.asarray(times, dtype=np.float32),
            "values": np.asarray(values, dtype=np.float32),
        }

    def rot_track(node_name, times, eulers):
        return {
            "node": node_lookup[node_name],
            "path": "rotation",
            "times": np.asarray(times, dtype=np.float32),
            "values": np.asarray([quat_from_euler_xyz(*angles) for angles in eulers], dtype=np.float32),
        }

    return [
        {
            "name": "idle",
            "extras": {"loop": True},
            "tracks": [
                trans_track(
                    "WeaponPose",
                    [0.0, 0.55, 1.1, 1.65],
                    [(0.0, 0.0, 0.0), (0.0, 0.004, -0.003), (0.0, 0.0, 0.0), (0.0, -0.002, -0.001)],
                ),
                rot_track(
                    "WeaponPose",
                    [0.0, 0.55, 1.1, 1.65],
                    [(0.4, -0.4, 0.0), (0.9, 0.3, -0.5), (0.2, -0.2, 0.1), (0.4, -0.4, 0.0)],
                ),
            ],
        },
        {
            "name": "fire",
            "extras": {"loop": False},
            "tracks": [
                trans_track(
                    "WeaponPose",
                    [0.0, 0.035, 0.08, 0.14, 0.24],
                    [(0.0, 0.0, 0.0), (0.0, -0.004, -0.026), (0.0, 0.002, -0.012), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)],
                ),
                rot_track(
                    "WeaponPose",
                    [0.0, 0.035, 0.08, 0.14, 0.24],
                    [(0.0, 0.0, 0.0), (4.0, 0.0, 1.2), (1.5, 0.0, 0.4), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)],
                ),
            ],
        },
        {
            "name": "reload",
            "extras": {"loop": False},
            "tracks": [
                trans_track(
                    "WeaponPose",
                    [0.0, 0.18, 0.42, 0.72, 1.02, 1.34],
                    [(0.0, 0.0, 0.0), (0.012, -0.010, 0.020), (0.026, -0.030, 0.046), (0.022, -0.024, 0.036), (0.008, -0.008, 0.012), (0.0, 0.0, 0.0)],
                ),
                rot_track(
                    "WeaponPose",
                    [0.0, 0.18, 0.42, 0.72, 1.02, 1.34],
                    [(0.0, 0.0, 0.0), (7.0, 0.0, 10.0), (16.0, 0.0, 20.0), (10.0, 0.0, 11.0), (3.0, 0.0, 3.0), (0.0, 0.0, 0.0)],
                ),
                trans_track(
                    "MagazineGroup",
                    [0.0, 0.12, 0.28, 0.46, 0.76, 0.98, 1.18],
                    [
                        (0.0, 0.0, 0.0),
                        (0.0, -0.028, 0.006),
                        (0.006, -0.095, 0.024),
                        (0.018, -0.165, 0.058),
                        (0.004, -0.050, 0.014),
                        (0.0, -0.010, 0.002),
                        (0.0, 0.0, 0.0),
                    ],
                ),
                rot_track(
                    "MagazineGroup",
                    [0.0, 0.12, 0.28, 0.46, 0.76, 0.98, 1.18],
                    [(0.0, 0.0, 0.0), (4.0, 0.0, -8.0), (10.0, 0.0, -18.0), (16.0, 0.0, -32.0), (4.0, 0.0, -9.0), (0.0, 0.0, -2.0), (0.0, 0.0, 0.0)],
                ),
            ],
        },
        {
            "name": "ads",
            "extras": {"loop": False},
            "tracks": [
                trans_track("WeaponPose", [0.0, 0.18, 0.34], [(0.0, 0.0, 0.0), (0.0, 0.018, -0.050), (0.0, 0.034, -0.082)]),
                rot_track("WeaponPose", [0.0, 0.18, 0.34], [(0.0, 0.0, 0.0), (-1.5, 0.0, -3.0), (-2.5, 0.0, -6.0)]),
            ],
        },
        {
            "name": "sprint",
            "extras": {"loop": True},
            "tracks": [
                trans_track(
                    "WeaponPose",
                    [0.0, 0.36, 0.72, 1.08],
                    [(0.040, -0.060, 0.080), (0.056, -0.086, 0.108), (0.046, -0.070, 0.090), (0.040, -0.060, 0.080)],
                ),
                rot_track(
                    "WeaponPose",
                    [0.0, 0.36, 0.72, 1.08],
                    [(11.0, -6.0, 18.0), (15.0, -8.0, 26.0), (12.0, -6.0, 21.0), (11.0, -6.0, 18.0)],
                ),
            ],
        },
    ]


def build_gltf():
    source, buffer_blob = load_source()
    images, textures, samplers, materials = build_materials(source)
    mesh_records = build_mesh_records(source, buffer_blob)

    builder = BufferBuilder()
    meshes = []
    nodes = [
        {"name": "RedDragonTechSniper_Root", "children": [1]},
        {"name": "WeaponPose", "translation": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0, 1.0], "children": [2, 3]},
        {"name": "ReceiverGroup", "translation": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0, 1.0], "children": []},
        {"name": "MagazineGroup", "translation": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0, 1.0], "children": []},
    ]
    node_lookup = {"WeaponPose": 1, "MagazineGroup": 3}

    preview_parts = []
    for record in mesh_records:
        position_accessor = builder.add_accessor(record["positions"], FLOAT, "VEC3", target=ARRAY_BUFFER)
        normal_accessor = builder.add_accessor(record["normals"], FLOAT, "VEC3", target=ARRAY_BUFFER)
        texcoord_accessor = builder.add_accessor(record["texcoords"], FLOAT, "VEC2", target=ARRAY_BUFFER)
        index_accessor = builder.add_accessor(record["indices"], UNSIGNED_SHORT, "SCALAR", target=ELEMENT_ARRAY_BUFFER)

        mesh_index = len(meshes)
        meshes.append(
            {
                "name": record["mesh_name"],
                "primitives": [
                    {
                        "attributes": {
                            "POSITION": position_accessor,
                            "NORMAL": normal_accessor,
                            "TEXCOORD_0": texcoord_accessor,
                        },
                        "indices": index_accessor,
                        "material": record["material_index"],
                    }
                ],
            }
        )

        node_index = len(nodes)
        nodes.append({"name": record["node_name"], "mesh": mesh_index})
        group_index = 2 if record["group"] == "receiver" else 3
        nodes[group_index]["children"].append(node_index)

        preview_parts.append(
            {
                "material_index": record["material_index"],
                "positions": record["positions"],
                "indices": record["indices"],
            }
        )

    animations = []
    for clip in build_animations(node_lookup):
        samplers_json = []
        channels_json = []
        for track in clip["tracks"]:
            input_accessor = builder.add_accessor(track["times"], FLOAT, "SCALAR")
            output_type = "VEC4" if track["path"] == "rotation" else "VEC3"
            output_accessor = builder.add_accessor(track["values"], FLOAT, output_type)
            sampler_index = len(samplers_json)
            samplers_json.append({"input": input_accessor, "output": output_accessor, "interpolation": "LINEAR"})
            channels_json.append({"sampler": sampler_index, "target": {"node": track["node"], "path": track["path"]}})
        animations.append({"name": clip["name"], "samplers": samplers_json, "channels": channels_json, "extras": clip["extras"]})

    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "Codex Weapon03 Original-Detail Animation Organizer",
        },
        "scene": 0,
        "scenes": [{"name": "Weapon03AnimatedScene", "nodes": [0]}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "textures": textures,
        "images": images,
        "samplers": samplers,
        "animations": animations,
        "bufferViews": builder.buffer_views,
        "accessors": builder.accessors,
        "buffers": [{"byteLength": len(builder.data), "uri": "buffer.bin"}],
        "extras": {
            "source_asset": source.get("asset", {}),
            "pipeline": {
                "preserve_original_mesh_detail": True,
                "discarded_source_root_translation": True,
                "baked_source_mesh_rotation": True,
                "discarded_source_export_scale": True,
            },
        },
    }
    return gltf, builder.data, preview_parts, materials, images


def average_texture_color(image_path, fallback):
    try:
        image = Image.open(image_path).convert("RGBA")
    except Exception:
        return np.asarray(fallback, dtype=np.float64)

    pixels = np.asarray(image, dtype=np.float64).reshape(-1, 4)
    alpha = pixels[:, 3] / 255.0
    mask = alpha > 0.02
    if np.any(mask):
        weighted_alpha = alpha[mask][:, None]
        rgb = (pixels[mask, :3] * weighted_alpha).sum(axis=0) / max(weighted_alpha.sum(), 1e-6)
        return rgb
    return pixels[:, :3].mean(axis=0)


def render_preview(output_dir, preview_parts, materials, images, textures):
    colors = {}
    for material_index, material in enumerate(materials):
        pbr = material.get("pbrMetallicRoughness", {})
        base_color_texture = pbr.get("baseColorTexture")
        fallback = np.array([148.0, 148.0, 148.0], dtype=np.float64)
        if "Glass" in material["name"]:
            fallback = np.array([112.0, 186.0, 207.0], dtype=np.float64)
        elif "Emissive" in material["name"]:
            fallback = np.array([255.0, 132.0, 54.0], dtype=np.float64)

        if base_color_texture is None:
            factor = np.asarray(pbr.get("baseColorFactor", [0.58, 0.58, 0.58, 1.0])[:3], dtype=np.float64)
            colors[material_index] = np.clip(factor * 255.0, 0.0, 255.0)
            continue

        texture = textures[base_color_texture["index"]]
        image = images[texture["source"]]
        colors[material_index] = average_texture_color(output_dir / image["uri"], fallback)

    triangles = []
    for part in preview_parts:
        positions = np.asarray(part["positions"], dtype=np.float64)
        indices = np.asarray(part["indices"], dtype=np.int32).reshape(-1, 3)
        color = colors.get(part["material_index"], np.array([148.0, 148.0, 148.0], dtype=np.float64))
        for tri in indices:
            triangles.append((positions[tri], color))

    all_points = np.concatenate([tri[0] for tri in triangles], axis=0)
    center = (all_points.min(axis=0) + all_points.max(axis=0)) * 0.5

    def rotation_matrix(yaw_deg, pitch_deg):
        yaw = math.radians(yaw_deg)
        pitch = math.radians(pitch_deg)
        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        rotate_y = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]], dtype=np.float64)
        rotate_x = np.array([[1.0, 0.0, 0.0], [0.0, cp, -sp], [0.0, sp, cp]], dtype=np.float64)
        return rotate_x @ rotate_y

    views = [("Side", 90.0, -8.0), ("3/4", 56.0, -16.0)]
    width = 520
    height = 320
    image = Image.new("RGB", (width * len(views), height), (238, 232, 224))
    light = np.array([0.55, -0.65, 0.52], dtype=np.float64)
    light /= np.linalg.norm(light)

    for view_index, (label, yaw, pitch) in enumerate(views):
        draw = ImageDraw.Draw(image)
        left = view_index * width
        draw.rounded_rectangle([left + 8, 8, left + width - 8, height - 8], radius=18, fill=(247, 243, 236), outline=(192, 180, 165), width=2)

        transform = rotation_matrix(yaw, pitch)
        transformed_triangles = []
        projected = []
        for points, color in triangles:
            rotated = (points - center) @ transform.T
            transformed_triangles.append((rotated, color))
            projected.append(rotated[:, :2])

        projected = np.concatenate(projected, axis=0)
        minimum = projected.min(axis=0)
        maximum = projected.max(axis=0)
        span = max(maximum[0] - minimum[0], maximum[1] - minimum[1])
        scale = (min(width, height) - 74) / span

        draw_items = []
        for points, color in transformed_triangles:
            normal = np.cross(points[1] - points[0], points[2] - points[0])
            normal = normal / (np.linalg.norm(normal) or 1.0)
            shade = max(0.22, float(normal @ light))
            shaded = np.clip(color * (0.54 + 0.58 * shade), 0.0, 255.0).astype(int)
            polygon = []
            for x, y, z in points:
                sx = (x - (minimum[0] + maximum[0]) * 0.5) * scale + width * 0.5 + left
                sy = height * 0.56 - (y - (minimum[1] + maximum[1]) * 0.5) * scale
                polygon.append((sx, sy))
            draw_items.append((points[:, 2].mean(), tuple(shaded.tolist()), polygon))

        draw_items.sort(key=lambda item: item[0])
        for _, fill, polygon in draw_items:
            draw.polygon(polygon, fill=fill)

        draw.text((left + 16, 14), label, fill=(90, 73, 57))
        draw.text((left + 16, 34), "Weapon03 / Red Dragon Tech Sniper", fill=(126, 103, 82))

    image.save(output_dir / "weapon03_preview.png")


def write_meta(output_dir):
    meta = {
        "name": "Red Dragon Tech Sniper",
        "asset_name": "枪03",
        "category": "sniper_rifle",
        "style": "web_ready_futuristic_red_dragon_sniper",
        "formats": ["gltf", "glb"],
        "animations": ["idle", "fire", "reload", "ads", "sprint"],
        "detail_strategy": "preserve_original_meshes_and_textures",
        "weapon_traits": {
            "damage_profile": "very_high_per_shot",
            "range_profile": "long_range_precision",
            "handling": "heavy_scope_weight_deliberate_reload",
            "best_for": ["precision_shots", "anchoring_lanes", "high_feedback_single_fire"],
        },
    }
    (output_dir / "weapon03_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def write_readme(output_dir):
    readme = """# 枪03 - Red Dragon Tech Sniper Animated

## 1. 资源说明

这是一个面向网页 FPS 使用的 `Red Dragon Tech Sniper` 第一人称武器模型资源。

- 保留了原始 `枪03` 模型的网格、贴图和主要细节
- 对原始导出结构做了规范化整理
- 增加了适合网页项目使用的基础动作：
  - `idle`
  - `fire`
  - `reload`
  - `ads`
  - `sprint`

## 2. 动作说明

- `idle`：待机呼吸晃动
- `fire`：整枪后坐与镜身抬升
- `reload`：枪身倾斜并带独立弹匣抽离与回装
- `ads`：推进到瞄准姿态
- `sprint`：奔跑压枪姿态

## 3. 结构说明

- 重新建立了 `WeaponPose / ReceiverGroup / MagazineGroup` 层级
- 清理了源文件中的场景位移
- 烘焙了源文件的朝向修正
- 保留了原始材质贴图，并补充了玻璃透明和橙色发光材质设置
- 源模型没有独立枪机网格，所以本版本没有单独的枪机后拉动画

## 4. 使用建议

- 网页项目优先使用 `model.glb`
- `idle` 和 `sprint` 建议循环播放
- `fire`、`reload`、`ads` 建议单次播放
- 如果你后续需要更强的第一人称表现，可以继续在此基础上拆出枪机或拉机柄节点

## 5. 文件

- `model.gltf`
- `model.glb`
- `buffer.bin`
- `viewer.html`
- `viewer-data.js`
- `weapon03_preview.png`
- `weapon03_meta.json`
- `generate_weapon03_animated.py`

## 6. 贴图引用

- 脚本会复制源 PNG 到当前目录
- `model.gltf` 会引用当前目录中的贴图
- `model.glb` 仍会把贴图打包进单文件里

## 7. 重新生成

```bash
python3 generate_weapon03_animated.py
```

## 8. 本地查看

- 直接双击 `viewer.html`
- 查看器会读取同目录下自动生成的 `viewer-data.js`
- 不需要本地起服务
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def ensure_viewer_runtime_assets(output_dir):
    for relative_path, url in VIEWER_RUNTIME_FILES.items():
        target_path = output_dir / relative_path
        if target_path.exists() and target_path.stat().st_size > 0:
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(url) as response:
            target_path.write_bytes(response.read())


def copy_textures(source, output_dir):
    for image in source.get("images", []):
        uri = image.get("uri")
        if not uri or uri.startswith("data:"):
            continue
        source_path = SOURCE_DIR / uri
        target_path = output_dir / Path(uri).name
        if source_path.resolve() == target_path.resolve():
            continue
        shutil.copy2(source_path, target_path)


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
        "title": "Weapon03 / Red Dragon Tech Sniper",
        "subtitle": "Local GLB viewer with structure, materials, and animation controls",
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


def write_viewer_data(output_dir, manifest):
    glb_data = (output_dir / "model.glb").read_bytes()
    payload = {
        "manifest": manifest,
        "modelBase64": base64.b64encode(glb_data).decode("ascii"),
    }
    viewer_data = "window.WEAPON_VIEWER_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (output_dir / "viewer-data.js").write_text(viewer_data, encoding="utf-8")


def write_glb(output_dir, gltf, buffer_data):
    glb_dict = copy.deepcopy(gltf)
    binary_blob = bytearray(buffer_data)

    for image in glb_dict.get("images", []):
        uri = image.pop("uri", None)
        if uri is None:
            continue
        image_path = output_dir / uri
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
    model.save_binary(str(output_dir / "model.glb"))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    packaged_mode = SOURCE_DIR.resolve() == OUTPUT_DIR.resolve() and SOURCE_GLTF.name == "model.gltf"
    if packaged_mode:
        gltf_path = OUTPUT_DIR / "model.gltf"
        gltf = json.loads(gltf_path.read_text(encoding="utf-8"))
        glb_path = OUTPUT_DIR / "model.glb"
        if not glb_path.exists():
            write_glb(OUTPUT_DIR, gltf, (OUTPUT_DIR / "buffer.bin").read_bytes())
        ensure_viewer_runtime_assets(OUTPUT_DIR)
        write_viewer_data(OUTPUT_DIR, build_viewer_manifest(gltf))
        write_meta(OUTPUT_DIR)
        write_readme(OUTPUT_DIR)
        print(gltf_path)
        print(glb_path)
        print(OUTPUT_DIR / "viewer.html")
        print(OUTPUT_DIR / "weapon03_preview.png")
        return

    gltf, buffer_data, preview_parts, materials, images = build_gltf()
    source, _ = load_source()
    copy_textures(source, OUTPUT_DIR)

    buffer_path = OUTPUT_DIR / "buffer.bin"
    buffer_path.write_bytes(buffer_data)

    gltf_path = OUTPUT_DIR / "model.gltf"
    gltf_path.write_text(json.dumps(gltf, ensure_ascii=False, indent=2), encoding="utf-8")

    glb_path = OUTPUT_DIR / "model.glb"
    try:
        write_glb(OUTPUT_DIR, gltf, buffer_data)
    except Exception as exc:
        glb_path.write_text(f"GLB export failed.\nReason: {exc}\nUse model.gltf instead.\n", encoding="utf-8")

    ensure_viewer_runtime_assets(OUTPUT_DIR)
    write_viewer_data(OUTPUT_DIR, build_viewer_manifest(gltf))
    render_preview(OUTPUT_DIR, preview_parts, materials, images, gltf["textures"])
    write_meta(OUTPUT_DIR)
    write_readme(OUTPUT_DIR)

    print(gltf_path)
    print(glb_path)
    print(OUTPUT_DIR / "viewer.html")
    print(OUTPUT_DIR / "weapon03_preview.png")


if __name__ == "__main__":
    main()
