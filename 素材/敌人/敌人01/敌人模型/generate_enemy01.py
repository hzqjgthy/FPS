#!/usr/bin/env python3

from __future__ import annotations

import base64
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from pygltflib import GLTF2


OUTPUT_DIR = Path(__file__).resolve().parent

FLOAT = 5126
UNSIGNED_SHORT = 5123
ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963


def normalize_quat(q):
    q = np.asarray(q, dtype=np.float64)
    norm = np.linalg.norm(q)
    if norm == 0:
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


def rotate_vector(q, v):
    q = normalize_quat(q)
    vq = np.array([v[0], v[1], v[2], 0.0], dtype=np.float64)
    qi = np.array([-q[0], -q[1], -q[2], q[3]], dtype=np.float64)
    return quat_mul(quat_mul(q, vq), qi)[:3]


def geometry_dict(positions, normals, indices):
    return {
        "positions": np.asarray(positions, dtype=np.float32),
        "normals": np.asarray(normals, dtype=np.float32),
        "indices": np.asarray(indices, dtype=np.uint16),
    }


def transform_geometry(
    geo,
    translation=(0.0, 0.0, 0.0),
    rotation=(0.0, 0.0, 0.0, 1.0),
    scale=(1.0, 1.0, 1.0),
):
    translation = np.asarray(translation, dtype=np.float64)
    rotation = normalize_quat(rotation)
    scale = np.asarray(scale, dtype=np.float64)

    positions = []
    normals = []
    for pos, normal in zip(geo["positions"], geo["normals"]):
        p = rotate_vector(rotation, np.asarray(pos, dtype=np.float64) * scale) + translation
        n = rotate_vector(rotation, np.asarray(normal, dtype=np.float64) / np.where(scale == 0.0, 1.0, scale))
        n = n / (np.linalg.norm(n) or 1.0)
        positions.append(p)
        normals.append(n)

    return geometry_dict(np.asarray(positions), np.asarray(normals), geo["indices"])


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


def prepare_textures(output_dir):
    bark_path = output_dir / "enemy01_bark.png"
    moss_path = output_dir / "enemy01_moss.png"

    bark = Image.new("RGBA", (512, 512), (96, 72, 48, 255))
    draw = ImageDraw.Draw(bark)
    for y in range(0, 512, 8):
        shade = 42 + (y % 36)
        draw.line([(0, y), (511, y + 6)], fill=(shade + 34, shade + 18, shade, 255), width=3)
    for x in range(0, 512, 30):
        draw.line([(x, 0), (x + 18, 511)], fill=(34, 22, 16, 220), width=4)
    bark = bark.filter(ImageFilter.GaussianBlur(0.7))
    bark.save(bark_path)

    moss = bark.copy()
    arr = np.array(moss, dtype=np.uint8)
    arr[..., 0] = (arr[..., 0] * 0.55).astype(np.uint8)
    arr[..., 1] = np.clip(arr[..., 1] * 1.1 + 26, 0, 255).astype(np.uint8)
    arr[..., 2] = (arr[..., 2] * 0.48).astype(np.uint8)
    moss = Image.fromarray(arr, "RGBA").filter(ImageFilter.GaussianBlur(0.8))
    ImageDraw.Draw(moss).ellipse((90, 90, 240, 240), fill=(88, 138, 62, 88))
    ImageDraw.Draw(moss).ellipse((260, 200, 420, 360), fill=(72, 120, 50, 92))
    moss.save(moss_path)


def build_mesh_library():
    box = make_box()
    return {
        "torso": transform_geometry(box, translation=(0.0, 0.0, 0.0), scale=(0.88, 1.0, 0.46)),
        "chest": transform_geometry(box, translation=(0.0, 0.1, 0.27), scale=(0.94, 0.16, 0.18)),
        "hips": transform_geometry(box, translation=(0.0, 0.0, 0.0), scale=(0.78, 0.32, 0.34)),
        "head": transform_geometry(box, translation=(0.0, 0.02, 0.0), scale=(0.42, 0.42, 0.42)),
        "scarf": transform_geometry(box, translation=(0.0, -0.22, 0.0), scale=(0.5, 0.16, 0.5)),
        "eyeband": transform_geometry(box, translation=(0.0, 0.04, 0.06), scale=(0.48, 0.08, 0.48)),
        "arm": transform_geometry(box, translation=(0.0, -0.46, 0.0), scale=(0.24, 0.92, 0.24)),
        "hand": transform_geometry(box, translation=(0.0, -0.98, 0.0), scale=(0.22, 0.28, 0.22)),
        "leg": transform_geometry(box, translation=(0.0, -0.56, 0.0), scale=(0.28, 1.08, 0.3)),
        "foot": transform_geometry(box, translation=(0.0, -1.16, 0.08), scale=(0.34, 0.18, 0.52)),
        "handle": transform_geometry(box, translation=(0.06, -1.08, 0.04), rotation=quat_from_euler_xyz(0.0, 0.0, -11.0), scale=(0.08, 0.26, 0.08)),
        "blade": transform_geometry(box, translation=(0.12, -1.38, 0.04), rotation=quat_from_euler_xyz(6.0, 0.0, -19.0), scale=(0.06, 0.56, 0.04)),
    }


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
            raise ValueError(component_type)
        view_index = self.add_blob(arr.tobytes(), target=target)
        accessor = {
            "bufferView": view_index,
            "componentType": component_type,
            "count": int(arr.shape[0]),
            "type": accessor_type,
        }
        if accessor_type != "SCALAR":
            accessor["min"] = [float(v) for v in arr.min(axis=0)]
            accessor["max"] = [float(v) for v in arr.max(axis=0)]
        else:
            accessor["min"] = [int(arr.min()) if component_type == UNSIGNED_SHORT else float(arr.min())]
            accessor["max"] = [int(arr.max()) if component_type == UNSIGNED_SHORT else float(arr.max())]
        self.accessors.append(accessor)
        return len(self.accessors) - 1


def build_structure(mesh_lookup):
    nodes = []
    node_lookup = {}

    def add_node(name, translation=None, rotation=None, mesh=None):
        node = {"name": name}
        if translation is not None:
            node["translation"] = list(translation)
        if rotation is not None:
            node["rotation"] = list(rotation)
        if mesh is not None:
            node["mesh"] = mesh
        node_lookup[name] = len(nodes)
        nodes.append(node)
        return node_lookup[name]

    def attach_mesh(parent_index, name, mesh_name):
        mesh_node = add_node(name, mesh=mesh_lookup[mesh_name])
        nodes[parent_index].setdefault("children", []).append(mesh_node)

    root = add_node("EnemyRoot")
    hips = add_node("Hips", translation=(0.0, 0.92, 0.0))
    nodes[root]["children"] = [hips]

    spine = add_node("Spine", translation=(0.0, 0.78, 0.0))
    head = add_node("Head", translation=(0.0, 0.92, 0.02))
    arm_l = add_node("Arm_L", translation=(-0.56, 0.68, 0.0))
    arm_r = add_node("Arm_R", translation=(0.56, 0.68, 0.0))
    leg_l = add_node("Leg_L", translation=(-0.22, -0.02, 0.0))
    leg_r = add_node("Leg_R", translation=(0.22, -0.02, 0.0))

    nodes[hips]["children"] = [spine, leg_l, leg_r]
    nodes[spine]["children"] = [head, arm_l, arm_r]

    attach_mesh(spine, "Torso_Geom", "torso")
    attach_mesh(spine, "Chest_Geom", "chest")
    attach_mesh(hips, "Hips_Geom", "hips")
    attach_mesh(head, "Head_Geom", "head")
    attach_mesh(head, "Scarf_Geom", "scarf")
    attach_mesh(head, "EyeBand_Geom", "eyeband")
    attach_mesh(arm_l, "ArmL_Geom", "arm")
    attach_mesh(arm_l, "HandL_Geom", "hand")
    attach_mesh(arm_r, "ArmR_Geom", "arm")
    attach_mesh(arm_r, "HandR_Geom", "hand")
    attach_mesh(arm_r, "Handle_Geom", "handle")
    attach_mesh(arm_r, "Blade_Geom", "blade")
    attach_mesh(leg_l, "LegL_Geom", "leg")
    attach_mesh(leg_l, "FootL_Geom", "foot")
    attach_mesh(leg_r, "LegR_Geom", "leg")
    attach_mesh(leg_r, "FootR_Geom", "foot")

    return nodes, node_lookup, root


def build_animations(node_lookup):
    base_translation = {
        "EnemyRoot": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "Hips": np.array([0.0, 0.92, 0.0], dtype=np.float64),
    }
    base_euler = {
        "EnemyRoot": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "Spine": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "Head": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "Arm_L": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "Arm_R": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "Leg_L": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "Leg_R": np.array([0.0, 0.0, 0.0], dtype=np.float64),
    }

    def rot_track(node_name, times, deltas):
        values = []
        for delta in deltas:
            euler = base_euler[node_name] + np.array(delta, dtype=np.float64)
            values.append(quat_from_euler_xyz(*euler))
        return {
            "node": node_lookup[node_name],
            "path": "rotation",
            "times": np.array(times, dtype=np.float32),
            "values": np.array(values, dtype=np.float32),
        }

    def trans_track(node_name, times, deltas):
        values = []
        for delta in deltas:
            values.append(base_translation[node_name] + np.array(delta, dtype=np.float64))
        return {
            "node": node_lookup[node_name],
            "path": "translation",
            "times": np.array(times, dtype=np.float32),
            "values": np.array(values, dtype=np.float32),
        }

    clips = []
    clips.append({"name": "Idle", "tracks": [
        trans_track("Hips", [0.0, 0.7, 1.4], [(0.0, 0.00, 0.0), (0.0, 0.04, 0.0), (0.0, 0.00, 0.0)]),
        rot_track("Spine", [0.0, 0.7, 1.4], [(0.0, -2.0, 0.0), (4.0, 2.0, 0.0), (0.0, -2.0, 0.0)]),
        rot_track("Head", [0.0, 0.7, 1.4], [(0.0, -4.0, 0.0), (0.0, 5.0, 0.0), (0.0, -4.0, 0.0)]),
        rot_track("Arm_L", [0.0, 0.7, 1.4], [(6.0, 0.0, -2.0), (0.0, 0.0, 2.0), (6.0, 0.0, -2.0)]),
        rot_track("Arm_R", [0.0, 0.7, 1.4], [(6.0, 0.0, 2.0), (0.0, 0.0, -2.0), (6.0, 0.0, 2.0)]),
    ]})
    clips.append({"name": "Walk", "tracks": [
        trans_track("Hips", [0.0, 0.25, 0.5, 0.75, 1.0], [(0.0, 0.00, 0.0), (0.0, -0.04, 0.0), (0.0, 0.01, 0.0), (0.0, -0.04, 0.0), (0.0, 0.00, 0.0)]),
        rot_track("Arm_L", [0.0, 0.25, 0.5, 0.75, 1.0], [(22.0, 0.0, -8.0), (-18.0, 0.0, 4.0), (22.0, 0.0, -8.0), (-18.0, 0.0, 4.0), (22.0, 0.0, -8.0)]),
        rot_track("Arm_R", [0.0, 0.25, 0.5, 0.75, 1.0], [(-18.0, 0.0, 4.0), (22.0, 0.0, -8.0), (-18.0, 0.0, 4.0), (22.0, 0.0, -8.0), (-18.0, 0.0, 4.0)]),
        rot_track("Leg_L", [0.0, 0.25, 0.5, 0.75, 1.0], [(-20.0, 0.0, 0.0), (18.0, 0.0, 0.0), (-20.0, 0.0, 0.0), (18.0, 0.0, 0.0), (-20.0, 0.0, 0.0)]),
        rot_track("Leg_R", [0.0, 0.25, 0.5, 0.75, 1.0], [(18.0, 0.0, 0.0), (-20.0, 0.0, 0.0), (18.0, 0.0, 0.0), (-20.0, 0.0, 0.0), (18.0, 0.0, 0.0)]),
    ]})
    clips.append({"name": "Run", "tracks": [
        trans_track("Hips", [0.0, 0.18, 0.36, 0.54, 0.72], [(0.0, -0.04, 0.0), (0.0, 0.02, 0.0), (0.0, -0.04, 0.0), (0.0, 0.02, 0.0), (0.0, -0.04, 0.0)]),
        rot_track("Spine", [0.0, 0.18, 0.36, 0.54, 0.72], [(10.0, 0.0, 5.0), (12.0, 0.0, -5.0), (10.0, 0.0, 5.0), (12.0, 0.0, -5.0), (10.0, 0.0, 5.0)]),
        rot_track("Arm_L", [0.0, 0.18, 0.36, 0.54, 0.72], [(38.0, 0.0, -10.0), (-34.0, 0.0, 8.0), (38.0, 0.0, -10.0), (-34.0, 0.0, 8.0), (38.0, 0.0, -10.0)]),
        rot_track("Arm_R", [0.0, 0.18, 0.36, 0.54, 0.72], [(-34.0, 0.0, 8.0), (38.0, 0.0, -10.0), (-34.0, 0.0, 8.0), (38.0, 0.0, -10.0), (-34.0, 0.0, 8.0)]),
        rot_track("Leg_L", [0.0, 0.18, 0.36, 0.54, 0.72], [(-32.0, 0.0, 0.0), (36.0, 0.0, 0.0), (-32.0, 0.0, 0.0), (36.0, 0.0, 0.0), (-32.0, 0.0, 0.0)]),
        rot_track("Leg_R", [0.0, 0.18, 0.36, 0.54, 0.72], [(36.0, 0.0, 0.0), (-32.0, 0.0, 0.0), (36.0, 0.0, 0.0), (-32.0, 0.0, 0.0), (36.0, 0.0, 0.0)]),
    ]})
    clips.append({"name": "Attack", "tracks": [
        rot_track("Spine", [0.0, 0.18, 0.42, 0.72, 0.96], [(0.0, 0.0, 0.0), (8.0, -20.0, 0.0), (-8.0, 30.0, -6.0), (-2.0, 8.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("Arm_R", [0.0, 0.18, 0.42, 0.72, 0.96], [(6.0, 0.0, 0.0), (-68.0, 0.0, 12.0), (98.0, 0.0, -18.0), (18.0, 0.0, 0.0), (6.0, 0.0, 0.0)]),
        rot_track("Arm_L", [0.0, 0.18, 0.42, 0.72, 0.96], [(0.0, 0.0, 0.0), (18.0, 0.0, 10.0), (-8.0, 0.0, -6.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
    ]})
    clips.append({"name": "Hit", "tracks": [
        trans_track("Hips", [0.0, 0.12, 0.3, 0.48], [(0.0, 0.0, 0.0), (0.0, 0.03, -0.04), (0.0, -0.02, 0.01), (0.0, 0.0, 0.0)]),
        rot_track("Spine", [0.0, 0.12, 0.3, 0.48], [(0.0, 0.0, 0.0), (-24.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("Head", [0.0, 0.12, 0.3, 0.48], [(0.0, 0.0, 0.0), (-18.0, 0.0, 0.0), (8.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("Arm_L", [0.0, 0.12, 0.3, 0.48], [(0.0, 0.0, 0.0), (18.0, 0.0, 10.0), (-4.0, 0.0, -2.0), (0.0, 0.0, 0.0)]),
        rot_track("Arm_R", [0.0, 0.12, 0.3, 0.48], [(0.0, 0.0, 0.0), (18.0, 0.0, -10.0), (-4.0, 0.0, 2.0), (0.0, 0.0, 0.0)]),
    ]})
    clips.append({"name": "Death", "tracks": [
        rot_track("EnemyRoot", [0.0, 0.32, 0.78, 1.18, 1.54], [(0.0, 0.0, 0.0), (0.0, 0.0, 12.0), (0.0, 0.0, 48.0), (0.0, 0.0, 90.0), (0.0, 0.0, 96.0)]),
        trans_track("Hips", [0.0, 0.32, 0.78, 1.18, 1.54], [(0.0, 0.0, 0.0), (0.0, -0.06, 0.0), (0.0, -0.28, 0.0), (0.0, -0.46, 0.0), (0.0, -0.48, 0.0)]),
        rot_track("Spine", [0.0, 0.32, 0.78, 1.18, 1.54], [(0.0, 0.0, 0.0), (12.0, -8.0, 0.0), (34.0, -10.0, -6.0), (76.0, 0.0, -14.0), (84.0, 0.0, -16.0)]),
        rot_track("Arm_L", [0.0, 0.32, 0.78, 1.18, 1.54], [(0.0, 0.0, 0.0), (24.0, 0.0, 18.0), (64.0, 0.0, 38.0), (102.0, 0.0, 28.0), (108.0, 0.0, 28.0)]),
        rot_track("Arm_R", [0.0, 0.32, 0.78, 1.18, 1.54], [(0.0, 0.0, 0.0), (18.0, 0.0, -18.0), (42.0, 0.0, -34.0), (84.0, 0.0, -24.0), (90.0, 0.0, -24.0)]),
        rot_track("Leg_L", [0.0, 0.32, 0.78, 1.18, 1.54], [(0.0, 0.0, 0.0), (-10.0, 0.0, 10.0), (14.0, 0.0, 24.0), (40.0, 0.0, 12.0), (40.0, 0.0, 12.0)]),
        rot_track("Leg_R", [0.0, 0.32, 0.78, 1.18, 1.54], [(0.0, 0.0, 0.0), (-12.0, 0.0, -10.0), (10.0, 0.0, -24.0), (34.0, 0.0, -12.0), (34.0, 0.0, -12.0)]),
    ]})
    return clips


def build_gltf():
    prepare_textures(OUTPUT_DIR)
    meshes_geo = build_mesh_library()
    builder = BufferBuilder()
    mesh_defs = []
    mesh_lookup = {}

    materials = [
        {"name": "Coat", "pbrMetallicRoughness": {"baseColorFactor": [0.27, 0.36, 0.22, 1.0], "metallicFactor": 0.04, "roughnessFactor": 0.92}},
        {"name": "Cloth", "pbrMetallicRoughness": {"baseColorFactor": [0.20, 0.22, 0.25, 1.0], "metallicFactor": 0.03, "roughnessFactor": 0.92}},
        {"name": "Skin", "pbrMetallicRoughness": {"baseColorFactor": [0.82, 0.63, 0.49, 1.0], "metallicFactor": 0.02, "roughnessFactor": 0.96}},
        {"name": "Bandana", "pbrMetallicRoughness": {"baseColorFactor": [0.50, 0.18, 0.10, 1.0], "metallicFactor": 0.06, "roughnessFactor": 0.84}},
        {"name": "Blade", "pbrMetallicRoughness": {"baseColorFactor": [0.76, 0.77, 0.78, 1.0], "metallicFactor": 0.9, "roughnessFactor": 0.26}},
        {"name": "Handle", "pbrMetallicRoughness": {"baseColorFactor": [0.27, 0.20, 0.13, 1.0], "metallicFactor": 0.12, "roughnessFactor": 0.82}},
    ]
    material_for_mesh = {
        "torso": 0,
        "chest": 1,
        "hips": 1,
        "head": 2,
        "scarf": 3,
        "eyeband": 3,
        "arm": 0,
        "hand": 2,
        "leg": 1,
        "foot": 1,
        "handle": 5,
        "blade": 4,
    }

    for name, geo in meshes_geo.items():
        pos = builder.add_accessor(geo["positions"], FLOAT, "VEC3", target=ARRAY_BUFFER)
        norm = builder.add_accessor(geo["normals"], FLOAT, "VEC3", target=ARRAY_BUFFER)
        idx = builder.add_accessor(geo["indices"], UNSIGNED_SHORT, "SCALAR", target=ELEMENT_ARRAY_BUFFER)
        mesh_lookup[name] = len(mesh_defs)
        mesh_defs.append({"name": name, "primitives": [{"attributes": {"POSITION": pos, "NORMAL": norm}, "indices": idx, "material": material_for_mesh[name]}]})

    nodes, node_lookup, root = build_structure(mesh_lookup)
    clips = build_animations(node_lookup)
    animations = []
    for clip in clips:
        samplers = []
        channels = []
        for track in clip["tracks"]:
            input_accessor = builder.add_accessor(track["times"], FLOAT, "SCALAR")
            output_accessor = builder.add_accessor(track["values"], FLOAT, "VEC4" if track["path"] == "rotation" else "VEC3")
            sampler_index = len(samplers)
            samplers.append({"input": input_accessor, "output": output_accessor, "interpolation": "LINEAR"})
            channels.append({"sampler": sampler_index, "target": {"node": track["node"], "path": track["path"]}})
        animations.append({"name": clip["name"], "samplers": samplers, "channels": channels})

    gltf = {
        "asset": {"version": "2.0", "generator": "Codex Raider Python Generator"},
        "scene": 0,
        "scenes": [{"name": "Enemy01Scene", "nodes": [root]}],
        "nodes": nodes,
        "meshes": mesh_defs,
        "materials": materials,
        "animations": animations,
        "bufferViews": builder.buffer_views,
        "accessors": builder.accessors,
        "buffers": [{"byteLength": len(builder.data), "uri": "data:application/octet-stream;base64," + base64.b64encode(builder.data).decode("ascii")}],
    }
    return gltf


def render_preview(output_dir):
    width = 900
    height = 420
    image = Image.new("RGB", (width, height), (242, 236, 226))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((10, 10, 440, 410), radius=26, fill=(248, 244, 238), outline=(196, 181, 156), width=3)
    draw.rounded_rectangle((460, 10, 890, 410), radius=26, fill=(248, 244, 238), outline=(196, 181, 156), width=3)
    draw.text((34, 28), "Front", fill=(86, 70, 54))
    draw.text((486, 28), "3/4", fill=(86, 70, 54))
    accent = (80, 98, 68)
    draw.rectangle((160, 80, 280, 300), fill=accent)
    draw.rectangle((195, 45, 245, 95), fill=(100, 118, 88))
    draw.rectangle((145, 130, 160, 245), fill=(58, 72, 52))
    draw.rectangle((280, 130, 295, 245), fill=(58, 72, 52))
    draw.rectangle((185, 300, 215, 380), fill=(66, 82, 58))
    draw.rectangle((225, 300, 255, 380), fill=(66, 82, 58))
    draw.rectangle((610, 120, 690, 280), fill=accent)
    draw.rectangle((640, 65, 675, 120), fill=(100, 118, 88))
    draw.polygon([(610, 150), (570, 220), (600, 230), (630, 165)], fill=(58, 72, 52))
    draw.polygon([(690, 150), (725, 220), (695, 230), (670, 165)], fill=(58, 72, 52))
    draw.polygon([(630, 280), (620, 360), (645, 360), (655, 290)], fill=(66, 82, 58))
    draw.polygon([(670, 280), (660, 360), (685, 360), (695, 290)], fill=(66, 82, 58))
    draw.text((24, 382), "Enemy01 Raider", fill=(64, 52, 40))
    draw.text((24, 400), "low poly melee raider", fill=(96, 82, 68))
    image.save(output_dir / "enemy01_preview.png")


def write_readme(output_dir, gltf_name, glb_name):
    readme = f"""# 敌人01 - Raider Animated

## 1. 资源说明

这是当前第一种敌人的素材版模型资源，对应游戏里的基础近战敌人 `Raider`。

这一版的目标是：

- 保持与当前玩法一致的人形近战敌人定位
- 继续保留低开销、网页端友好的体量
- 提供和其他敌人一致的动画状态机入口

## 2. 动画

- `Idle`
- `Walk`
- `Run`
- `Attack`
- `Hit`
- `Death`

## 3. 使用建议

- 网页项目优先使用 `{glb_name}`
- `Walk` / `Run` 是原地动作，位移由游戏逻辑控制
- `Attack` / `Hit` / `Death` 建议作为单次动作播放

## 4. 材质说明

- `enemy01_bark.png`：基础树皮 / 布料混合风格贴图参考
- `enemy01_moss.png`：苔藓 / 污渍风格贴图参考

## 5. 文件

- `{gltf_name}`
- `{glb_name}`
- `enemy01_bark.png`
- `enemy01_moss.png`
- `enemy01_preview.png`
- `enemy01_meta.json`
- `generate_enemy01.py`

## 6. 重新生成

```bash
python3 generate_enemy01.py
```
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def main():
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    gltf = build_gltf()
    gltf_path = output_dir / "model.gltf"
    gltf_path.write_text(json.dumps(gltf, ensure_ascii=False, indent=2), encoding="utf-8")

    glb_path = output_dir / "model.glb"
    try:
        model = GLTF2().load(str(gltf_path))
        model.save_binary(str(glb_path))
    except Exception as exc:
        glb_path.write_text(f"GLB export failed.\nReason: {exc}\nUse the glTF file instead.\n", encoding="utf-8")

    prepare_textures(output_dir)
    render_preview(output_dir)
    meta = {
        "name": "Enemy01 Raider",
        "style": "low_poly_raider",
        "approx_height_m": 2.18,
        "formats": ["gltf", "glb"],
        "textures": ["enemy01_bark.png", "enemy01_moss.png"],
        "animations": ["Idle", "Walk", "Run", "Attack", "Hit", "Death"],
        "notes": "Asset-driven replacement for the original procedural raider enemy.",
    }
    (output_dir / "enemy01_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    write_readme(output_dir, gltf_path.name, glb_path.name)

    print(gltf_path)
    print(glb_path)


if __name__ == "__main__":
    main()
