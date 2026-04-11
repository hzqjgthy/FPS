#!/usr/bin/env python3

import base64
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from pygltflib import GLTF2


OUTPUT_DIR = Path("/Users/thy/Desktop/ZiSuo/proj_06/generated_weapon02_animated")
TARGET_DIR = Path("/Users/thy/Desktop/KaiYuan_proj/FPS/素材/武器/枪/枪02")

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


def make_cylinder(length=1.0, radius=0.1, sides=12, radius_end=None):
    if radius_end is None:
        radius_end = radius
    half = length * 0.5
    positions = []
    normals = []
    indices = []
    ring_a = []
    ring_b = []

    for i in range(sides):
        angle = i / sides * math.pi * 2.0
        ring_a.append(np.array([-half, math.cos(angle) * radius, math.sin(angle) * radius], dtype=np.float64))
        ring_b.append(np.array([half, math.cos(angle) * radius_end, math.sin(angle) * radius_end], dtype=np.float64))

    for i in range(sides):
        j = (i + 1) % sides
        a, b, c, d = ring_a[i], ring_a[j], ring_b[j], ring_b[i]
        normal = np.cross(d - a, b - a)
        normal = normal / (np.linalg.norm(normal) or 1.0)
        start = len(positions)
        positions.extend([a, b, c, d])
        normals.extend([normal, normal, normal, normal])
        indices.extend([start, start + 1, start + 2, start, start + 2, start + 3])

    def add_cap(center_x, ring, flip):
        center_index = len(positions)
        positions.append((center_x, 0.0, 0.0))
        normals.append((-1.0, 0.0, 0.0) if flip else (1.0, 0.0, 0.0))
        for i in range(sides):
            j = (i + 1) % sides
            positions.extend([ring[j], ring[i]] if flip else [ring[i], ring[j]])
            normals.extend([(-1.0, 0.0, 0.0) if flip else (1.0, 0.0, 0.0)] * 2)
            idx_base = center_index + 1 + i * 2
            indices.extend([center_index, idx_base, idx_base + 1])

    add_cap(-half, ring_a, True)
    add_cap(half, ring_b, False)
    return geometry_dict(positions, normals, indices)


def add_group_part(groups, group, material, geo, translation=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0, 1.0), scale=(1.0, 1.0, 1.0)):
    groups.setdefault(group, {}).setdefault(material, []).append(
        transform_geometry(geo, translation=translation, rotation=rotation, scale=scale)
    )


def build_weapon_groups():
    box = make_box()
    cylinder = make_cylinder()
    groups = {}

    receiver = "receiver"
    bolt = "bolt"
    mag = "mag"

    tan = "tan"
    black = "black"
    polymer = "polymer"
    steel = "steel"
    accent = "accent"

    # Upper / lower receiver and handguard
    add_group_part(groups, receiver, tan, box, translation=(0.00, 0.08, 0.02), scale=(0.36, 0.09, 0.08))
    add_group_part(groups, receiver, tan, box, translation=(-0.08, 0.02, 0.02), scale=(0.24, 0.08, 0.08))
    add_group_part(groups, receiver, tan, box, translation=(0.24, 0.07, 0.02), scale=(0.32, 0.08, 0.09))
    add_group_part(groups, receiver, tan, box, translation=(0.23, 0.00, 0.02), scale=(0.20, 0.08, 0.08))
    add_group_part(groups, receiver, tan, box, translation=(0.40, 0.02, 0.02), scale=(0.28, 0.09, 0.10))
    add_group_part(groups, receiver, tan, box, translation=(0.38, -0.06, 0.02), scale=(0.22, 0.06, 0.07))

    for x in [0.29, 0.34, 0.39, 0.44, 0.49]:
        add_group_part(groups, receiver, black, box, translation=(x, 0.11, 0.02), scale=(0.026, 0.012, 0.10))

    for x in np.linspace(-0.14, 0.53, 15):
        add_group_part(groups, receiver, black, box, translation=(x, 0.14, 0.02), scale=(0.024, 0.010, 0.10))

    # Sights and optic
    add_group_part(groups, receiver, black, box, translation=(-0.11, 0.18, 0.02), scale=(0.05, 0.05, 0.02))
    add_group_part(groups, receiver, black, box, translation=(-0.10, 0.22, 0.02), scale=(0.02, 0.04, 0.02))
    add_group_part(groups, receiver, black, box, translation=(0.48, 0.17, 0.02), scale=(0.05, 0.04, 0.03))
    add_group_part(groups, receiver, black, box, translation=(0.49, 0.22, 0.02), scale=(0.02, 0.05, 0.02))
    add_group_part(groups, receiver, black, box, translation=(0.06, 0.21, 0.02), scale=(0.12, 0.07, 0.08))
    add_group_part(groups, receiver, steel, box, translation=(0.02, 0.17, 0.02), scale=(0.10, 0.02, 0.08))
    add_group_part(groups, receiver, accent, box, translation=(0.10, 0.22, 0.02), scale=(0.04, 0.03, 0.05))

    # Barrel and muzzle
    add_group_part(groups, receiver, steel, cylinder, translation=(0.63, 0.01, 0.02), rotation=quat_from_euler_xyz(0.0, 0.0, 90.0), scale=(0.50, 0.018, 0.018))
    add_group_part(groups, receiver, black, cylinder, translation=(0.43, 0.06, 0.02), rotation=quat_from_euler_xyz(0.0, 0.0, 90.0), scale=(0.14, 0.014, 0.014))
    add_group_part(groups, receiver, black, box, translation=(0.52, 0.05, 0.02), scale=(0.04, 0.06, 0.05))
    add_group_part(groups, receiver, steel, cylinder, translation=(0.85, 0.01, 0.02), rotation=quat_from_euler_xyz(0.0, 0.0, 90.0), scale=(0.09, 0.028, 0.028))
    add_group_part(groups, receiver, black, box, translation=(0.89, 0.01, 0.02), scale=(0.03, 0.02, 0.06))

    # Lower receiver and grip
    add_group_part(groups, receiver, tan, box, translation=(0.02, -0.05, 0.02), scale=(0.22, 0.10, 0.09))
    add_group_part(groups, receiver, tan, box, translation=(0.12, -0.12, 0.02), scale=(0.07, 0.08, 0.08))
    add_group_part(groups, receiver, black, box, translation=(0.10, -0.17, 0.02), scale=(0.08, 0.01, 0.05))
    add_group_part(groups, receiver, black, box, translation=(0.07, -0.14, 0.02), scale=(0.01, 0.06, 0.05))
    add_group_part(groups, receiver, black, box, translation=(0.13, -0.14, 0.02), scale=(0.01, 0.06, 0.05))
    add_group_part(groups, receiver, black, box, translation=(0.08, -0.10, 0.02), scale=(0.02, 0.05, 0.01))
    grip_rot = quat_from_euler_xyz(0.0, 0.0, -18.0)
    add_group_part(groups, receiver, polymer, box, translation=(0.01, -0.22, 0.02), rotation=grip_rot, scale=(0.08, 0.18, 0.05))
    add_group_part(groups, receiver, black, box, translation=(0.01, -0.30, 0.02), rotation=grip_rot, scale=(0.07, 0.03, 0.05))

    # Stock
    add_group_part(groups, receiver, black, box, translation=(-0.22, 0.05, 0.02), scale=(0.05, 0.08, 0.07))
    add_group_part(groups, receiver, tan, box, translation=(-0.34, 0.10, 0.02), scale=(0.12, 0.04, 0.05))
    add_group_part(groups, receiver, black, box, translation=(-0.38, 0.06, 0.05), scale=(0.18, 0.02, 0.02))
    add_group_part(groups, receiver, black, box, translation=(-0.38, 0.06, -0.01), scale=(0.18, 0.02, 0.02))
    add_group_part(groups, receiver, black, box, translation=(-0.50, 0.09, 0.05), rotation=quat_from_euler_xyz(0.0, 0.0, 10.0), scale=(0.07, 0.02, 0.02))
    add_group_part(groups, receiver, black, box, translation=(-0.50, 0.09, -0.01), rotation=quat_from_euler_xyz(0.0, 0.0, 10.0), scale=(0.07, 0.02, 0.02))
    add_group_part(groups, receiver, polymer, box, translation=(-0.55, 0.11, 0.02), scale=(0.04, 0.09, 0.08))
    add_group_part(groups, receiver, polymer, box, translation=(-0.49, 0.16, 0.02), scale=(0.08, 0.03, 0.07))

    # Selector / small fixed details
    add_group_part(groups, receiver, black, box, translation=(0.00, -0.02, 0.07), scale=(0.03, 0.02, 0.01))
    add_group_part(groups, receiver, black, box, translation=(-0.02, 0.02, 0.07), scale=(0.04, 0.01, 0.01))

    # Bolt / charging handle group
    add_group_part(groups, bolt, black, box, translation=(-0.01, 0.08, -0.045), scale=(0.05, 0.02, 0.02))
    add_group_part(groups, bolt, steel, box, translation=(0.03, 0.08, -0.020), scale=(0.12, 0.03, 0.005))

    # Magazine group
    mag_positions = [
        (0.13, -0.20, 0.02, -7.0),
        (0.15, -0.28, 0.02, -10.0),
        (0.17, -0.36, 0.02, -14.0),
        (0.21, -0.43, 0.02, -18.0),
    ]
    for x, y, z, rot_z in mag_positions:
        add_group_part(groups, mag, polymer, box, translation=(x, y, z), rotation=quat_from_euler_xyz(0.0, 0.0, rot_z), scale=(0.09, 0.10, 0.05))
    add_group_part(groups, mag, steel, box, translation=(0.23, -0.50, 0.02), rotation=quat_from_euler_xyz(0.0, 0.0, -18.0), scale=(0.09, 0.03, 0.05))

    return {group: {material: merge_geometries(geos) for material, geos in mats.items()} for group, mats in groups.items()}


def flatten_group_parts(groups):
    combined = {}
    for mats in groups.values():
        for material, geo in mats.items():
            combined.setdefault(material, []).append(geo)
    return {material: merge_geometries(geos) for material, geos in combined.items()}


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


def build_animations(node_lookup):
    base_translation = {
        "WeaponPose": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "BoltGroup": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "MagazineGroup": np.array([0.0, 0.0, 0.0], dtype=np.float64),
    }
    base_euler = {
        "WeaponPose": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "BoltGroup": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "MagazineGroup": np.array([0.0, 0.0, 0.0], dtype=np.float64),
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

    def rot_track(node_name, times, delta_eulers):
        values = []
        for delta in delta_eulers:
            euler = base_euler[node_name] + np.array(delta, dtype=np.float64)
            values.append(quat_from_euler_xyz(*euler))
        return {
            "node": node_lookup[node_name],
            "path": "rotation",
            "times": np.array(times, dtype=np.float32),
            "values": np.array(values, dtype=np.float32),
        }

    clips = []

    clips.append(
        {
            "name": "idle",
            "extras": {"loop": True},
            "tracks": [
                trans_track("WeaponPose", [0.0, 0.5, 1.0, 1.5], [(0.0, 0.0, 0.0), (0.0, 0.004, 0.0), (0.0, 0.0, 0.0), (0.0, -0.002, 0.0)]),
                rot_track("WeaponPose", [0.0, 0.5, 1.0, 1.5], [(0.4, -0.3, 0.0), (0.8, 0.4, -0.4), (0.2, -0.2, 0.1), (0.4, -0.3, 0.0)]),
            ],
        }
    )

    clips.append(
        {
            "name": "fire",
            "extras": {"loop": False},
            "tracks": [
                trans_track("WeaponPose", [0.0, 0.035, 0.08, 0.14, 0.24], [(0.0, 0.0, 0.0), (-0.03, -0.006, 0.0), (-0.015, 0.002, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
                rot_track("WeaponPose", [0.0, 0.035, 0.08, 0.14, 0.24], [(0.0, 0.0, 0.0), (0.0, 0.0, 4.5), (0.0, 0.0, 1.5), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
                trans_track("BoltGroup", [0.0, 0.03, 0.06, 0.12], [(0.0, 0.0, 0.0), (-0.055, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
            ],
        }
    )

    clips.append(
        {
            "name": "reload",
            "extras": {"loop": False},
            "tracks": [
                trans_track("WeaponPose", [0.0, 0.18, 0.45, 0.75, 1.05, 1.35], [(0.0, 0.0, 0.0), (0.02, -0.02, 0.04), (0.04, -0.05, 0.08), (0.03, -0.03, 0.06), (0.01, -0.01, 0.02), (0.0, 0.0, 0.0)]),
                rot_track("WeaponPose", [0.0, 0.18, 0.45, 0.75, 1.05, 1.35], [(0.0, 0.0, 0.0), (8.0, 0.0, 10.0), (18.0, 0.0, 18.0), (12.0, 0.0, 10.0), (4.0, 0.0, 3.0), (0.0, 0.0, 0.0)]),
                trans_track("MagazineGroup", [0.0, 0.12, 0.28, 0.46, 0.78, 1.0, 1.22], [(0.0, 0.0, 0.0), (0.02, -0.06, 0.02), (0.07, -0.20, 0.06), (0.10, -0.34, 0.08), (0.02, -0.12, 0.02), (0.0, -0.02, 0.0), (0.0, 0.0, 0.0)]),
                rot_track("MagazineGroup", [0.0, 0.12, 0.28, 0.46, 0.78, 1.0, 1.22], [(0.0, 0.0, 0.0), (6.0, 0.0, -12.0), (14.0, 0.0, -28.0), (18.0, 0.0, -44.0), (4.0, 0.0, -10.0), (0.0, 0.0, -2.0), (0.0, 0.0, 0.0)]),
                trans_track("BoltGroup", [0.0, 0.88, 0.98, 1.10, 1.22], [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (-0.05, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
            ],
        }
    )

    clips.append(
        {
            "name": "ads",
            "extras": {"loop": False},
            "tracks": [
                trans_track("WeaponPose", [0.0, 0.18, 0.34], [(0.0, 0.0, 0.0), (-0.04, 0.02, -0.05), (-0.08, 0.05, -0.08)]),
                rot_track("WeaponPose", [0.0, 0.18, 0.34], [(0.0, 0.0, 0.0), (-2.0, 0.0, -5.0), (-3.0, 0.0, -9.0)]),
            ],
        }
    )

    clips.append(
        {
            "name": "sprint",
            "extras": {"loop": True},
            "tracks": [
                trans_track("WeaponPose", [0.0, 0.35, 0.7, 1.05], [(0.05, -0.07, 0.10), (0.08, -0.10, 0.14), (0.06, -0.08, 0.12), (0.05, -0.07, 0.10)]),
                rot_track("WeaponPose", [0.0, 0.35, 0.7, 1.05], [(10.0, -6.0, 24.0), (14.0, -8.0, 32.0), (12.0, -6.0, 28.0), (10.0, -6.0, 24.0)]),
            ],
        }
    )

    return clips


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


def build_gltf():
    groups = build_weapon_groups()
    preview_parts = flatten_group_parts(groups)
    builder = BufferBuilder()
    meshes = []
    materials = [
        {
            "name": "TanBody",
            "pbrMetallicRoughness": {"baseColorFactor": [0.69, 0.61, 0.44, 1.0], "metallicFactor": 0.0, "roughnessFactor": 0.95},
        },
        {
            "name": "BlackMetal",
            "pbrMetallicRoughness": {"baseColorFactor": [0.16, 0.17, 0.18, 1.0], "metallicFactor": 0.2, "roughnessFactor": 0.62},
        },
        {
            "name": "Polymer",
            "pbrMetallicRoughness": {"baseColorFactor": [0.12, 0.12, 0.12, 1.0], "metallicFactor": 0.0, "roughnessFactor": 0.88},
        },
        {
            "name": "Steel",
            "pbrMetallicRoughness": {"baseColorFactor": [0.33, 0.35, 0.37, 1.0], "metallicFactor": 0.55, "roughnessFactor": 0.40},
        },
        {
            "name": "Accent",
            "pbrMetallicRoughness": {"baseColorFactor": [0.46, 0.22, 0.08, 1.0], "metallicFactor": 0.0, "roughnessFactor": 0.40},
            "emissiveFactor": [0.18, 0.07, 0.02],
        },
    ]
    material_lookup = {"tan": 0, "black": 1, "polymer": 2, "steel": 3, "accent": 4}

    mesh_index_lookup = {}
    for group_name, mats in groups.items():
        for material_name, geo in mats.items():
            pos_accessor = builder.add_accessor(geo["positions"], FLOAT, "VEC3", target=ARRAY_BUFFER)
            norm_accessor = builder.add_accessor(geo["normals"], FLOAT, "VEC3", target=ARRAY_BUFFER)
            idx_accessor = builder.add_accessor(geo["indices"], UNSIGNED_SHORT, "SCALAR", target=ELEMENT_ARRAY_BUFFER)
            mesh_index_lookup[(group_name, material_name)] = len(meshes)
            meshes.append(
                {
                    "name": f"{group_name}_{material_name}",
                    "primitives": [
                        {
                            "attributes": {"POSITION": pos_accessor, "NORMAL": norm_accessor},
                            "indices": idx_accessor,
                            "material": material_lookup[material_name],
                        }
                    ],
                }
            )

    nodes = [
        {"name": "SCAR-H_Root", "children": [1]},
        {"name": "WeaponPose", "translation": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0, 1.0], "children": [2]},
        {"name": "ReceiverGroup", "translation": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0, 1.0], "children": [3, 4]},
        {"name": "BoltGroup", "translation": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0, 1.0], "children": []},
        {"name": "MagazineGroup", "translation": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0, 1.0], "children": []},
    ]

    group_parent = {"receiver": 2, "bolt": 3, "mag": 4}
    node_lookup = {"WeaponPose": 1, "BoltGroup": 3, "MagazineGroup": 4}

    for group_name, mats in groups.items():
        for material_name in mats.keys():
            mesh_index = mesh_index_lookup[(group_name, material_name)]
            node_index = len(nodes)
            nodes.append({"name": f"{group_name}_{material_name}_node", "mesh": mesh_index})
            nodes[group_parent[group_name]].setdefault("children", []).append(node_index)

    clips = build_animations(node_lookup)
    animations = []
    for clip in clips:
        samplers = []
        channels = []
        for track in clip["tracks"]:
            input_accessor = builder.add_accessor(track["times"], FLOAT, "SCALAR")
            output_type = "VEC4" if track["path"] == "rotation" else "VEC3"
            output_accessor = builder.add_accessor(track["values"], FLOAT, output_type)
            sampler_index = len(samplers)
            samplers.append({"input": input_accessor, "output": output_accessor, "interpolation": "LINEAR"})
            channels.append({"sampler": sampler_index, "target": {"node": track["node"], "path": track["path"]}})
        animations.append({"name": clip["name"], "samplers": samplers, "channels": channels, "extras": clip.get("extras", {})})

    gltf = {
        "asset": {"version": "2.0", "generator": "Codex SCAR-H Animated Procedural Generator"},
        "scene": 0,
        "scenes": [{"name": "SCARHAnimatedScene", "nodes": [0]}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "animations": animations,
        "bufferViews": builder.buffer_views,
        "accessors": builder.accessors,
        "buffers": [
            {
                "byteLength": len(builder.data),
                "uri": "data:application/octet-stream;base64," + base64.b64encode(builder.data).decode("ascii"),
            }
        ],
    }
    return gltf, preview_parts


def render_preview(output_dir, parts):
    colors = {
        "tan": np.array([176, 154, 108], dtype=np.float64),
        "black": np.array([42, 44, 46], dtype=np.float64),
        "polymer": np.array([28, 29, 30], dtype=np.float64),
        "steel": np.array([92, 98, 104], dtype=np.float64),
        "accent": np.array([148, 74, 24], dtype=np.float64),
    }
    triangles = []
    for material, geo in parts.items():
        verts = np.asarray(geo["positions"], dtype=np.float64)
        tri_ids = geo["indices"].reshape(-1, 3)
        for tri in tri_ids:
            triangles.append((verts[tri], colors[material]))

    points = np.concatenate([tri[0] for tri in triangles], axis=0)
    center = (points.min(axis=0) + points.max(axis=0)) * 0.5

    def rotation_matrix(yaw_deg, pitch_deg):
        yaw = math.radians(yaw_deg)
        pitch = math.radians(pitch_deg)
        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        ry = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]], dtype=np.float64)
        rx = np.array([[1.0, 0.0, 0.0], [0.0, cp, -sp], [0.0, sp, cp]], dtype=np.float64)
        return rx @ ry

    views = [("Side", 0.0, -8.0), ("3/4", 32.0, -14.0)]
    width = 520
    height = 320
    image = Image.new("RGB", (width * len(views), height), (239, 235, 226))
    light = np.array([0.5, -0.7, 0.5], dtype=np.float64)
    light /= np.linalg.norm(light)

    for view_index, (label, yaw, pitch) in enumerate(views):
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle([view_index * width + 8, 8, (view_index + 1) * width - 8, height - 8], radius=18, fill=(248, 245, 239), outline=(198, 189, 174), width=2)
        rot = rotation_matrix(yaw, pitch)
        transformed = []
        projected = []
        for tri, color in triangles:
            p = (tri - center) @ rot.T
            transformed.append((p, color))
            projected.append(p[:, :2])
        projected = np.concatenate(projected, axis=0)
        minimum = projected.min(axis=0)
        maximum = projected.max(axis=0)
        span = max(maximum[0] - minimum[0], maximum[1] - minimum[1])
        scale = (min(width, height) - 70) / span
        draw_items = []
        for points_3d, color in transformed:
            normal = np.cross(points_3d[1] - points_3d[0], points_3d[2] - points_3d[0])
            normal = normal / (np.linalg.norm(normal) or 1.0)
            shade = max(0.20, float(normal @ light))
            shaded = np.clip(color * (0.54 + 0.56 * shade), 0, 255).astype(int)
            polygon = []
            for x, y, z in points_3d:
                sx = (x - (minimum[0] + maximum[0]) * 0.5) * scale + width * 0.5 + view_index * width
                sy = height * 0.54 - (y - (minimum[1] + maximum[1]) * 0.5) * scale
                polygon.append((sx, sy))
            draw_items.append((points_3d[:, 2].mean(), tuple(shaded.tolist()), polygon))
        draw_items.sort(key=lambda item: item[0])
        for _, fill, polygon in draw_items:
            draw.polygon(polygon, fill=fill)
        draw.text((view_index * width + 16, 14), label, fill=(88, 72, 54))

    image.save(output_dir / "weapon02_preview.png")


def write_readme(output_dir, gltf_name, glb_name):
    readme = f"""# 枪02 - SCAR-H Animated

## 1. 资源说明

这是一个面向网页游戏使用的 `SCAR-H` 战斗步枪模型资源，包含基础动作：

- `idle`
- `fire`
- `reload`
- `ads`
- `sprint`

## 2. 动作说明

### `idle`

- 循环动作
- 轻微呼吸式晃动
- 适合默认持枪待机

### `fire`

- 单次动作
- 带整枪后坐和枪机后拉
- 适合作为单发或连发中的基础射击动作

### `reload`

- 单次动作
- 带枪身倾斜、弹匣抽离与回装、枪机回拉
- 适合作为完整换弹基础

### `ads`

- 单次动作
- 将武器从默认持枪位置推进到瞄准姿态

### `sprint`

- 循环动作
- 枪口下压、持枪侧摆
- 适合奔跑状态

## 3. 使用建议

- 网页端优先使用 `{glb_name}`
- `idle` 和 `sprint` 建议循环播放
- `fire`、`reload`、`ads` 建议单次播放
- 如果你后续要做更强的第一人称表现，可以继续细化枪机、枪托、拉机柄、弹匣的可动节点

## 4. 文件

- `{gltf_name}`
- `{glb_name}`
- `weapon02_preview.png`
- `weapon02_meta.json`
- `generate_weapon02_animated.py`
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def write_meta(output_dir):
    meta = {
        "name": "SCAR-H",
        "asset_name": "枪02",
        "category": "battle_rifle",
        "style": "web_ready_hard_hitting_rifle",
        "formats": ["gltf", "glb"],
        "animations": ["idle", "fire", "reload", "ads", "sprint"],
        "weapon_traits": {
            "damage_profile": "high_per_shot",
            "range_profile": "strong_mid_range",
            "handling": "heavy_recoil_lower_fire_rate",
            "best_for": ["tap_fire", "short_bursts", "heavy_feedback"],
        },
    }
    (output_dir / "weapon02_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    gltf, preview_parts = build_gltf()
    gltf_path = output_dir / "model.gltf"
    gltf_path.write_text(json.dumps(gltf, ensure_ascii=False, indent=2), encoding="utf-8")

    glb_path = output_dir / "model.glb"
    try:
        model = GLTF2().load(str(gltf_path))
        model.save_binary(str(glb_path))
    except Exception as exc:
        glb_path.write_text(f"GLB export failed.\nReason: {exc}\nUse the glTF file instead.\n", encoding="utf-8")

    render_preview(output_dir, preview_parts)
    write_meta(output_dir)
    write_readme(output_dir, gltf_path.name, glb_path.name)

    print(gltf_path)
    print(glb_path)
    print(output_dir / "README.md")
    print(TARGET_DIR)


if __name__ == "__main__":
    main()
