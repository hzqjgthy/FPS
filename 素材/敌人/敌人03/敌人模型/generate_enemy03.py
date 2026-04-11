#!/usr/bin/env python3

import base64
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


OUTPUT_DIR = Path("/Users/thy/Desktop/KaiYuan_proj/FPS/素材/敌人/敌人03/敌人模型")
SOURCE_FBX = Path("/Users/thy/Desktop/KaiYuan_proj/FPS/素材/敌人/敌人01-树妖.fbx")

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


def irregular_value(seed, index):
    value = math.sin(seed * 13.17 + index * 4.21) * 0.5 + math.cos(seed * 2.93 + index * 1.37) * 0.5
    return value


def geometry_dict(positions, normals, uvs, indices):
    return {
        "positions": np.asarray(positions, dtype=np.float32),
        "normals": np.asarray(normals, dtype=np.float32),
        "uvs": np.asarray(uvs, dtype=np.float32),
        "indices": np.asarray(indices, dtype=np.uint16),
    }


def merge_geometries(geometries):
    positions = []
    normals = []
    uvs = []
    indices = []
    offset = 0
    for geo in geometries:
        positions.append(geo["positions"])
        normals.append(geo["normals"])
        uvs.append(geo["uvs"])
        indices.append(geo["indices"] + offset)
        offset += len(geo["positions"])
    return geometry_dict(np.concatenate(positions), np.concatenate(normals), np.concatenate(uvs), np.concatenate(indices))


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

    return geometry_dict(np.asarray(positions), np.asarray(normals), geo["uvs"], geo["indices"])


def make_box(size=(1.0, 1.0, 1.0), uv_scale=(1.0, 1.0)):
    sx, sy, sz = size
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    u_scale, v_scale = uv_scale
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
    uvs = []
    indices = []
    for a, b, c, d, normal in faces:
        start = len(positions)
        positions.extend([a, b, c, d])
        normals.extend([normal, normal, normal, normal])
        uvs.extend([(0.0, 0.0), (u_scale, 0.0), (u_scale, v_scale), (0.0, v_scale)])
        indices.extend([start, start + 1, start + 2, start, start + 2, start + 3])
    return geometry_dict(positions, normals, uvs, indices)


def make_tapered_cylinder(height, radius_bottom, radius_top, sides=10, uv_scale=(1.0, 1.5), wobble=0.14, seed=1.0, cap_bottom=False, cap_top=False):
    half = height * 0.5
    positions = []
    normals = []
    uvs = []
    indices = []

    ring_bottom = []
    ring_top = []
    for i in range(sides):
        frac = i / sides
        angle = frac * math.pi * 2.0
        wobble_bottom = 1.0 + wobble * irregular_value(seed, i)
        wobble_top = 1.0 + wobble * irregular_value(seed + 5.0, i + 17)
        rb = radius_bottom * wobble_bottom
        rt = radius_top * wobble_top
        x0 = math.cos(angle) * rb
        z0 = math.sin(angle) * rb
        x1 = math.cos(angle + 0.08 * irregular_value(seed + 1.0, i + 3)) * rt
        z1 = math.sin(angle + 0.08 * irregular_value(seed + 2.0, i + 9)) * rt
        ring_bottom.append(np.array([x0, -half, z0], dtype=np.float64))
        ring_top.append(np.array([x1, half, z1], dtype=np.float64))

    u_scale, v_scale = uv_scale
    for i in range(sides):
        j = (i + 1) % sides
        a = ring_bottom[i]
        b = ring_bottom[j]
        c = ring_top[j]
        d = ring_top[i]
        normal = np.cross(d - a, b - a)
        normal = normal / (np.linalg.norm(normal) or 1.0)
        start = len(positions)
        positions.extend([a, b, c, d])
        normals.extend([normal, normal, normal, normal])
        u0 = i / sides * u_scale
        u1 = (i + 1) / sides * u_scale
        uvs.extend([(u0, 0.0), (u1, 0.0), (u1, v_scale), (u0, v_scale)])
        indices.extend([start, start + 1, start + 2, start, start + 2, start + 3])

    if cap_bottom:
        center_index = len(positions)
        positions.append((0.0, -half, 0.0))
        normals.append((0.0, -1.0, 0.0))
        uvs.append((0.5, 0.5))
        for i in range(sides):
            j = (i + 1) % sides
            positions.extend([ring_bottom[j], ring_bottom[i]])
            normals.extend([(0.0, -1.0, 0.0), (0.0, -1.0, 0.0)])
            uvs.extend([(0.5 + ring_bottom[j][0], 0.5 + ring_bottom[j][2]), (0.5 + ring_bottom[i][0], 0.5 + ring_bottom[i][2])])
            indices.extend([center_index, center_index + 1 + i * 2, center_index + 2 + i * 2])

    if cap_top:
        center_index = len(positions)
        positions.append((0.0, half, 0.0))
        normals.append((0.0, 1.0, 0.0))
        uvs.append((0.5, 0.5))
        for i in range(sides):
            j = (i + 1) % sides
            positions.extend([ring_top[i], ring_top[j]])
            normals.extend([(0.0, 1.0, 0.0), (0.0, 1.0, 0.0)])
            uvs.extend([(0.5 + ring_top[i][0], 0.5 + ring_top[i][2]), (0.5 + ring_top[j][0], 0.5 + ring_top[j][2])])
            indices.extend([center_index, center_index + 1 + i * 2, center_index + 2 + i * 2])

    return geometry_dict(positions, normals, uvs, indices)


def make_spike(length=1.0, radius=0.16, sides=6, uv_scale=(1.0, 1.0), bend=(0.0, 0.0), seed=1.0):
    positions = []
    normals = []
    uvs = []
    indices = []
    tip = np.array([bend[0], length, bend[1]], dtype=np.float64)
    base = []
    for i in range(sides):
        frac = i / sides
        angle = frac * math.pi * 2.0
        rr = radius * (1.0 + 0.18 * irregular_value(seed, i))
        base.append(np.array([math.cos(angle) * rr, 0.0, math.sin(angle) * rr], dtype=np.float64))

    u_scale, v_scale = uv_scale
    for i in range(sides):
        j = (i + 1) % sides
        a = base[i]
        b = base[j]
        c = tip
        normal = np.cross(b - a, c - a)
        normal = normal / (np.linalg.norm(normal) or 1.0)
        start = len(positions)
        positions.extend([a, b, c])
        normals.extend([normal, normal, normal])
        u0 = i / sides * u_scale
        u1 = (i + 1) / sides * u_scale
        uvs.extend([(u0, 0.0), (u1, 0.0), ((u0 + u1) * 0.5, v_scale)])
        indices.extend([start, start + 1, start + 2])

    center_index = len(positions)
    positions.append((0.0, 0.0, 0.0))
    normals.append((0.0, -1.0, 0.0))
    uvs.append((0.5, 0.5))
    for i in range(sides):
        j = (i + 1) % sides
        positions.extend([base[j], base[i]])
        normals.extend([(0.0, -1.0, 0.0), (0.0, -1.0, 0.0)])
        uvs.extend([(0.5 + base[j][0], 0.5 + base[j][2]), (0.5 + base[i][0], 0.5 + base[i][2])])
        indices.extend([center_index, center_index + 1 + i * 2, center_index + 2 + i * 2])
    return geometry_dict(positions, normals, uvs, indices)


def make_moss_patch(width=0.6, height=0.25, depth=0.18, segments_u=6, segments_v=4, uv_scale=(1.2, 1.2)):
    positions = []
    normals = []
    uvs = []
    indices = []
    for y in range(segments_v + 1):
        fy = y / segments_v
        theta = fy * math.pi * 0.5
        for x in range(segments_u + 1):
            fx = x / segments_u
            phi = (fx - 0.5) * math.pi
            px = math.sin(phi) * width * 0.5
            py = math.sin(theta) * height
            pz = math.cos(phi) * math.cos(theta) * depth
            normal = np.array([px / max(width * 0.5, 0.001), py / max(height, 0.001), pz / max(depth, 0.001)], dtype=np.float64)
            normal = normal / (np.linalg.norm(normal) or 1.0)
            positions.append((px, py, pz))
            normals.append(normal)
            uvs.append((fx * uv_scale[0], fy * uv_scale[1]))
    cols = segments_u + 1
    for y in range(segments_v):
        for x in range(segments_u):
            a = y * cols + x
            b = a + 1
            c = a + cols + 1
            d = a + cols
            indices.extend([a, b, c, a, c, d])
    return geometry_dict(positions, normals, uvs, indices)


def bark_plate(width, height, depth, lean=(0.0, 0.0, 0.0), uv_scale=(1.0, 1.0)):
    plate = make_box((width, height, depth), uv_scale=uv_scale)
    return transform_geometry(plate, rotation=quat_from_euler_xyz(*lean))


def build_mesh_library():
    meshes = {}

    meshes["hips_bark"] = merge_geometries(
        [
            make_tapered_cylinder(0.42, 0.34, 0.28, sides=10, uv_scale=(1.0, 0.9), wobble=0.12, seed=4.0, cap_bottom=True),
            transform_geometry(make_spike(0.44, 0.12, sides=5, uv_scale=(0.8, 0.7), bend=(0.02, 0.03), seed=10.0), translation=(-0.20, -0.16, 0.11), rotation=quat_from_euler_xyz(-76.0, -18.0, 22.0)),
            transform_geometry(make_spike(0.38, 0.10, sides=5, uv_scale=(0.8, 0.7), bend=(-0.01, 0.02), seed=11.0), translation=(0.02, -0.16, 0.14), rotation=quat_from_euler_xyz(-82.0, 0.0, 0.0)),
            transform_geometry(make_spike(0.44, 0.12, sides=5, uv_scale=(0.8, 0.7), bend=(-0.02, 0.03), seed=12.0), translation=(0.21, -0.16, 0.08), rotation=quat_from_euler_xyz(-78.0, 18.0, -22.0)),
            transform_geometry(bark_plate(0.42, 0.18, 0.10, lean=(16.0, 0.0, 0.0), uv_scale=(1.0, 0.6)), translation=(0.0, 0.06, 0.24)),
        ]
    )

    meshes["torso_lower_bark"] = merge_geometries(
        [
            make_tapered_cylinder(0.90, 0.42, 0.32, sides=12, uv_scale=(1.2, 2.4), wobble=0.16, seed=20.0),
            transform_geometry(bark_plate(0.52, 0.34, 0.14, lean=(12.0, 0.0, 0.0), uv_scale=(1.1, 0.8)), translation=(0.0, 0.08, 0.25)),
            transform_geometry(bark_plate(0.26, 0.52, 0.12, lean=(0.0, 0.0, -20.0), uv_scale=(0.8, 1.2)), translation=(-0.34, 0.12, 0.05)),
            transform_geometry(bark_plate(0.26, 0.52, 0.12, lean=(0.0, 0.0, 20.0), uv_scale=(0.8, 1.2)), translation=(0.34, 0.14, 0.03)),
            transform_geometry(make_spike(0.28, 0.08, sides=5, uv_scale=(0.6, 0.6), bend=(0.02, 0.02), seed=24.0), translation=(-0.20, 0.26, -0.18), rotation=quat_from_euler_xyz(-36.0, 0.0, -32.0)),
            transform_geometry(make_spike(0.24, 0.07, sides=5, uv_scale=(0.6, 0.6), bend=(-0.02, 0.01), seed=25.0), translation=(0.24, 0.18, -0.15), rotation=quat_from_euler_xyz(-24.0, 0.0, 26.0)),
        ]
    )

    meshes["chest_bark"] = merge_geometries(
        [
            make_tapered_cylinder(0.80, 0.40, 0.26, sides=12, uv_scale=(1.4, 2.2), wobble=0.18, seed=30.0),
            transform_geometry(bark_plate(0.58, 0.40, 0.16, lean=(10.0, 0.0, 0.0), uv_scale=(1.0, 0.9)), translation=(0.0, 0.06, 0.24)),
            transform_geometry(bark_plate(0.36, 0.18, 0.14, lean=(0.0, 0.0, -12.0), uv_scale=(0.8, 0.6)), translation=(-0.30, 0.28, 0.08)),
            transform_geometry(bark_plate(0.36, 0.18, 0.14, lean=(0.0, 0.0, 12.0), uv_scale=(0.8, 0.6)), translation=(0.30, 0.30, 0.06)),
            transform_geometry(make_spike(0.22, 0.08, sides=5, uv_scale=(0.6, 0.6), bend=(0.02, -0.01), seed=33.0), translation=(-0.20, 0.26, -0.17), rotation=quat_from_euler_xyz(-30.0, 0.0, -24.0)),
            transform_geometry(make_spike(0.26, 0.08, sides=5, uv_scale=(0.6, 0.6), bend=(-0.02, -0.01), seed=34.0), translation=(0.18, 0.18, -0.18), rotation=quat_from_euler_xyz(-36.0, 0.0, 22.0)),
        ]
    )

    meshes["head_bark"] = merge_geometries(
        [
            make_tapered_cylinder(0.58, 0.30, 0.24, sides=10, uv_scale=(1.0, 1.4), wobble=0.12, seed=40.0),
            transform_geometry(make_box((0.42, 0.16, 0.24), uv_scale=(0.8, 0.5)), translation=(0.0, -0.06, 0.22), rotation=quat_from_euler_xyz(-8.0, 0.0, 0.0)),
            transform_geometry(bark_plate(0.52, 0.16, 0.12, lean=(18.0, 0.0, 0.0), uv_scale=(1.0, 0.5)), translation=(0.0, 0.18, 0.20)),
            transform_geometry(bark_plate(0.24, 0.28, 0.10, lean=(0.0, 0.0, -18.0), uv_scale=(0.7, 0.8)), translation=(-0.23, 0.02, 0.04)),
            transform_geometry(bark_plate(0.24, 0.28, 0.10, lean=(0.0, 0.0, 18.0), uv_scale=(0.7, 0.8)), translation=(0.23, 0.03, 0.02)),
            transform_geometry(make_spike(0.16, 0.06, sides=5, uv_scale=(0.5, 0.5), bend=(0.02, 0.00), seed=43.0), translation=(-0.14, -0.03, 0.18), rotation=quat_from_euler_xyz(-56.0, 0.0, -12.0)),
            transform_geometry(make_spike(0.16, 0.06, sides=5, uv_scale=(0.5, 0.5), bend=(-0.02, 0.00), seed=44.0), translation=(0.14, -0.03, 0.18), rotation=quat_from_euler_xyz(-56.0, 0.0, 12.0)),
        ]
    )

    meshes["upper_arm_bark"] = merge_geometries(
        [
            make_tapered_cylinder(0.76, 0.16, 0.12, sides=8, uv_scale=(0.9, 1.8), wobble=0.16, seed=50.0),
            transform_geometry(bark_plate(0.18, 0.22, 0.10, lean=(0.0, 0.0, -18.0), uv_scale=(0.5, 0.6)), translation=(-0.09, 0.10, 0.06)),
            transform_geometry(make_spike(0.18, 0.05, sides=5, uv_scale=(0.5, 0.5), bend=(0.02, 0.0), seed=51.0), translation=(0.07, -0.08, -0.08), rotation=quat_from_euler_xyz(-20.0, 0.0, 36.0)),
        ]
    )

    meshes["forearm_bark"] = merge_geometries(
        [
            make_tapered_cylinder(0.70, 0.13, 0.10, sides=8, uv_scale=(0.9, 1.8), wobble=0.16, seed=60.0),
            transform_geometry(bark_plate(0.16, 0.18, 0.08, lean=(0.0, 0.0, 20.0), uv_scale=(0.4, 0.5)), translation=(0.07, -0.06, 0.06)),
            transform_geometry(make_spike(0.20, 0.05, sides=5, uv_scale=(0.5, 0.5), bend=(-0.02, 0.02), seed=61.0), translation=(-0.05, 0.05, -0.09), rotation=quat_from_euler_xyz(-12.0, 0.0, -32.0)),
        ]
    )

    meshes["claw_hand_bark"] = merge_geometries(
        [
            make_tapered_cylinder(0.26, 0.12, 0.08, sides=7, uv_scale=(0.7, 0.7), wobble=0.16, seed=70.0),
            transform_geometry(make_spike(0.34, 0.05, sides=5, uv_scale=(0.5, 0.7), bend=(0.04, 0.02), seed=71.0), translation=(-0.10, 0.02, 0.06), rotation=quat_from_euler_xyz(-74.0, -6.0, -16.0)),
            transform_geometry(make_spike(0.42, 0.06, sides=5, uv_scale=(0.5, 0.8), bend=(0.02, 0.04), seed=72.0), translation=(0.00, 0.04, 0.09), rotation=quat_from_euler_xyz(-80.0, 0.0, 0.0)),
            transform_geometry(make_spike(0.32, 0.05, sides=5, uv_scale=(0.5, 0.7), bend=(-0.04, 0.02), seed=73.0), translation=(0.10, 0.00, 0.05), rotation=quat_from_euler_xyz(-72.0, 6.0, 18.0)),
        ]
    )

    meshes["thigh_bark"] = merge_geometries(
        [
            make_tapered_cylinder(0.84, 0.19, 0.13, sides=8, uv_scale=(0.9, 1.9), wobble=0.14, seed=80.0),
            transform_geometry(bark_plate(0.18, 0.20, 0.10, lean=(12.0, 0.0, 0.0), uv_scale=(0.5, 0.6)), translation=(0.0, 0.10, 0.10)),
        ]
    )

    meshes["shin_bark"] = merge_geometries(
        [
            make_tapered_cylinder(0.78, 0.15, 0.10, sides=8, uv_scale=(0.9, 1.8), wobble=0.14, seed=90.0),
            transform_geometry(bark_plate(0.18, 0.30, 0.08, lean=(4.0, 0.0, 0.0), uv_scale=(0.5, 0.8)), translation=(0.0, -0.04, 0.08)),
            transform_geometry(make_spike(0.20, 0.05, sides=5, uv_scale=(0.5, 0.5), bend=(0.0, 0.03), seed=91.0), translation=(0.05, 0.08, -0.06), rotation=quat_from_euler_xyz(-12.0, 0.0, 16.0)),
        ]
    )

    meshes["foot_bark"] = merge_geometries(
        [
            make_box((0.24, 0.16, 0.30), uv_scale=(0.7, 0.7)),
            transform_geometry(make_spike(0.22, 0.05, sides=5, uv_scale=(0.4, 0.5), bend=(0.02, 0.02), seed=100.0), translation=(-0.10, -0.04, 0.16), rotation=quat_from_euler_xyz(-76.0, -12.0, -4.0)),
            transform_geometry(make_spike(0.28, 0.05, sides=5, uv_scale=(0.4, 0.6), bend=(0.00, 0.03), seed=101.0), translation=(0.00, -0.04, 0.18), rotation=quat_from_euler_xyz(-82.0, 0.0, 0.0)),
            transform_geometry(make_spike(0.22, 0.05, sides=5, uv_scale=(0.4, 0.5), bend=(-0.02, 0.02), seed=102.0), translation=(0.10, -0.04, 0.16), rotation=quat_from_euler_xyz(-76.0, 12.0, 4.0)),
        ]
    )

    meshes["horn_bark"] = merge_geometries(
        [
            make_spike(0.54, 0.11, sides=6, uv_scale=(0.8, 1.1), bend=(0.08, -0.04), seed=110.0),
            transform_geometry(make_spike(0.18, 0.06, sides=5, uv_scale=(0.4, 0.4), bend=(0.02, 0.0), seed=111.0), translation=(0.02, 0.22, -0.04), rotation=quat_from_euler_xyz(20.0, 0.0, 18.0)),
        ]
    )

    meshes["shoulder_spike_bark"] = merge_geometries(
        [
            make_spike(0.44, 0.10, sides=5, uv_scale=(0.6, 0.9), bend=(0.04, -0.02), seed=120.0),
            transform_geometry(make_spike(0.18, 0.05, sides=5, uv_scale=(0.4, 0.4), bend=(0.01, 0.0), seed=121.0), translation=(-0.02, 0.22, -0.01), rotation=quat_from_euler_xyz(12.0, 0.0, -16.0)),
        ]
    )

    meshes["back_spike_bark"] = merge_geometries(
        [
            make_spike(0.50, 0.10, sides=5, uv_scale=(0.6, 0.9), bend=(0.02, -0.05), seed=130.0),
            transform_geometry(make_spike(0.24, 0.05, sides=5, uv_scale=(0.4, 0.4), bend=(-0.02, 0.0), seed=131.0), translation=(0.03, 0.18, -0.03), rotation=quat_from_euler_xyz(18.0, 0.0, 18.0)),
        ]
    )

    meshes["moss_patch"] = make_moss_patch()
    meshes["eye_glow"] = make_box((0.08, 0.06, 0.04))
    return meshes


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
        if accessor_type != "SCALAR":
            accessor["min"] = [float(v) for v in arr.min(axis=0)]
            accessor["max"] = [float(v) for v in arr.max(axis=0)]
        elif component_type == FLOAT:
            accessor["min"] = [float(arr.min())]
            accessor["max"] = [float(arr.max())]
        else:
            accessor["min"] = [int(arr.min())]
            accessor["max"] = [int(arr.max())]
        self.accessors.append(accessor)
        return len(self.accessors) - 1


def add_node(nodes, node_lookup, name, translation=None, rotation=None, scale=None, mesh=None):
    node = {"name": name}
    if translation is not None:
        node["translation"] = [float(v) for v in translation]
    if rotation is not None:
        node["rotation"] = [float(v) for v in normalize_quat(rotation)]
    if scale is not None:
        node["scale"] = [float(v) for v in scale]
    if mesh is not None:
        node["mesh"] = mesh
    nodes.append(node)
    node_lookup[name] = len(nodes) - 1
    return len(nodes) - 1


def link_child(nodes, parent, child):
    nodes[parent].setdefault("children", []).append(child)


def attach_mesh(nodes, node_lookup, mesh_lookup, parent, name, mesh_name, translation=(0.0, 0.0, 0.0), rotation=None, scale=(1.0, 1.0, 1.0)):
    idx = add_node(nodes, node_lookup, name, translation=translation, rotation=rotation, scale=scale, mesh=mesh_lookup[mesh_name])
    link_child(nodes, parent, idx)
    return idx


def build_enemy_structure(mesh_lookup):
    nodes = []
    node_lookup = {}

    root = add_node(nodes, node_lookup, "EnemyRoot", translation=(0.0, 0.0, 0.0))
    hips = add_node(nodes, node_lookup, "Hips", translation=(0.0, 1.08, 0.0))
    link_child(nodes, root, hips)
    attach_mesh(nodes, node_lookup, mesh_lookup, hips, "HipsGeom", "hips_bark", translation=(0.0, 0.06, 0.0))

    spine_low = add_node(nodes, node_lookup, "SpineLow", translation=(0.0, 0.20, 0.00), rotation=quat_from_euler_xyz(8.0, 0.0, 0.0))
    link_child(nodes, hips, spine_low)
    attach_mesh(nodes, node_lookup, mesh_lookup, spine_low, "TorsoLowerGeom", "torso_lower_bark", translation=(0.0, 0.38, 0.0))

    spine_high = add_node(nodes, node_lookup, "SpineHigh", translation=(0.0, 0.66, 0.02), rotation=quat_from_euler_xyz(6.0, 0.0, 0.0))
    link_child(nodes, spine_low, spine_high)
    attach_mesh(nodes, node_lookup, mesh_lookup, spine_high, "ChestGeom", "chest_bark", translation=(0.0, 0.30, 0.0))
    attach_mesh(nodes, node_lookup, mesh_lookup, spine_high, "ChestMossGeom", "moss_patch", translation=(0.0, 0.12, 0.25), rotation=quat_from_euler_xyz(16.0, 0.0, 0.0), scale=(0.70, 0.32, 0.26))
    attach_mesh(nodes, node_lookup, mesh_lookup, spine_high, "ShoulderMoss_L_Geom", "moss_patch", translation=(-0.28, 0.28, 0.06), rotation=quat_from_euler_xyz(26.0, 0.0, -34.0), scale=(0.28, 0.18, 0.16))
    attach_mesh(nodes, node_lookup, mesh_lookup, spine_high, "ShoulderMoss_R_Geom", "moss_patch", translation=(0.28, 0.28, 0.04), rotation=quat_from_euler_xyz(26.0, 0.0, 34.0), scale=(0.28, 0.18, 0.16))

    attach_mesh(nodes, node_lookup, mesh_lookup, spine_high, "ShoulderSpike_L_Geom", "shoulder_spike_bark", translation=(-0.38, 0.34, -0.08), rotation=quat_from_euler_xyz(-40.0, 10.0, -88.0), scale=(0.50, 0.72, 0.50))
    attach_mesh(nodes, node_lookup, mesh_lookup, spine_high, "ShoulderSpike_R_Geom", "shoulder_spike_bark", translation=(0.38, 0.34, -0.08), rotation=quat_from_euler_xyz(-40.0, -10.0, 88.0), scale=(0.50, 0.72, 0.50))
    attach_mesh(nodes, node_lookup, mesh_lookup, spine_high, "BackSpikeA_Geom", "back_spike_bark", translation=(-0.12, 0.34, -0.18), rotation=quat_from_euler_xyz(-54.0, 0.0, -12.0), scale=(0.52, 0.74, 0.52))
    attach_mesh(nodes, node_lookup, mesh_lookup, spine_high, "BackSpikeB_Geom", "back_spike_bark", translation=(0.15, 0.16, -0.20), rotation=quat_from_euler_xyz(-48.0, 0.0, 14.0), scale=(0.44, 0.62, 0.44))

    neck = add_node(nodes, node_lookup, "Neck", translation=(0.0, 0.52, 0.05), rotation=quat_from_euler_xyz(-4.0, 0.0, 0.0))
    link_child(nodes, spine_high, neck)
    head = add_node(nodes, node_lookup, "Head", translation=(0.0, 0.18, 0.08))
    link_child(nodes, neck, head)
    attach_mesh(nodes, node_lookup, mesh_lookup, head, "HeadGeom", "head_bark", translation=(0.0, 0.12, 0.0))
    attach_mesh(nodes, node_lookup, mesh_lookup, head, "EyeL_Geom", "eye_glow", translation=(-0.10, 0.10, 0.22), scale=(0.78, 0.90, 1.0))
    attach_mesh(nodes, node_lookup, mesh_lookup, head, "EyeR_Geom", "eye_glow", translation=(0.10, 0.10, 0.22), scale=(0.78, 0.90, 1.0))
    horn_l = add_node(nodes, node_lookup, "Horn_L", translation=(-0.18, 0.32, -0.02), rotation=quat_from_euler_xyz(-6.0, 6.0, -18.0))
    horn_r = add_node(nodes, node_lookup, "Horn_R", translation=(0.18, 0.32, -0.02), rotation=quat_from_euler_xyz(-6.0, -6.0, 18.0))
    link_child(nodes, head, horn_l)
    link_child(nodes, head, horn_r)
    attach_mesh(nodes, node_lookup, mesh_lookup, horn_l, "HornL_Geom", "horn_bark", scale=(0.56, 0.82, 0.56))
    attach_mesh(nodes, node_lookup, mesh_lookup, horn_r, "HornR_Geom", "horn_bark", scale=(0.56, 0.82, 0.56))

    arm_l = add_node(nodes, node_lookup, "Arm_L", translation=(-0.48, 0.28, 0.04), rotation=quat_from_euler_xyz(4.0, 6.0, 26.0))
    arm_r = add_node(nodes, node_lookup, "Arm_R", translation=(0.48, 0.28, 0.04), rotation=quat_from_euler_xyz(4.0, -6.0, -26.0))
    link_child(nodes, spine_high, arm_l)
    link_child(nodes, spine_high, arm_r)
    attach_mesh(nodes, node_lookup, mesh_lookup, arm_l, "UpperArmL_Geom", "upper_arm_bark", translation=(0.0, -0.34, 0.0))
    attach_mesh(nodes, node_lookup, mesh_lookup, arm_r, "UpperArmR_Geom", "upper_arm_bark", translation=(0.0, -0.34, 0.0))

    forearm_l = add_node(nodes, node_lookup, "Forearm_L", translation=(0.0, -0.64, 0.08), rotation=quat_from_euler_xyz(10.0, 0.0, 0.0))
    forearm_r = add_node(nodes, node_lookup, "Forearm_R", translation=(0.0, -0.64, 0.08), rotation=quat_from_euler_xyz(10.0, 0.0, 0.0))
    link_child(nodes, arm_l, forearm_l)
    link_child(nodes, arm_r, forearm_r)
    attach_mesh(nodes, node_lookup, mesh_lookup, forearm_l, "ForearmL_Geom", "forearm_bark", translation=(0.0, -0.30, 0.04))
    attach_mesh(nodes, node_lookup, mesh_lookup, forearm_r, "ForearmR_Geom", "forearm_bark", translation=(0.0, -0.30, 0.04))

    hand_l = add_node(nodes, node_lookup, "Hand_L", translation=(0.0, -0.60, 0.12), rotation=quat_from_euler_xyz(-6.0, 0.0, 0.0))
    hand_r = add_node(nodes, node_lookup, "Hand_R", translation=(0.0, -0.60, 0.12), rotation=quat_from_euler_xyz(-6.0, 0.0, 0.0))
    link_child(nodes, forearm_l, hand_l)
    link_child(nodes, forearm_r, hand_r)
    attach_mesh(nodes, node_lookup, mesh_lookup, hand_l, "HandL_Geom", "claw_hand_bark")
    attach_mesh(nodes, node_lookup, mesh_lookup, hand_r, "HandR_Geom", "claw_hand_bark")

    leg_l = add_node(nodes, node_lookup, "Leg_L", translation=(-0.24, -0.02, 0.02), rotation=quat_from_euler_xyz(-2.0, 0.0, 2.0))
    leg_r = add_node(nodes, node_lookup, "Leg_R", translation=(0.24, -0.02, 0.02), rotation=quat_from_euler_xyz(-2.0, 0.0, -2.0))
    link_child(nodes, hips, leg_l)
    link_child(nodes, hips, leg_r)
    attach_mesh(nodes, node_lookup, mesh_lookup, leg_l, "ThighL_Geom", "thigh_bark", translation=(0.0, -0.38, 0.0))
    attach_mesh(nodes, node_lookup, mesh_lookup, leg_r, "ThighR_Geom", "thigh_bark", translation=(0.0, -0.38, 0.0))

    shin_l = add_node(nodes, node_lookup, "Shin_L", translation=(0.0, -0.74, 0.10), rotation=quat_from_euler_xyz(10.0, 0.0, 0.0))
    shin_r = add_node(nodes, node_lookup, "Shin_R", translation=(0.0, -0.74, 0.10), rotation=quat_from_euler_xyz(10.0, 0.0, 0.0))
    link_child(nodes, leg_l, shin_l)
    link_child(nodes, leg_r, shin_r)
    attach_mesh(nodes, node_lookup, mesh_lookup, shin_l, "ShinL_Geom", "shin_bark", translation=(0.0, -0.34, 0.02))
    attach_mesh(nodes, node_lookup, mesh_lookup, shin_r, "ShinR_Geom", "shin_bark", translation=(0.0, -0.34, 0.02))

    foot_l = add_node(nodes, node_lookup, "Foot_L", translation=(0.0, -0.64, 0.12), rotation=quat_from_euler_xyz(-8.0, 0.0, 0.0))
    foot_r = add_node(nodes, node_lookup, "Foot_R", translation=(0.0, -0.64, 0.12), rotation=quat_from_euler_xyz(-8.0, 0.0, 0.0))
    link_child(nodes, shin_l, foot_l)
    link_child(nodes, shin_r, foot_r)
    attach_mesh(nodes, node_lookup, mesh_lookup, foot_l, "FootL_Geom", "foot_bark")
    attach_mesh(nodes, node_lookup, mesh_lookup, foot_r, "FootR_Geom", "foot_bark")

    return nodes, node_lookup, root


def build_animations(node_lookup):
    base_translation = {
        "EnemyRoot": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "Hips": np.array([0.0, 1.08, 0.0], dtype=np.float64),
    }
    base_euler = {
        "EnemyRoot": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "Hips": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "SpineLow": np.array([8.0, 0.0, 0.0], dtype=np.float64),
        "SpineHigh": np.array([6.0, 0.0, 0.0], dtype=np.float64),
        "Neck": np.array([-4.0, 0.0, 0.0], dtype=np.float64),
        "Head": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "Horn_L": np.array([-6.0, 6.0, -18.0], dtype=np.float64),
        "Horn_R": np.array([-6.0, -6.0, 18.0], dtype=np.float64),
        "Arm_L": np.array([4.0, 6.0, 26.0], dtype=np.float64),
        "Forearm_L": np.array([10.0, 0.0, 0.0], dtype=np.float64),
        "Hand_L": np.array([-6.0, 0.0, 0.0], dtype=np.float64),
        "Arm_R": np.array([4.0, -6.0, -26.0], dtype=np.float64),
        "Forearm_R": np.array([10.0, 0.0, 0.0], dtype=np.float64),
        "Hand_R": np.array([-6.0, 0.0, 0.0], dtype=np.float64),
        "Leg_L": np.array([-2.0, 0.0, 2.0], dtype=np.float64),
        "Shin_L": np.array([10.0, 0.0, 0.0], dtype=np.float64),
        "Foot_L": np.array([-8.0, 0.0, 0.0], dtype=np.float64),
        "Leg_R": np.array([-2.0, 0.0, -2.0], dtype=np.float64),
        "Shin_R": np.array([10.0, 0.0, 0.0], dtype=np.float64),
        "Foot_R": np.array([-8.0, 0.0, 0.0], dtype=np.float64),
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
        rot_track("SpineLow", [0.0, 0.7, 1.4], [(0.0, -2.0, 0.0), (4.0, 2.0, 0.0), (0.0, -2.0, 0.0)]),
        rot_track("SpineHigh", [0.0, 0.7, 1.4], [(0.0, 3.0, 0.0), (4.0, -3.0, 0.0), (0.0, 3.0, 0.0)]),
        rot_track("Head", [0.0, 0.7, 1.4], [(0.0, -4.0, 0.0), (0.0, 5.0, 0.0), (0.0, -4.0, 0.0)]),
        rot_track("Arm_L", [0.0, 0.7, 1.4], [(6.0, 0.0, -2.0), (0.0, 0.0, 2.0), (6.0, 0.0, -2.0)]),
        rot_track("Forearm_L", [0.0, 0.7, 1.4], [(4.0, 0.0, 0.0), (0.0, 0.0, 0.0), (4.0, 0.0, 0.0)]),
        rot_track("Arm_R", [0.0, 0.7, 1.4], [(6.0, 0.0, 2.0), (0.0, 0.0, -2.0), (6.0, 0.0, 2.0)]),
        rot_track("Forearm_R", [0.0, 0.7, 1.4], [(4.0, 0.0, 0.0), (0.0, 0.0, 0.0), (4.0, 0.0, 0.0)]),
    ]})

    common_walk_times = [0.0, 0.25, 0.5, 0.75, 1.0]
    clips.append({"name": "Walk", "tracks": [
        trans_track("Hips", common_walk_times, [(0.0, 0.00, 0.0), (0.0, -0.04, 0.0), (0.0, 0.01, 0.0), (0.0, -0.04, 0.0), (0.0, 0.00, 0.0)]),
        rot_track("SpineLow", common_walk_times, [(0.0, 0.0, 3.0), (0.0, 0.0, -3.0), (0.0, 0.0, 3.0), (0.0, 0.0, -3.0), (0.0, 0.0, 3.0)]),
        rot_track("SpineHigh", common_walk_times, [(2.0, 2.0, 2.0), (-2.0, -2.0, -2.0), (2.0, 2.0, 2.0), (-2.0, -2.0, -2.0), (2.0, 2.0, 2.0)]),
        rot_track("Head", common_walk_times, [(0.0, 2.0, 2.0), (0.0, -2.0, -2.0), (0.0, 2.0, 2.0), (0.0, -2.0, -2.0), (0.0, 2.0, 2.0)]),
        rot_track("Arm_L", common_walk_times, [(22.0, 0.0, -8.0), (-18.0, 0.0, 4.0), (22.0, 0.0, -8.0), (-18.0, 0.0, 4.0), (22.0, 0.0, -8.0)]),
        rot_track("Forearm_L", common_walk_times, [(8.0, 0.0, 0.0), (-6.0, 0.0, 0.0), (8.0, 0.0, 0.0), (-6.0, 0.0, 0.0), (8.0, 0.0, 0.0)]),
        rot_track("Hand_L", common_walk_times, [(8.0, 0.0, 0.0), (-4.0, 0.0, 0.0), (8.0, 0.0, 0.0), (-4.0, 0.0, 0.0), (8.0, 0.0, 0.0)]),
        rot_track("Arm_R", common_walk_times, [(-18.0, 0.0, 4.0), (22.0, 0.0, -8.0), (-18.0, 0.0, 4.0), (22.0, 0.0, -8.0), (-18.0, 0.0, 4.0)]),
        rot_track("Forearm_R", common_walk_times, [(-6.0, 0.0, 0.0), (8.0, 0.0, 0.0), (-6.0, 0.0, 0.0), (8.0, 0.0, 0.0), (-6.0, 0.0, 0.0)]),
        rot_track("Hand_R", common_walk_times, [(-4.0, 0.0, 0.0), (8.0, 0.0, 0.0), (-4.0, 0.0, 0.0), (8.0, 0.0, 0.0), (-4.0, 0.0, 0.0)]),
        rot_track("Leg_L", common_walk_times, [(-20.0, 0.0, 0.0), (18.0, 0.0, 0.0), (-20.0, 0.0, 0.0), (18.0, 0.0, 0.0), (-20.0, 0.0, 0.0)]),
        rot_track("Shin_L", common_walk_times, [(6.0, 0.0, 0.0), (18.0, 0.0, 0.0), (2.0, 0.0, 0.0), (18.0, 0.0, 0.0), (6.0, 0.0, 0.0)]),
        rot_track("Foot_L", common_walk_times, [(6.0, 0.0, 0.0), (-8.0, 0.0, 0.0), (6.0, 0.0, 0.0), (-8.0, 0.0, 0.0), (6.0, 0.0, 0.0)]),
        rot_track("Leg_R", common_walk_times, [(18.0, 0.0, 0.0), (-20.0, 0.0, 0.0), (18.0, 0.0, 0.0), (-20.0, 0.0, 0.0), (18.0, 0.0, 0.0)]),
        rot_track("Shin_R", common_walk_times, [(18.0, 0.0, 0.0), (6.0, 0.0, 0.0), (18.0, 0.0, 0.0), (2.0, 0.0, 0.0), (18.0, 0.0, 0.0)]),
        rot_track("Foot_R", common_walk_times, [(-8.0, 0.0, 0.0), (6.0, 0.0, 0.0), (-8.0, 0.0, 0.0), (6.0, 0.0, 0.0), (-8.0, 0.0, 0.0)]),
    ]})

    run_times = [0.0, 0.175, 0.35, 0.525, 0.7]
    clips.append({"name": "Run", "tracks": [
        trans_track("Hips", run_times, [(0.0, -0.04, 0.0), (0.0, 0.02, 0.0), (0.0, -0.04, 0.0), (0.0, 0.02, 0.0), (0.0, -0.04, 0.0)]),
        rot_track("SpineLow", run_times, [(10.0, 0.0, 5.0), (12.0, 0.0, -5.0), (10.0, 0.0, 5.0), (12.0, 0.0, -5.0), (10.0, 0.0, 5.0)]),
        rot_track("SpineHigh", run_times, [(8.0, 4.0, 4.0), (12.0, -4.0, -4.0), (8.0, 4.0, 4.0), (12.0, -4.0, -4.0), (8.0, 4.0, 4.0)]),
        rot_track("Head", run_times, [(-6.0, 5.0, 0.0), (-4.0, -5.0, 0.0), (-6.0, 5.0, 0.0), (-4.0, -5.0, 0.0), (-6.0, 5.0, 0.0)]),
        rot_track("Arm_L", run_times, [(38.0, 0.0, -10.0), (-34.0, 0.0, 8.0), (38.0, 0.0, -10.0), (-34.0, 0.0, 8.0), (38.0, 0.0, -10.0)]),
        rot_track("Forearm_L", run_times, [(16.0, 0.0, 0.0), (-10.0, 0.0, 0.0), (16.0, 0.0, 0.0), (-10.0, 0.0, 0.0), (16.0, 0.0, 0.0)]),
        rot_track("Hand_L", run_times, [(12.0, 0.0, 0.0), (-8.0, 0.0, 0.0), (12.0, 0.0, 0.0), (-8.0, 0.0, 0.0), (12.0, 0.0, 0.0)]),
        rot_track("Arm_R", run_times, [(-34.0, 0.0, 8.0), (38.0, 0.0, -10.0), (-34.0, 0.0, 8.0), (38.0, 0.0, -10.0), (-34.0, 0.0, 8.0)]),
        rot_track("Forearm_R", run_times, [(-10.0, 0.0, 0.0), (16.0, 0.0, 0.0), (-10.0, 0.0, 0.0), (16.0, 0.0, 0.0), (-10.0, 0.0, 0.0)]),
        rot_track("Hand_R", run_times, [(-8.0, 0.0, 0.0), (12.0, 0.0, 0.0), (-8.0, 0.0, 0.0), (12.0, 0.0, 0.0), (-8.0, 0.0, 0.0)]),
        rot_track("Leg_L", run_times, [(-32.0, 0.0, 0.0), (36.0, 0.0, 0.0), (-32.0, 0.0, 0.0), (36.0, 0.0, 0.0), (-32.0, 0.0, 0.0)]),
        rot_track("Shin_L", run_times, [(6.0, 0.0, 0.0), (28.0, 0.0, 0.0), (0.0, 0.0, 0.0), (28.0, 0.0, 0.0), (6.0, 0.0, 0.0)]),
        rot_track("Foot_L", run_times, [(10.0, 0.0, 0.0), (-12.0, 0.0, 0.0), (10.0, 0.0, 0.0), (-12.0, 0.0, 0.0), (10.0, 0.0, 0.0)]),
        rot_track("Leg_R", run_times, [(36.0, 0.0, 0.0), (-32.0, 0.0, 0.0), (36.0, 0.0, 0.0), (-32.0, 0.0, 0.0), (36.0, 0.0, 0.0)]),
        rot_track("Shin_R", run_times, [(28.0, 0.0, 0.0), (6.0, 0.0, 0.0), (28.0, 0.0, 0.0), (0.0, 0.0, 0.0), (28.0, 0.0, 0.0)]),
        rot_track("Foot_R", run_times, [(-12.0, 0.0, 0.0), (10.0, 0.0, 0.0), (-12.0, 0.0, 0.0), (10.0, 0.0, 0.0), (-12.0, 0.0, 0.0)]),
    ]})

    clips.append({"name": "Attack", "tracks": [
        trans_track("Hips", [0.0, 0.18, 0.42, 0.72, 0.96], [(0.0, 0.0, 0.0), (0.0, -0.06, 0.0), (0.0, 0.02, 0.0), (0.0, -0.01, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("Hips", [0.0, 0.18, 0.42, 0.72, 0.96], [(0.0, 0.0, 0.0), (0.0, -14.0, 0.0), (0.0, 12.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("SpineLow", [0.0, 0.18, 0.42, 0.72, 0.96], [(0.0, 0.0, 0.0), (8.0, -20.0, 0.0), (-8.0, 30.0, -6.0), (-2.0, 8.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("SpineHigh", [0.0, 0.18, 0.42, 0.72, 0.96], [(0.0, 0.0, 0.0), (6.0, -26.0, 0.0), (-14.0, 34.0, -8.0), (-4.0, 12.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("Head", [0.0, 0.18, 0.42, 0.72, 0.96], [(0.0, 0.0, 0.0), (0.0, -18.0, 0.0), (0.0, 18.0, 0.0), (0.0, 6.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("Arm_R", [0.0, 0.18, 0.42, 0.72, 0.96], [(6.0, 0.0, 0.0), (-68.0, 0.0, 12.0), (98.0, 0.0, -18.0), (18.0, 0.0, 0.0), (6.0, 0.0, 0.0)]),
        rot_track("Forearm_R", [0.0, 0.18, 0.42, 0.72, 0.96], [(6.0, 0.0, 0.0), (-48.0, 0.0, 0.0), (42.0, 0.0, 0.0), (8.0, 0.0, 0.0), (6.0, 0.0, 0.0)]),
        rot_track("Hand_R", [0.0, 0.18, 0.42, 0.72, 0.96], [(0.0, 0.0, 0.0), (-18.0, 0.0, 0.0), (24.0, 0.0, 0.0), (6.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("Arm_L", [0.0, 0.18, 0.42, 0.72, 0.96], [(0.0, 0.0, 0.0), (18.0, 0.0, 10.0), (-8.0, 0.0, -6.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("Forearm_L", [0.0, 0.18, 0.42, 0.72, 0.96], [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (-6.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("Leg_L", [0.0, 0.18, 0.42, 0.72, 0.96], [(0.0, 0.0, 0.0), (-12.0, 0.0, 0.0), (8.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("Leg_R", [0.0, 0.18, 0.42, 0.72, 0.96], [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (-8.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
    ]})

    clips.append({"name": "Hit", "tracks": [
        trans_track("Hips", [0.0, 0.12, 0.30, 0.48], [(0.0, 0.0, 0.0), (0.0, 0.03, -0.04), (0.0, -0.02, 0.01), (0.0, 0.0, 0.0)]),
        rot_track("SpineLow", [0.0, 0.12, 0.30, 0.48], [(0.0, 0.0, 0.0), (-22.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("SpineHigh", [0.0, 0.12, 0.30, 0.48], [(0.0, 0.0, 0.0), (-28.0, 0.0, 0.0), (14.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("Head", [0.0, 0.12, 0.30, 0.48], [(0.0, 0.0, 0.0), (-22.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("Arm_L", [0.0, 0.12, 0.30, 0.48], [(0.0, 0.0, 0.0), (18.0, 0.0, 10.0), (-4.0, 0.0, -2.0), (0.0, 0.0, 0.0)]),
        rot_track("Arm_R", [0.0, 0.12, 0.30, 0.48], [(0.0, 0.0, 0.0), (18.0, 0.0, -10.0), (-4.0, 0.0, 2.0), (0.0, 0.0, 0.0)]),
        rot_track("Forearm_L", [0.0, 0.12, 0.30, 0.48], [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (-4.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
        rot_track("Forearm_R", [0.0, 0.12, 0.30, 0.48], [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (-4.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
    ]})

    clips.append({"name": "Death", "tracks": [
        trans_track("EnemyRoot", [0.0, 0.28, 0.72, 1.18, 1.54], [(0.0, 0.0, 0.0), (0.0, 0.02, 0.0), (0.08, 0.04, 0.0), (0.20, 0.05, 0.0), (0.20, 0.05, 0.0)]),
        rot_track("EnemyRoot", [0.0, 0.28, 0.72, 1.18, 1.54], [(0.0, 0.0, 0.0), (0.0, 0.0, 12.0), (0.0, 0.0, 48.0), (0.0, 0.0, 90.0), (0.0, 0.0, 96.0)]),
        trans_track("Hips", [0.0, 0.28, 0.72, 1.18, 1.54], [(0.0, 0.0, 0.0), (0.0, -0.05, 0.0), (0.0, -0.28, 0.0), (0.0, -0.46, 0.0), (0.0, -0.48, 0.0)]),
        rot_track("SpineLow", [0.0, 0.28, 0.72, 1.18, 1.54], [(0.0, 0.0, 0.0), (12.0, -8.0, 0.0), (34.0, -10.0, -6.0), (76.0, 0.0, -14.0), (84.0, 0.0, -16.0)]),
        rot_track("SpineHigh", [0.0, 0.28, 0.72, 1.18, 1.54], [(0.0, 0.0, 0.0), (12.0, -6.0, 0.0), (32.0, -8.0, -8.0), (70.0, 0.0, -12.0), (76.0, 0.0, -12.0)]),
        rot_track("Head", [0.0, 0.28, 0.72, 1.18, 1.54], [(0.0, 0.0, 0.0), (8.0, 0.0, 0.0), (26.0, 6.0, -6.0), (50.0, 0.0, -10.0), (56.0, 0.0, -10.0)]),
        rot_track("Arm_L", [0.0, 0.28, 0.72, 1.18, 1.54], [(0.0, 0.0, 0.0), (24.0, 0.0, 18.0), (64.0, 0.0, 38.0), (102.0, 0.0, 28.0), (108.0, 0.0, 28.0)]),
        rot_track("Forearm_L", [0.0, 0.28, 0.72, 1.18, 1.54], [(0.0, 0.0, 0.0), (18.0, 0.0, 0.0), (38.0, 0.0, 0.0), (56.0, 0.0, 0.0), (60.0, 0.0, 0.0)]),
        rot_track("Arm_R", [0.0, 0.28, 0.72, 1.18, 1.54], [(0.0, 0.0, 0.0), (18.0, 0.0, -18.0), (42.0, 0.0, -34.0), (84.0, 0.0, -24.0), (90.0, 0.0, -24.0)]),
        rot_track("Forearm_R", [0.0, 0.28, 0.72, 1.18, 1.54], [(0.0, 0.0, 0.0), (14.0, 0.0, 0.0), (34.0, 0.0, 0.0), (52.0, 0.0, 0.0), (56.0, 0.0, 0.0)]),
        rot_track("Leg_L", [0.0, 0.28, 0.72, 1.18, 1.54], [(0.0, 0.0, 0.0), (-10.0, 0.0, 10.0), (14.0, 0.0, 24.0), (40.0, 0.0, 12.0), (40.0, 0.0, 12.0)]),
        rot_track("Shin_L", [0.0, 0.28, 0.72, 1.18, 1.54], [(0.0, 0.0, 0.0), (12.0, 0.0, 0.0), (30.0, 0.0, 0.0), (48.0, 0.0, 0.0), (48.0, 0.0, 0.0)]),
        rot_track("Leg_R", [0.0, 0.28, 0.72, 1.18, 1.54], [(0.0, 0.0, 0.0), (-12.0, 0.0, -10.0), (10.0, 0.0, -24.0), (34.0, 0.0, -12.0), (34.0, 0.0, -12.0)]),
        rot_track("Shin_R", [0.0, 0.28, 0.72, 1.18, 1.54], [(0.0, 0.0, 0.0), (14.0, 0.0, 0.0), (30.0, 0.0, 0.0), (42.0, 0.0, 0.0), (42.0, 0.0, 0.0)]),
    ]})
    return clips


def prepare_textures(output_dir):
    bark_path = output_dir / "enemy03_bark.png"
    moss_path = output_dir / "enemy03_moss.png"
    bark_written = False
    if SOURCE_FBX.exists():
        data = SOURCE_FBX.read_bytes()
        start = data.find(b"\x89PNG\r\n\x1a\n")
        end_marker = b"IEND\xaeB`\x82"
        end = data.find(end_marker, start)
        if start >= 0 and end >= 0:
            bark_path.write_bytes(data[start : end + len(end_marker)])
            bark_written = True
    if not bark_written:
        bark = Image.new("RGBA", (512, 512), (78, 55, 34, 255))
        draw = ImageDraw.Draw(bark)
        for y in range(0, 512, 8):
            shade = 45 + (y % 48)
            draw.line([(0, y), (511, y + 6)], fill=(shade + 40, shade + 18, shade, 255), width=3)
        for x in range(0, 512, 32):
            draw.line([(x, 0), (x + 18, 511)], fill=(42, 26, 17, 255), width=5)
        bark = bark.filter(ImageFilter.GaussianBlur(0.7))
        bark.save(bark_path)

    bark = Image.open(bark_path).convert("RGBA")
    moss = bark.copy()
    arr = np.array(moss, dtype=np.uint8)
    arr[..., 0] = (arr[..., 0] * 0.45).astype(np.uint8)
    arr[..., 1] = np.clip(arr[..., 1] * 0.95 + 36, 0, 255).astype(np.uint8)
    arr[..., 2] = (arr[..., 2] * 0.35).astype(np.uint8)
    moss = Image.fromarray(arr, "RGBA").filter(ImageFilter.GaussianBlur(0.8))
    ImageDraw.Draw(moss).ellipse((110, 110, 230, 230), fill=(85, 120, 52, 90))
    ImageDraw.Draw(moss).ellipse((280, 180, 400, 320), fill=(70, 108, 44, 86))
    moss.save(moss_path)
    return bark_path, moss_path


def build_gltf(output_dir):
    bark_path, moss_path = prepare_textures(output_dir)
    meshes_geo = build_mesh_library()
    builder = BufferBuilder()
    mesh_defs = []
    mesh_lookup = {}

    materials = [
        {"name": "Bark", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0, "roughnessFactor": 1.0}},
        {"name": "Moss", "pbrMetallicRoughness": {"baseColorTexture": {"index": 1}, "baseColorFactor": [0.92, 1.0, 0.92, 1.0], "metallicFactor": 0.0, "roughnessFactor": 0.96}},
        {"name": "Eyes", "pbrMetallicRoughness": {"baseColorFactor": [0.96, 0.20, 0.10, 1.0], "metallicFactor": 0.0, "roughnessFactor": 0.18}, "emissiveFactor": [1.0, 0.24, 0.12]},
    ]

    material_for_mesh = {"moss_patch": 1, "eye_glow": 2}
    for name, geo in meshes_geo.items():
        pos = builder.add_accessor(geo["positions"], FLOAT, "VEC3", target=ARRAY_BUFFER)
        norm = builder.add_accessor(geo["normals"], FLOAT, "VEC3", target=ARRAY_BUFFER)
        uv = builder.add_accessor(geo["uvs"], FLOAT, "VEC2", target=ARRAY_BUFFER)
        idx = builder.add_accessor(geo["indices"], UNSIGNED_SHORT, "SCALAR", target=ELEMENT_ARRAY_BUFFER)
        mesh_lookup[name] = len(mesh_defs)
        mesh_defs.append({"name": name, "primitives": [{"attributes": {"POSITION": pos, "NORMAL": norm, "TEXCOORD_0": uv}, "indices": idx, "material": material_for_mesh.get(name, 0)}]})

    nodes, node_lookup, root = build_enemy_structure(mesh_lookup)
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
        "asset": {"version": "2.0", "generator": "Codex Enemy03 Detailed Tree Guardian Generator"},
        "scene": 0,
        "scenes": [{"name": "Enemy03Scene", "nodes": [root]}],
        "nodes": nodes,
        "meshes": mesh_defs,
        "materials": materials,
        "images": [{"uri": bark_path.name}, {"uri": moss_path.name}],
        "textures": [{"sampler": 0, "source": 0}, {"sampler": 0, "source": 1}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}],
        "animations": animations,
        "bufferViews": builder.buffer_views,
        "accessors": builder.accessors,
        "buffers": [{"byteLength": len(builder.data), "uri": "data:application/octet-stream;base64," + base64.b64encode(builder.data).decode("ascii")}],
    }
    return gltf, mesh_lookup


def write_readme(output_dir, gltf_name, glb_name):
    readme = f"""# 敌人03 详细说明

## 1. 资源定位

`敌人03` 是一个比 `敌人02` 更接近 `敌人01-树妖.fbx` 视觉方向的树妖敌人资源。

这一版的设计目标不是“极简低模原型”，而是“适合网页端、但外形已经更像成品怪物”的树妖敌人：

- 轮廓更接近树干、树枝、枯木、苔藓覆盖的树妖
- 局部细节比 `敌人02` 更丰富，包括肩刺、背刺、爪子、树根脚部和头部角状结构
- 继续保留网页端友好的资源体积和状态机接入方式
- 动画仍然提供 `Idle / Walk / Run / Attack / Hit / Death`

## 2. 与 敌人02 的差异

相对于 `敌人02`，这一版的提升点主要在于：

- 造型更复杂，不再只是简单方块拼接
- 身体主要由不规则树干截面、尖刺和树根结构构成
- 增加了 bark 纹理贴图，视觉更接近原始树妖
- 胸口、肩部加入苔藓块，头部加入更明显的树妖五官轮廓
- 四肢和手爪更像“枝杈怪物”而不是人形方块人

## 3. 资源文件

- `{gltf_name}`: 文本版 glTF 主文件
- `{glb_name}`: 二进制版 glTF 模型
- `enemy03_bark.png`: 树皮纹理
- `enemy03_moss.png`: 苔藓纹理
- `enemy03_preview.png`: 静态预览图
- `enemy03_meta.json`: 元信息
- `generate_enemy03.py`: 生成脚本

## 4. 动画

- `Idle`: 站立待机
- `Walk`: 慢速移动
- `Run`: 高速追击
- `Attack`: 近战挥击
- `Hit`: 受击反馈
- `Death`: 倒地死亡

## 5. 使用建议

- 网页项目优先使用 `{glb_name}` 或 `{gltf_name}`
- `Walk` / `Run` 是原地动作，位移由游戏逻辑控制
- `Attack` / `Hit` / `Death` 建议作为单次动作播放
- 推荐用胶囊体做主碰撞、攻击盒做命中检测

## 6. 材质说明

- `Bark`: 身体主体使用树皮纹理
- `Moss`: 苔藓覆盖物
- `Eyes`: 发光眼睛材质

`enemy03_bark.png` 会优先尝试从 `敌人01-树妖.fbx` 中提取，因此风格会更接近原始树妖。

## 7. 重新生成

```bash
python3 generate_enemy03.py
```
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def render_preview(output_dir, mesh_lookup, nodes):
    bark_color = np.array([109, 72, 39], dtype=np.float64)
    moss_color = np.array([78, 118, 54], dtype=np.float64)
    eye_color = np.array([236, 56, 28], dtype=np.float64)
    color_by_mesh = {}
    for name, mesh_index in mesh_lookup.items():
        color_by_mesh[mesh_index] = moss_color if name == "moss_patch" else eye_color if name == "eye_glow" else bark_color

    mesh_geo = build_mesh_library()
    mesh_geo_by_index = {mesh_lookup[name]: geo for name, geo in mesh_geo.items()}
    children = {idx: node.get("children", []) for idx, node in enumerate(nodes)}
    world = {}

    def traverse(idx, parent_t=None, parent_q=None, parent_s=None):
        parent_t = np.zeros(3, dtype=np.float64) if parent_t is None else parent_t
        parent_q = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64) if parent_q is None else parent_q
        parent_s = np.ones(3, dtype=np.float64) if parent_s is None else parent_s
        node = nodes[idx]
        t = np.array(node.get("translation", [0.0, 0.0, 0.0]), dtype=np.float64)
        r = np.array(node.get("rotation", [0.0, 0.0, 0.0, 1.0]), dtype=np.float64)
        s = np.array(node.get("scale", [1.0, 1.0, 1.0]), dtype=np.float64)
        wt = parent_t + rotate_vector(parent_q, parent_s * t)
        wq = normalize_quat(quat_mul(parent_q, r))
        ws = parent_s * s
        world[idx] = (wt, wq, ws)
        for child in children.get(idx, []):
            traverse(child, wt, wq, ws)

    traverse(0)
    triangles = []
    for idx, node in enumerate(nodes):
        if "mesh" not in node:
            continue
        geo = mesh_geo_by_index[node["mesh"]]
        wt, wq, ws = world[idx]
        verts = np.array([rotate_vector(wq, np.asarray(pos, dtype=np.float64) * ws) + wt for pos in geo["positions"]], dtype=np.float64)
        for tri in geo["indices"].reshape(-1, 3):
            triangles.append((verts[tri], color_by_mesh[node["mesh"]]))

    points = np.concatenate([tri[0] for tri in triangles], axis=0)
    center = (points.min(axis=0) + points.max(axis=0)) * 0.5

    def rotation_matrix(yaw_deg, pitch_deg):
        yaw = math.radians(yaw_deg)
        pitch = math.radians(pitch_deg)
        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        return np.array([[cy, sy * sp, sy * cp], [0.0, cp, -sp], [-sy, cy * sp, cy * cp]], dtype=np.float64)

    views = [("Front", 10.0, -8.0), ("3/4", 42.0, -12.0)]
    width = 460
    height = 440
    image = Image.new("RGB", (width * len(views), height), (242, 235, 220))
    light = np.array([0.4, -0.6, 0.7], dtype=np.float64)
    light /= np.linalg.norm(light)

    for view_index, (label, yaw, pitch) in enumerate(views):
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle([view_index * width + 8, 8, (view_index + 1) * width - 8, height - 8], radius=20, fill=(248, 243, 234), outline=(196, 181, 156), width=2)
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
        scale = (min(width, height) - 76) / span

        draw_items = []
        for points_3d, color in transformed:
            normal = np.cross(points_3d[1] - points_3d[0], points_3d[2] - points_3d[0])
            normal = normal / (np.linalg.norm(normal) or 1.0)
            shade = max(0.20, float(normal @ light))
            shaded = np.clip(color * (0.56 + 0.54 * shade), 0, 255).astype(int)
            polygon = []
            for x, y, z in points_3d:
                sx = (x - (minimum[0] + maximum[0]) * 0.5) * scale + width * 0.5 + view_index * width
                sy = height * 0.55 - (y - (minimum[1] + maximum[1]) * 0.5) * scale
                polygon.append((sx, sy))
            draw_items.append((points_3d[:, 2].mean(), tuple(shaded.tolist()), polygon))
        draw_items.sort(key=lambda item: item[0])
        for _, fill, polygon in draw_items:
            draw.polygon(polygon, fill=fill)
        draw.text((view_index * width + 18, 16), label, fill=(88, 70, 54))

    image.save(output_dir / "enemy03_preview.png")


def main():
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    gltf, mesh_lookup = build_gltf(output_dir)
    gltf_path = output_dir / "model.gltf"
    gltf_path.write_text(json.dumps(gltf, ensure_ascii=False, indent=2), encoding="utf-8")

    glb_path = output_dir / "model.glb"
    try:
        from pygltflib import GLTF2

        model = GLTF2().load(str(gltf_path))
        model.save_binary(str(glb_path))
    except Exception as exc:
        glb_path.write_text(f"GLB export failed.\nReason: {exc}\nUse the glTF file instead.\n", encoding="utf-8")

    render_preview(output_dir, mesh_lookup, gltf["nodes"])
    write_readme(output_dir, gltf_path.name, glb_path.name)
    meta = {
        "name": "Enemy03 Tree Guardian",
        "style": "detailed_tree_monster",
        "approx_height_m": 2.7,
        "formats": ["gltf", "glb"],
        "textures": ["enemy03_bark.png", "enemy03_moss.png"],
        "animations": ["Idle", "Walk", "Run", "Attack", "Hit", "Death"],
    }
    (output_dir / "enemy03_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(gltf_path)
    print(glb_path)
    print(output_dir / "README.md")


if __name__ == "__main__":
    main()
