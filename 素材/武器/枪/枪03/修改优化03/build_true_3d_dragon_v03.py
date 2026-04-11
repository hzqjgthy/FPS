#!/usr/bin/env python3

import base64
import copy
import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from pygltflib import GLTF2


ROOT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = ROOT_DIR.parent / "枪的模型"
OUTPUT_DIR = ROOT_DIR

BASE_FILES = [
    "model.gltf",
    "buffer.bin",
    "glass.png",
    "EM_Orange.png",
    "T_XCR_Iron_Rouge_scope02_B.png",
    "T_XCR_Iron_Rouge_magazine_B.png",
    "T_XCR_Iron_Rouge_body_B.png",
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

FLOAT = 5126
UNSIGNED_SHORT = 5123
ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963


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
    (OUTPUT_DIR / "model.gltf").write_text(json.dumps(gltf, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize(v):
    v = np.asarray(v, dtype=np.float64)
    norm = np.linalg.norm(v)
    if norm == 0.0:
        return v
    return v / norm


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
    axis = normalize(axis)
    half = math.radians(angle_deg) * 0.5
    s = math.sin(half)
    c = math.cos(half)
    return np.array([axis[0] * s, axis[1] * s, axis[2] * s, c], dtype=np.float64)


def quat_from_euler_xyz(x_deg, y_deg, z_deg):
    qx = quat_from_axis_angle((1.0, 0.0, 0.0), x_deg)
    qy = quat_from_axis_angle((0.0, 1.0, 0.0), y_deg)
    qz = quat_from_axis_angle((0.0, 0.0, 1.0), z_deg)
    return normalize(quat_mul(quat_mul(qz, qy), qx))


def rotate_vectors(quat, vectors):
    quat = normalize(quat)
    x, y, z, w = quat
    matrix = np.array(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )
    return np.asarray(vectors, dtype=np.float64) @ matrix.T


def geometry_dict(positions, normals, indices):
    return {
        "positions": np.asarray(positions, dtype=np.float32),
        "normals": np.asarray(normals, dtype=np.float32),
        "indices": np.asarray(indices, dtype=np.uint16),
    }


def merge_geometries(geometries):
    positions = []
    normals = []
    indices = []
    offset = 0
    for geo in geometries:
        positions.append(geo["positions"])
        normals.append(geo["normals"])
        indices.append(geo["indices"] + offset)
        offset += len(geo["positions"])
    return geometry_dict(np.concatenate(positions), np.concatenate(normals), np.concatenate(indices))


def transform_geometry(geo, translation=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0, 1.0), scale=(1.0, 1.0, 1.0)):
    translation = np.asarray(translation, dtype=np.float64)
    rotation = np.asarray(rotation, dtype=np.float64)
    scale = np.asarray(scale, dtype=np.float64)
    positions = rotate_vectors(rotation, geo["positions"] * scale) + translation
    normal_scale = np.where(scale == 0.0, 1.0, scale)
    normals = rotate_vectors(rotation, geo["normals"] / normal_scale)
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = normals / np.where(norms == 0.0, 1.0, norms)
    return geometry_dict(positions, normals, geo["indices"])


def make_box(size=(1.0, 1.0, 1.0)):
    sx, sy, sz = size
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    faces = [
        ((-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz), (0.0, 0.0, 1.0)),
        ((hx, -hy, -hz), (-hx, -hy, -hz), (-hx, hy, -hz), (hx, hy, -hz), (0.0, 0.0, -1.0)),
        ((-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz), (-hx, hy, -hz), (-1.0, 0.0, 0.0)),
        ((hx, -hy, hz), (hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz), (1.0, 0.0, 0.0)),
        ((-hx, hy, hz), (hx, hy, hz), (hx, hy, -hz), (-hx, hy, -hz), (0.0, 1.0, 0.0)),
        ((-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz), (0.0, -1.0, 0.0)),
    ]
    positions = []
    normals = []
    indices = []
    for a, b, c, d, normal in faces:
        start = len(positions)
        positions.extend([a, b, c, d])
        normals.extend([normal, normal, normal, normal])
        indices.extend([start, start + 1, start + 2, start, start + 2, start + 3])
    return geometry_dict(positions, normals, indices)


def make_pyramid(base=(1.0, 1.0), height=1.0, axis="+y"):
    bx, bz = base
    hx = bx * 0.5
    hz = bz * 0.5
    base_points = [
        np.array([-hx, 0.0, -hz], dtype=np.float64),
        np.array([hx, 0.0, -hz], dtype=np.float64),
        np.array([hx, 0.0, hz], dtype=np.float64),
        np.array([-hx, 0.0, hz], dtype=np.float64),
    ]
    tip = np.array([0.0, height, 0.0], dtype=np.float64)

    positions = []
    normals = []
    indices = []

    def add_triangle(a, b, c):
        start = len(positions)
        normal = normalize(np.cross(b - a, c - a))
        positions.extend([tuple(a), tuple(b), tuple(c)])
        normals.extend([tuple(normal)] * 3)
        indices.extend([start, start + 1, start + 2])

    def add_quad(a, b, c, d):
        start = len(positions)
        normal = normalize(np.cross(b - a, c - a))
        positions.extend([tuple(a), tuple(b), tuple(c), tuple(d)])
        normals.extend([tuple(normal)] * 4)
        indices.extend([start, start + 1, start + 2, start, start + 2, start + 3])

    for index in range(4):
        a = base_points[index]
        b = base_points[(index + 1) % 4]
        add_triangle(a, b, tip)

    add_quad(base_points[3], base_points[2], base_points[1], base_points[0])
    geo = geometry_dict(positions, normals, indices)

    rotations = {
        "+y": quat_from_euler_xyz(0.0, 0.0, 0.0),
        "-y": quat_from_euler_xyz(180.0, 0.0, 0.0),
        "+x": quat_from_euler_xyz(0.0, 0.0, -90.0),
        "-x": quat_from_euler_xyz(0.0, 0.0, 90.0),
        "+z": quat_from_euler_xyz(90.0, 0.0, 0.0),
        "-z": quat_from_euler_xyz(-90.0, 0.0, 0.0),
    }
    return transform_geometry(geo, rotation=rotations[axis])


def make_wedge(length=1.0, width=1.0, height=1.0):
    l0 = -length * 0.5
    l1 = length * 0.5
    w = width * 0.5
    top = height * 0.5
    bottom = -height * 0.5

    front_top = np.array([0.0, top, l1], dtype=np.float64)
    front_left = np.array([-w, bottom, l1], dtype=np.float64)
    front_right = np.array([w, bottom, l1], dtype=np.float64)
    back_top = np.array([0.0, top, l0], dtype=np.float64)
    back_left = np.array([-w, bottom, l0], dtype=np.float64)
    back_right = np.array([w, bottom, l0], dtype=np.float64)

    positions = []
    normals = []
    indices = []

    def add_triangle(a, b, c):
        start = len(positions)
        normal = normalize(np.cross(b - a, c - a))
        positions.extend([tuple(a), tuple(b), tuple(c)])
        normals.extend([tuple(normal)] * 3)
        indices.extend([start, start + 1, start + 2])

    def add_quad(a, b, c, d):
        start = len(positions)
        normal = normalize(np.cross(b - a, c - a))
        positions.extend([tuple(a), tuple(b), tuple(c), tuple(d)])
        normals.extend([tuple(normal)] * 4)
        indices.extend([start, start + 1, start + 2, start, start + 2, start + 3])

    add_quad(back_left, back_right, front_right, front_left)
    add_quad(back_top, back_left, front_left, front_top)
    add_quad(back_right, back_top, front_top, front_right)
    add_triangle(front_left, front_right, front_top)
    add_triangle(back_right, back_left, back_top)
    return geometry_dict(positions, normals, indices)


def build_dragon_armor_geometries():
    bronze_parts = []
    obsidian_parts = []

    # Top dragon spine fins along the receiver top.
    spine_positions = [-0.16, -0.105, -0.05, 0.01, 0.07, 0.135, 0.20]
    spine_sizes = [0.020, 0.022, 0.024, 0.027, 0.030, 0.032, 0.035]
    for z, size in zip(spine_positions, spine_sizes):
        fin = make_pyramid(base=(size * 0.75, size * 1.7), height=size * 0.72, axis="+y")
        fin = transform_geometry(
            fin,
            translation=(0.0, 0.040, z),
            rotation=quat_from_euler_xyz(-10.0, 0.0, 0.0),
        )
        bronze_parts.append(fin)

    # Left and right dragon scale armor plates.
    scale_positions = [-0.14, -0.085, -0.03, 0.035, 0.105, 0.175]
    y_positions = [0.008, 0.006, 0.004, 0.002, -0.002, -0.004]
    for side in (-1.0, 1.0):
        axis = "-x" if side < 0 else "+x"
        for index, (z, y) in enumerate(zip(scale_positions, y_positions)):
            base_w = 0.018 + index * 0.002
            base_h = 0.038 + index * 0.004
            protrusion = 0.006 + index * 0.0007
            scale = make_pyramid(base=(base_h, base_w), height=protrusion, axis=axis)
            scale = transform_geometry(
                scale,
                translation=(side * 0.0135, y, z),
                rotation=quat_from_euler_xyz(-6.0, side * -8.0, side * (7.0 + index * 1.2)),
            )
            bronze_parts.append(scale)

    # Lower rib armor braces.
    rib_positions = [-0.115, -0.03, 0.055, 0.14]
    for side in (-1.0, 1.0):
        for z in rib_positions:
            rib = make_wedge(length=0.034, width=0.014, height=0.010)
            rib = transform_geometry(
                rib,
                translation=(side * 0.015, -0.018, z),
                rotation=quat_from_euler_xyz(90.0, 0.0, side * 90.0),
            )
            bronze_parts.append(rib)

    # Front dragon head / snout armor.
    snout = make_wedge(length=0.070, width=0.020, height=0.018)
    snout = transform_geometry(
        snout,
        translation=(0.0, 0.020, 0.235),
        rotation=quat_from_euler_xyz(-4.0, 0.0, 0.0),
    )
    bronze_parts.append(snout)

    brow_left = transform_geometry(make_box((0.010, 0.008, 0.028)), translation=(-0.010, 0.025, 0.208), rotation=quat_from_euler_xyz(8.0, 0.0, 12.0))
    brow_right = transform_geometry(make_box((0.010, 0.008, 0.028)), translation=(0.010, 0.025, 0.208), rotation=quat_from_euler_xyz(8.0, 0.0, -12.0))
    bronze_parts.extend([brow_left, brow_right])

    jaw = make_wedge(length=0.060, width=0.022, height=0.012)
    jaw = transform_geometry(jaw, translation=(0.0, 0.002, 0.224), rotation=quat_from_euler_xyz(176.0, 0.0, 0.0))
    obsidian_parts.append(jaw)

    horn_left = make_pyramid(base=(0.010, 0.018), height=0.022, axis="+z")
    horn_left = transform_geometry(horn_left, translation=(-0.015, 0.032, 0.198), rotation=quat_from_euler_xyz(-20.0, -24.0, 18.0))
    horn_right = make_pyramid(base=(0.010, 0.018), height=0.022, axis="+z")
    horn_right = transform_geometry(horn_right, translation=(0.015, 0.032, 0.198), rotation=quat_from_euler_xyz(-20.0, 24.0, -18.0))
    obsidian_parts.extend([horn_left, horn_right])

    cheek_left = transform_geometry(make_box((0.008, 0.010, 0.022)), translation=(-0.015, 0.011, 0.205), rotation=quat_from_euler_xyz(0.0, 0.0, 22.0))
    cheek_right = transform_geometry(make_box((0.008, 0.010, 0.022)), translation=(0.015, 0.011, 0.205), rotation=quat_from_euler_xyz(0.0, 0.0, -22.0))
    obsidian_parts.extend([cheek_left, cheek_right])

    return merge_geometries(bronze_parts), merge_geometries(obsidian_parts)


class BufferAppender:
    def __init__(self, gltf, initial_data):
        self.gltf = gltf
        self.data = bytearray(initial_data)
        self.buffer_views = gltf.setdefault("bufferViews", [])
        self.accessors = gltf.setdefault("accessors", [])

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
            raise ValueError(component_type)

        view_index = self.add_blob(arr.tobytes(), target=target)
        accessor = {
            "bufferView": view_index,
            "componentType": component_type,
            "count": int(arr.shape[0]),
            "type": accessor_type,
        }
        if accessor_type == "SCALAR":
            accessor["min"] = [int(arr.min())]
            accessor["max"] = [int(arr.max())]
        else:
            flat = arr.reshape(arr.shape[0], {"VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor_type])
            accessor["min"] = [float(v) for v in flat.min(axis=0)]
            accessor["max"] = [float(v) for v in flat.max(axis=0)]
        self.accessors.append(accessor)
        return len(self.accessors) - 1


def append_materials_and_geometry(gltf, buffer_data):
    builder = BufferAppender(gltf, buffer_data)
    bronze_geo, obsidian_geo = build_dragon_armor_geometries()

    materials = gltf.setdefault("materials", [])
    bronze_material_index = len(materials)
    materials.append(
        {
            "name": "DragonArmorBronze",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.76, 0.55, 0.20, 1.0],
                "metallicFactor": 0.88,
                "roughnessFactor": 0.30,
            },
        }
    )

    obsidian_material_index = len(materials)
    materials.append(
        {
            "name": "DragonArmorObsidian",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.18, 0.07, 0.05, 1.0],
                "metallicFactor": 0.62,
                "roughnessFactor": 0.44,
            },
        }
    )

    def add_mesh(name, geo, material_index):
        pos_accessor = builder.add_accessor(geo["positions"], FLOAT, "VEC3", target=ARRAY_BUFFER)
        normal_accessor = builder.add_accessor(geo["normals"], FLOAT, "VEC3", target=ARRAY_BUFFER)
        index_accessor = builder.add_accessor(geo["indices"], UNSIGNED_SHORT, "SCALAR", target=ELEMENT_ARRAY_BUFFER)
        mesh_index = len(gltf.setdefault("meshes", []))
        gltf["meshes"].append(
            {
                "name": name,
                "primitives": [
                    {
                        "attributes": {
                            "POSITION": pos_accessor,
                            "NORMAL": normal_accessor,
                        },
                        "indices": index_accessor,
                        "material": material_index,
                    }
                ],
            }
        )
        return mesh_index

    bronze_mesh_index = add_mesh("dragon_bronze_armor", bronze_geo, bronze_material_index)
    obsidian_mesh_index = add_mesh("dragon_obsidian_armor", obsidian_geo, obsidian_material_index)

    nodes = gltf.setdefault("nodes", [])
    bronze_node_index = len(nodes)
    nodes.append({"name": "dragon_bronze_armor_node", "mesh": bronze_mesh_index})
    obsidian_node_index = len(nodes)
    nodes.append({"name": "dragon_obsidian_armor_node", "mesh": obsidian_mesh_index})

    receiver_group = next(node for node in nodes if node.get("name") == "ReceiverGroup")
    receiver_group.setdefault("children", []).extend([bronze_node_index, obsidian_node_index])

    gltf.setdefault("extras", {})["variant"] = {
        "name": "true_3d_dragon_v03",
        "description": "Added protruding dragon scales and dragon-bone armor geometry to the receiver group.",
    }

    gltf.setdefault("buffers", [{}])[0]["byteLength"] = len(builder.data)
    return bytes(builder.data)


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
        "title": "Weapon03 / True 3D Dragon V03",
        "subtitle": "Receiver body upgraded with protruding dragon scales and dragon-bone armor geometry",
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


def render_preview(gltf):
    materials = gltf.get("materials", [])
    colors = {}
    for index, material in enumerate(materials):
        pbr = material.get("pbrMetallicRoughness", {})
        factor = pbr.get("baseColorFactor")
        if factor:
            colors[index] = np.array(factor[:3], dtype=np.float64) * 255.0
        else:
            colors[index] = np.array([155.0, 145.0, 132.0], dtype=np.float64)

    buffer = (OUTPUT_DIR / "buffer.bin").read_bytes()

    def read_accessor(idx):
        accessor = gltf["accessors"][idx]
        view = gltf["bufferViews"][accessor["bufferView"]]
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        component_count = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
        dtype = np.dtype("<f4") if accessor["componentType"] == FLOAT else np.dtype("<u2")
        raw = buffer[offset : offset + accessor["count"] * component_count * dtype.itemsize]
        arr = np.frombuffer(raw, dtype=dtype)
        if component_count == 1:
            return arr.copy()
        return arr.reshape(accessor["count"], component_count).copy()

    triangles = []
    for mesh in gltf["meshes"]:
        prim = mesh["primitives"][0]
        positions = read_accessor(prim["attributes"]["POSITION"]).astype(np.float64)
        indices = read_accessor(prim["indices"]).astype(np.int32).reshape(-1, 3)
        color = colors.get(prim["material"], np.array([155.0, 145.0, 132.0], dtype=np.float64))
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

    views = [("Side", 92.0, -8.0), ("3/4", 52.0, -16.0)]
    width = 560
    height = 340
    image = Image.new("RGB", (width * len(views), height), (239, 232, 222))
    light = normalize(np.array([0.5, -0.62, 0.58], dtype=np.float64))

    for view_index, (label, yaw, pitch) in enumerate(views):
        draw = ImageDraw.Draw(image)
        left = view_index * width
        draw.rounded_rectangle([left + 10, 10, left + width - 10, height - 10], radius=18, fill=(250, 246, 240), outline=(196, 179, 158), width=2)

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
        scale = (min(width, height) - 86) / span

        draw_items = []
        for points, color in transformed_triangles:
            normal = normalize(np.cross(points[1] - points[0], points[2] - points[0]))
            shade = max(0.18, float(np.dot(normal, light)))
            shaded = np.clip(color * (0.52 + 0.62 * shade), 0.0, 255.0).astype(int)
            polygon = []
            for x, y, z in points:
                sx = (x - (minimum[0] + maximum[0]) * 0.5) * scale + width * 0.5 + left
                sy = height * 0.57 - (y - (minimum[1] + maximum[1]) * 0.5) * scale
                polygon.append((sx, sy))
            draw_items.append((points[:, 2].mean(), tuple(shaded.tolist()), polygon))

        draw_items.sort(key=lambda item: item[0])
        for _, fill, polygon in draw_items:
            draw.polygon(polygon, fill=fill)

        draw.text((left + 18, 16), label, fill=(86, 67, 51))
        draw.text((left + 18, 36), "True 3D Dragon Armor V03", fill=(130, 95, 60))

    image.save(OUTPUT_DIR / "dragon_3d_armor_preview.png")


def update_meta():
    meta_path = OUTPUT_DIR / "weapon03_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["variant"] = "modification_optimization_03_true_3d_dragon_armor"
    meta["detail_strategy"] = "add_protruding_dragon_scale_and_dragon_bone_geometry_to_receiver_group"
    meta["modifications"] = {
        "target_component": "ReceiverGroup",
        "variant_goal": "true_3d_dragon_armor",
        "added_geometry_components": [
            "dragon_bronze_armor_node",
            "dragon_obsidian_armor_node",
        ],
        "added_materials": [
            "DragonArmorBronze",
            "DragonArmorObsidian",
        ],
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def write_readme():
    readme = """# 修改优化03 - 真正凸起的立体龙纹

## 1. 版本目标

本版本基于原版 `武器/枪/枪03/枪的模型` 生成，不改原目录。

- 在 `ReceiverGroup` 下新增真实几何体
- 让枪体表面长出龙鳞、龙骨装甲、龙首前额结构
- 保留原来的枪体、动画、贴图和查看器

## 2. 主要文件

- `model.gltf`
- `model.glb`
- `dragon_3d_armor_preview.png`
- `build_true_3d_dragon_v03.py`
- `真正凸起立体龙纹_实现过程.md`
- `viewer.html`
- `viewer-data.js`

## 3. 重新生成

```bash
python3 build_true_3d_dragon_v03.py
```

## 4. 查看

- 直接双击 `viewer.html`
- 或导入 `model.glb` 到 Blender / Babylon / glTF 查看器
"""
    (OUTPUT_DIR / "README.md").write_text(readme, encoding="utf-8")


def main():
    copy_base_assets()
    gltf = load_gltf()
    buffer_data = (OUTPUT_DIR / "buffer.bin").read_bytes()
    updated_buffer = append_materials_and_geometry(gltf, buffer_data)
    save_gltf(gltf)
    (OUTPUT_DIR / "buffer.bin").write_bytes(updated_buffer)
    update_meta()
    write_readme()
    write_glb(gltf, updated_buffer)
    write_viewer_data(gltf)
    render_preview(gltf)

    print(OUTPUT_DIR / "model.gltf")
    print(OUTPUT_DIR / "model.glb")
    print(OUTPUT_DIR / "dragon_3d_armor_preview.png")
    print(OUTPUT_DIR / "viewer.html")


if __name__ == "__main__":
    main()
