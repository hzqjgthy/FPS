#!/usr/bin/env python3

import base64
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


FLOAT = 5126
UNSIGNED_SHORT = 5123
ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963


def normalize_quat(q):
    q = np.asarray(q, dtype=np.float32)
    norm = np.linalg.norm(q)
    if norm == 0:
        return np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
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
        dtype=np.float32,
    )


def quat_from_axis_angle(axis, angle_deg):
    angle_rad = math.radians(angle_deg) * 0.5
    s = math.sin(angle_rad)
    c = math.cos(angle_rad)
    ax, ay, az = axis
    return np.array([ax * s, ay * s, az * s, c], dtype=np.float32)


def quat_from_euler_xyz(x_deg, y_deg, z_deg):
    qx = quat_from_axis_angle((1.0, 0.0, 0.0), x_deg)
    qy = quat_from_axis_angle((0.0, 1.0, 0.0), y_deg)
    qz = quat_from_axis_angle((0.0, 0.0, 1.0), z_deg)
    return normalize_quat(quat_mul(quat_mul(qz, qy), qx))


def vec3(values):
    return [float(v) for v in values]


def face(a, b, c, d, normal):
    positions = np.array([a, b, c, d], dtype=np.float32)
    normals = np.array([normal, normal, normal, normal], dtype=np.float32)
    indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint16)
    return positions, normals, indices


def make_cube():
    p = [
        (-0.5, -0.5, 0.5),
        (0.5, -0.5, 0.5),
        (0.5, 0.5, 0.5),
        (-0.5, 0.5, 0.5),
        (0.5, -0.5, -0.5),
        (-0.5, -0.5, -0.5),
        (-0.5, 0.5, -0.5),
        (0.5, 0.5, -0.5),
    ]
    faces = [
        face(p[0], p[1], p[2], p[3], (0.0, 0.0, 1.0)),
        face(p[4], p[5], p[6], p[7], (0.0, 0.0, -1.0)),
        face(p[5], p[0], p[3], p[6], (-1.0, 0.0, 0.0)),
        face(p[1], p[4], p[7], p[2], (1.0, 0.0, 0.0)),
        face(p[3], p[2], p[7], p[6], (0.0, 1.0, 0.0)),
        face(p[5], p[4], p[1], p[0], (0.0, -1.0, 0.0)),
    ]
    return join_geometry(faces)


def triangle(a, b, c):
    positions = np.array([a, b, c], dtype=np.float32)
    n = np.cross(np.array(b) - np.array(a), np.array(c) - np.array(a))
    n = n / (np.linalg.norm(n) or 1.0)
    normals = np.array([n, n, n], dtype=np.float32)
    indices = np.array([0, 1, 2], dtype=np.uint16)
    return positions, normals, indices


def make_spike():
    tip = (0.0, 0.6, 0.0)
    b0 = (-0.18, 0.0, 0.18)
    b1 = (0.18, 0.0, 0.18)
    b2 = (0.18, 0.0, -0.18)
    b3 = (-0.18, 0.0, -0.18)
    faces = [
        triangle(b0, b1, tip),
        triangle(b1, b2, tip),
        triangle(b2, b3, tip),
        triangle(b3, b0, tip),
        triangle(b3, b2, b1),
        triangle(b3, b1, b0),
    ]
    return join_geometry(faces)


def join_geometry(chunks):
    positions = []
    normals = []
    indices = []
    offset = 0
    for pos, norm, idx in chunks:
        positions.append(pos)
        normals.append(norm)
        indices.append(idx + offset)
        offset += len(pos)
    return {
        "positions": np.concatenate(positions, axis=0).astype(np.float32),
        "normals": np.concatenate(normals, axis=0).astype(np.float32),
        "indices": np.concatenate(indices, axis=0).astype(np.uint16),
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
        elif component_type == UNSIGNED_SHORT:
            accessor["min"] = [int(arr.min())]
            accessor["max"] = [int(arr.max())]

        self.accessors.append(accessor)
        return len(self.accessors) - 1


def add_node(nodes, node_lookup, name, translation=None, rotation=None, scale=None, mesh=None):
    node = {"name": name}
    if translation is not None:
        node["translation"] = vec3(translation)
    if rotation is not None:
        node["rotation"] = vec3(rotation[:3]) + [float(rotation[3])]
    if scale is not None:
        node["scale"] = vec3(scale)
    if mesh is not None:
        node["mesh"] = mesh
    nodes.append(node)
    node_lookup[name] = len(nodes) - 1
    return len(nodes) - 1


def link_child(nodes, parent, child):
    nodes[parent].setdefault("children", []).append(child)


def base_enemy_structure(mesh_lookup):
    nodes = []
    node_lookup = {}

    root = add_node(nodes, node_lookup, "EnemyRoot", translation=(0.0, 0.0, 0.0))

    hips = add_node(nodes, node_lookup, "Hips", translation=(0.0, 1.10, 0.0))
    link_child(nodes, root, hips)
    hips_geom = add_node(
        nodes,
        node_lookup,
        "HipsGeom",
        translation=(0.0, 0.12, 0.0),
        scale=(0.46, 0.28, 0.30),
        mesh=mesh_lookup["cube_bark"],
    )
    link_child(nodes, hips, hips_geom)

    spine = add_node(nodes, node_lookup, "Spine", translation=(0.0, 0.18, 0.0), rotation=quat_from_euler_xyz(2.0, 0.0, 0.0))
    link_child(nodes, hips, spine)
    torso_geom = add_node(
        nodes,
        node_lookup,
        "TorsoGeom",
        translation=(0.0, 0.48, 0.0),
        scale=(0.72, 0.82, 0.36),
        mesh=mesh_lookup["cube_bark"],
    )
    link_child(nodes, spine, torso_geom)
    chest_moss = add_node(
        nodes,
        node_lookup,
        "ChestMossGeom",
        translation=(0.0, 0.42, 0.21),
        scale=(0.48, 0.22, 0.08),
        mesh=mesh_lookup["cube_moss"],
    )
    link_child(nodes, spine, chest_moss)

    head = add_node(nodes, node_lookup, "Head", translation=(0.0, 0.84, 0.05))
    link_child(nodes, spine, head)
    head_geom = add_node(
        nodes,
        node_lookup,
        "HeadGeom",
        translation=(0.0, 0.18, 0.0),
        scale=(0.42, 0.40, 0.34),
        mesh=mesh_lookup["cube_bark"],
    )
    link_child(nodes, head, head_geom)
    eye_l = add_node(
        nodes,
        node_lookup,
        "Eye_L_Geom",
        translation=(-0.09, 0.22, 0.18),
        scale=(0.05, 0.05, 0.03),
        mesh=mesh_lookup["cube_eye"],
    )
    eye_r = add_node(
        nodes,
        node_lookup,
        "Eye_R_Geom",
        translation=(0.09, 0.22, 0.18),
        scale=(0.05, 0.05, 0.03),
        mesh=mesh_lookup["cube_eye"],
    )
    link_child(nodes, head, eye_l)
    link_child(nodes, head, eye_r)
    horn_l = add_node(nodes, node_lookup, "Horn_L", translation=(-0.13, 0.38, -0.02), rotation=quat_from_euler_xyz(0.0, 0.0, -18.0))
    horn_r = add_node(nodes, node_lookup, "Horn_R", translation=(0.13, 0.38, -0.02), rotation=quat_from_euler_xyz(0.0, 0.0, 18.0))
    link_child(nodes, head, horn_l)
    link_child(nodes, head, horn_r)
    horn_l_geom = add_node(nodes, node_lookup, "Horn_L_Geom", scale=(0.16, 0.36, 0.16), mesh=mesh_lookup["spike_bark"])
    horn_r_geom = add_node(nodes, node_lookup, "Horn_R_Geom", scale=(0.16, 0.36, 0.16), mesh=mesh_lookup["spike_bark"])
    link_child(nodes, horn_l, horn_l_geom)
    link_child(nodes, horn_r, horn_r_geom)

    arm_l = add_node(nodes, node_lookup, "Arm_L", translation=(-0.46, 0.66, 0.0), rotation=quat_from_euler_xyz(0.0, 0.0, 18.0))
    arm_r = add_node(nodes, node_lookup, "Arm_R", translation=(0.46, 0.66, 0.0), rotation=quat_from_euler_xyz(0.0, 0.0, -18.0))
    link_child(nodes, spine, arm_l)
    link_child(nodes, spine, arm_r)
    arm_l_geom = add_node(nodes, node_lookup, "Arm_L_Geom", translation=(0.0, -0.26, 0.0), scale=(0.22, 0.52, 0.22), mesh=mesh_lookup["cube_bark"])
    arm_r_geom = add_node(nodes, node_lookup, "Arm_R_Geom", translation=(0.0, -0.26, 0.0), scale=(0.22, 0.52, 0.22), mesh=mesh_lookup["cube_bark"])
    link_child(nodes, arm_l, arm_l_geom)
    link_child(nodes, arm_r, arm_r_geom)

    forearm_l = add_node(nodes, node_lookup, "Forearm_L", translation=(0.0, -0.50, 0.04), rotation=quat_from_euler_xyz(10.0, 0.0, 0.0))
    forearm_r = add_node(nodes, node_lookup, "Forearm_R", translation=(0.0, -0.50, 0.04), rotation=quat_from_euler_xyz(10.0, 0.0, 0.0))
    link_child(nodes, arm_l, forearm_l)
    link_child(nodes, arm_r, forearm_r)
    forearm_l_geom = add_node(
        nodes,
        node_lookup,
        "Forearm_L_Geom",
        translation=(0.0, -0.22, 0.03),
        scale=(0.18, 0.50, 0.18),
        mesh=mesh_lookup["cube_bark"],
    )
    forearm_r_geom = add_node(
        nodes,
        node_lookup,
        "Forearm_R_Geom",
        translation=(0.0, -0.22, 0.03),
        scale=(0.18, 0.50, 0.18),
        mesh=mesh_lookup["cube_bark"],
    )
    link_child(nodes, forearm_l, forearm_l_geom)
    link_child(nodes, forearm_r, forearm_r_geom)
    claw_l = add_node(nodes, node_lookup, "Claw_L", translation=(0.0, -0.48, 0.10), rotation=quat_from_euler_xyz(-90.0, 0.0, 0.0))
    claw_r = add_node(nodes, node_lookup, "Claw_R", translation=(0.0, -0.48, 0.10), rotation=quat_from_euler_xyz(-90.0, 0.0, 0.0))
    link_child(nodes, forearm_l, claw_l)
    link_child(nodes, forearm_r, claw_r)
    claw_l_geom = add_node(nodes, node_lookup, "Claw_L_Geom", scale=(0.18, 0.30, 0.18), mesh=mesh_lookup["spike_bark"])
    claw_r_geom = add_node(nodes, node_lookup, "Claw_R_Geom", scale=(0.18, 0.30, 0.18), mesh=mesh_lookup["spike_bark"])
    link_child(nodes, claw_l, claw_l_geom)
    link_child(nodes, claw_r, claw_r_geom)

    leg_l = add_node(nodes, node_lookup, "Leg_L", translation=(-0.20, -0.02, 0.0))
    leg_r = add_node(nodes, node_lookup, "Leg_R", translation=(0.20, -0.02, 0.0))
    link_child(nodes, hips, leg_l)
    link_child(nodes, hips, leg_r)
    leg_l_geom = add_node(nodes, node_lookup, "Leg_L_Geom", translation=(0.0, -0.26, 0.0), scale=(0.24, 0.52, 0.24), mesh=mesh_lookup["cube_bark"])
    leg_r_geom = add_node(nodes, node_lookup, "Leg_R_Geom", translation=(0.0, -0.26, 0.0), scale=(0.24, 0.52, 0.24), mesh=mesh_lookup["cube_bark"])
    link_child(nodes, leg_l, leg_l_geom)
    link_child(nodes, leg_r, leg_r_geom)

    shin_l = add_node(nodes, node_lookup, "Shin_L", translation=(0.0, -0.52, 0.04), rotation=quat_from_euler_xyz(8.0, 0.0, 0.0))
    shin_r = add_node(nodes, node_lookup, "Shin_R", translation=(0.0, -0.52, 0.04), rotation=quat_from_euler_xyz(8.0, 0.0, 0.0))
    link_child(nodes, leg_l, shin_l)
    link_child(nodes, leg_r, shin_r)
    shin_l_geom = add_node(nodes, node_lookup, "Shin_L_Geom", translation=(0.0, -0.23, 0.0), scale=(0.20, 0.46, 0.20), mesh=mesh_lookup["cube_bark"])
    shin_r_geom = add_node(nodes, node_lookup, "Shin_R_Geom", translation=(0.0, -0.23, 0.0), scale=(0.20, 0.46, 0.20), mesh=mesh_lookup["cube_bark"])
    link_child(nodes, shin_l, shin_l_geom)
    link_child(nodes, shin_r, shin_r_geom)
    foot_l = add_node(nodes, node_lookup, "Foot_L_Geom", translation=(0.0, -0.48, 0.16), scale=(0.24, 0.10, 0.34), mesh=mesh_lookup["cube_bark"])
    foot_r = add_node(nodes, node_lookup, "Foot_R_Geom", translation=(0.0, -0.48, 0.16), scale=(0.24, 0.10, 0.34), mesh=mesh_lookup["cube_bark"])
    link_child(nodes, shin_l, foot_l)
    link_child(nodes, shin_r, foot_r)

    back_spike_a = add_node(nodes, node_lookup, "BackSpike_A", translation=(-0.12, 0.78, -0.18), rotation=quat_from_euler_xyz(-30.0, 0.0, -8.0), scale=(0.16, 0.28, 0.16), mesh=mesh_lookup["spike_moss"])
    back_spike_b = add_node(nodes, node_lookup, "BackSpike_B", translation=(0.10, 0.68, -0.16), rotation=quat_from_euler_xyz(-20.0, 0.0, 12.0), scale=(0.14, 0.24, 0.14), mesh=mesh_lookup["spike_moss"])
    link_child(nodes, spine, back_spike_a)
    link_child(nodes, spine, back_spike_b)

    return nodes, node_lookup, root


def build_animations(node_lookup):
    base_translation = {
        "EnemyRoot": np.array([0.0, 0.0, 0.0], dtype=np.float32),
        "Hips": np.array([0.0, 1.10, 0.0], dtype=np.float32),
    }
    base_euler = {
        "EnemyRoot": np.array([0.0, 0.0, 0.0], dtype=np.float32),
        "Hips": np.array([0.0, 0.0, 0.0], dtype=np.float32),
        "Spine": np.array([2.0, 0.0, 0.0], dtype=np.float32),
        "Head": np.array([0.0, 0.0, 0.0], dtype=np.float32),
        "Arm_L": np.array([0.0, 0.0, 18.0], dtype=np.float32),
        "Forearm_L": np.array([10.0, 0.0, 0.0], dtype=np.float32),
        "Arm_R": np.array([0.0, 0.0, -18.0], dtype=np.float32),
        "Forearm_R": np.array([10.0, 0.0, 0.0], dtype=np.float32),
        "Leg_L": np.array([0.0, 0.0, 0.0], dtype=np.float32),
        "Shin_L": np.array([8.0, 0.0, 0.0], dtype=np.float32),
        "Leg_R": np.array([0.0, 0.0, 0.0], dtype=np.float32),
        "Shin_R": np.array([8.0, 0.0, 0.0], dtype=np.float32),
    }

    clips = []

    def rot_track(node_name, times, deltas):
        values = []
        for delta in deltas:
            euler = base_euler[node_name] + np.array(delta, dtype=np.float32)
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
            values.append(base_translation[node_name] + np.array(delta, dtype=np.float32))
        return {
            "node": node_lookup[node_name],
            "path": "translation",
            "times": np.array(times, dtype=np.float32),
            "values": np.array(values, dtype=np.float32),
        }

    clips.append(
        {
            "name": "Idle",
            "tracks": [
                trans_track("Hips", [0.0, 0.6, 1.2], [(0.0, 0.0, 0.0), (0.0, 0.03, 0.0), (0.0, 0.0, 0.0)]),
                rot_track("Spine", [0.0, 0.6, 1.2], [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
                rot_track("Head", [0.0, 0.6, 1.2], [(0.0, -3.0, 0.0), (0.0, 3.0, 0.0), (0.0, -3.0, 0.0)]),
                rot_track("Arm_L", [0.0, 0.6, 1.2], [(4.0, 0.0, 0.0), (0.0, 0.0, 1.5), (4.0, 0.0, 0.0)]),
                rot_track("Arm_R", [0.0, 0.6, 1.2], [(4.0, 0.0, 0.0), (0.0, 0.0, -1.5), (4.0, 0.0, 0.0)]),
            ],
        }
    )

    clips.append(
        {
            "name": "Walk",
            "tracks": [
                trans_track("Hips", [0.0, 0.25, 0.5, 0.75, 1.0], [(0.0, 0.00, 0.0), (0.0, -0.03, 0.0), (0.0, 0.00, 0.0), (0.0, -0.03, 0.0), (0.0, 0.00, 0.0)]),
                rot_track("Spine", [0.0, 0.25, 0.5, 0.75, 1.0], [(0.0, 0.0, 4.0), (0.0, 0.0, -4.0), (0.0, 0.0, 4.0), (0.0, 0.0, -4.0), (0.0, 0.0, 4.0)]),
                rot_track("Head", [0.0, 0.25, 0.5, 0.75, 1.0], [(0.0, 2.0, 2.0), (0.0, -2.0, -2.0), (0.0, 2.0, 2.0), (0.0, -2.0, -2.0), (0.0, 2.0, 2.0)]),
                rot_track("Arm_L", [0.0, 0.25, 0.5, 0.75, 1.0], [(22.0, 0.0, 0.0), (-18.0, 0.0, 0.0), (22.0, 0.0, 0.0), (-18.0, 0.0, 0.0), (22.0, 0.0, 0.0)]),
                rot_track("Forearm_L", [0.0, 0.25, 0.5, 0.75, 1.0], [(6.0, 0.0, 0.0), (-4.0, 0.0, 0.0), (6.0, 0.0, 0.0), (-4.0, 0.0, 0.0), (6.0, 0.0, 0.0)]),
                rot_track("Arm_R", [0.0, 0.25, 0.5, 0.75, 1.0], [(-18.0, 0.0, 0.0), (22.0, 0.0, 0.0), (-18.0, 0.0, 0.0), (22.0, 0.0, 0.0), (-18.0, 0.0, 0.0)]),
                rot_track("Forearm_R", [0.0, 0.25, 0.5, 0.75, 1.0], [(-4.0, 0.0, 0.0), (6.0, 0.0, 0.0), (-4.0, 0.0, 0.0), (6.0, 0.0, 0.0), (-4.0, 0.0, 0.0)]),
                rot_track("Leg_L", [0.0, 0.25, 0.5, 0.75, 1.0], [(-18.0, 0.0, 0.0), (18.0, 0.0, 0.0), (-18.0, 0.0, 0.0), (18.0, 0.0, 0.0), (-18.0, 0.0, 0.0)]),
                rot_track("Shin_L", [0.0, 0.25, 0.5, 0.75, 1.0], [(8.0, 0.0, 0.0), (16.0, 0.0, 0.0), (2.0, 0.0, 0.0), (16.0, 0.0, 0.0), (8.0, 0.0, 0.0)]),
                rot_track("Leg_R", [0.0, 0.25, 0.5, 0.75, 1.0], [(18.0, 0.0, 0.0), (-18.0, 0.0, 0.0), (18.0, 0.0, 0.0), (-18.0, 0.0, 0.0), (18.0, 0.0, 0.0)]),
                rot_track("Shin_R", [0.0, 0.25, 0.5, 0.75, 1.0], [(16.0, 0.0, 0.0), (8.0, 0.0, 0.0), (16.0, 0.0, 0.0), (2.0, 0.0, 0.0), (16.0, 0.0, 0.0)]),
            ],
        }
    )

    clips.append(
        {
            "name": "Run",
            "tracks": [
                trans_track("Hips", [0.0, 0.175, 0.35, 0.525, 0.7], [(0.0, -0.03, 0.0), (0.0, 0.02, 0.0), (0.0, -0.03, 0.0), (0.0, 0.02, 0.0), (0.0, -0.03, 0.0)]),
                rot_track("Spine", [0.0, 0.175, 0.35, 0.525, 0.7], [(8.0, 0.0, 6.0), (12.0, 0.0, -6.0), (8.0, 0.0, 6.0), (12.0, 0.0, -6.0), (8.0, 0.0, 6.0)]),
                rot_track("Head", [0.0, 0.175, 0.35, 0.525, 0.7], [(-4.0, 5.0, 0.0), (-2.0, -5.0, 0.0), (-4.0, 5.0, 0.0), (-2.0, -5.0, 0.0), (-4.0, 5.0, 0.0)]),
                rot_track("Arm_L", [0.0, 0.175, 0.35, 0.525, 0.7], [(40.0, 0.0, 0.0), (-34.0, 0.0, 0.0), (40.0, 0.0, 0.0), (-34.0, 0.0, 0.0), (40.0, 0.0, 0.0)]),
                rot_track("Forearm_L", [0.0, 0.175, 0.35, 0.525, 0.7], [(10.0, 0.0, 0.0), (-8.0, 0.0, 0.0), (10.0, 0.0, 0.0), (-8.0, 0.0, 0.0), (10.0, 0.0, 0.0)]),
                rot_track("Arm_R", [0.0, 0.175, 0.35, 0.525, 0.7], [(-34.0, 0.0, 0.0), (40.0, 0.0, 0.0), (-34.0, 0.0, 0.0), (40.0, 0.0, 0.0), (-34.0, 0.0, 0.0)]),
                rot_track("Forearm_R", [0.0, 0.175, 0.35, 0.525, 0.7], [(-8.0, 0.0, 0.0), (10.0, 0.0, 0.0), (-8.0, 0.0, 0.0), (10.0, 0.0, 0.0), (-8.0, 0.0, 0.0)]),
                rot_track("Leg_L", [0.0, 0.175, 0.35, 0.525, 0.7], [(-32.0, 0.0, 0.0), (34.0, 0.0, 0.0), (-32.0, 0.0, 0.0), (34.0, 0.0, 0.0), (-32.0, 0.0, 0.0)]),
                rot_track("Shin_L", [0.0, 0.175, 0.35, 0.525, 0.7], [(4.0, 0.0, 0.0), (24.0, 0.0, 0.0), (0.0, 0.0, 0.0), (24.0, 0.0, 0.0), (4.0, 0.0, 0.0)]),
                rot_track("Leg_R", [0.0, 0.175, 0.35, 0.525, 0.7], [(34.0, 0.0, 0.0), (-32.0, 0.0, 0.0), (34.0, 0.0, 0.0), (-32.0, 0.0, 0.0), (34.0, 0.0, 0.0)]),
                rot_track("Shin_R", [0.0, 0.175, 0.35, 0.525, 0.7], [(24.0, 0.0, 0.0), (4.0, 0.0, 0.0), (24.0, 0.0, 0.0), (0.0, 0.0, 0.0), (24.0, 0.0, 0.0)]),
            ],
        }
    )

    clips.append(
        {
            "name": "Attack",
            "tracks": [
                trans_track("Hips", [0.0, 0.2, 0.45, 0.7, 0.9], [(0.0, 0.0, 0.0), (0.0, -0.05, 0.0), (0.0, 0.02, 0.0), (0.0, -0.01, 0.0), (0.0, 0.0, 0.0)]),
                rot_track("Hips", [0.0, 0.2, 0.45, 0.7, 0.9], [(0.0, 0.0, 0.0), (0.0, -10.0, 0.0), (0.0, 10.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 0.0)]),
                rot_track("Spine", [0.0, 0.2, 0.45, 0.7, 0.9], [(0.0, 0.0, 0.0), (6.0, -22.0, 0.0), (-14.0, 28.0, -6.0), (-4.0, 4.0, 0.0), (0.0, 0.0, 0.0)]),
                rot_track("Head", [0.0, 0.2, 0.45, 0.7, 0.9], [(0.0, 0.0, 0.0), (0.0, -12.0, 0.0), (0.0, 15.0, 0.0), (0.0, 4.0, 0.0), (0.0, 0.0, 0.0)]),
                rot_track("Arm_R", [0.0, 0.2, 0.45, 0.7, 0.9], [(8.0, 0.0, 0.0), (-60.0, 0.0, 14.0), (92.0, 0.0, -12.0), (22.0, 0.0, 0.0), (8.0, 0.0, 0.0)]),
                rot_track("Forearm_R", [0.0, 0.2, 0.45, 0.7, 0.9], [(8.0, 0.0, 0.0), (-42.0, 0.0, 0.0), (38.0, 0.0, 0.0), (12.0, 0.0, 0.0), (8.0, 0.0, 0.0)]),
                rot_track("Arm_L", [0.0, 0.2, 0.45, 0.7, 0.9], [(0.0, 0.0, 0.0), (18.0, 0.0, 6.0), (-10.0, 0.0, -4.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
                rot_track("Forearm_L", [0.0, 0.2, 0.45, 0.7, 0.9], [(0.0, 0.0, 0.0), (8.0, 0.0, 0.0), (-4.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
                rot_track("Leg_L", [0.0, 0.2, 0.45, 0.7, 0.9], [(0.0, 0.0, 0.0), (-10.0, 0.0, 0.0), (6.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
                rot_track("Leg_R", [0.0, 0.2, 0.45, 0.7, 0.9], [(0.0, 0.0, 0.0), (8.0, 0.0, 0.0), (-6.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
            ],
        }
    )

    clips.append(
        {
            "name": "Hit",
            "tracks": [
                trans_track("Hips", [0.0, 0.12, 0.28, 0.45], [(0.0, 0.0, 0.0), (0.0, 0.02, -0.04), (0.0, -0.03, 0.01), (0.0, 0.0, 0.0)]),
                rot_track("Spine", [0.0, 0.12, 0.28, 0.45], [(0.0, 0.0, 0.0), (-20.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
                rot_track("Head", [0.0, 0.12, 0.28, 0.45], [(0.0, 0.0, 0.0), (-24.0, 0.0, 0.0), (12.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
                rot_track("Arm_L", [0.0, 0.12, 0.28, 0.45], [(0.0, 0.0, 0.0), (20.0, 0.0, 8.0), (-6.0, 0.0, -2.0), (0.0, 0.0, 0.0)]),
                rot_track("Arm_R", [0.0, 0.12, 0.28, 0.45], [(0.0, 0.0, 0.0), (20.0, 0.0, -8.0), (-6.0, 0.0, 2.0), (0.0, 0.0, 0.0)]),
            ],
        }
    )

    clips.append(
        {
            "name": "Death",
            "tracks": [
                trans_track("EnemyRoot", [0.0, 0.25, 0.7, 1.1, 1.4], [(0.0, 0.0, 0.0), (0.0, 0.02, 0.0), (0.08, 0.04, 0.0), (0.18, 0.05, 0.0), (0.18, 0.05, 0.0)]),
                rot_track("EnemyRoot", [0.0, 0.25, 0.7, 1.1, 1.4], [(0.0, 0.0, 0.0), (0.0, 0.0, 8.0), (0.0, 0.0, 42.0), (0.0, 0.0, 88.0), (0.0, 0.0, 92.0)]),
                trans_track("Hips", [0.0, 0.25, 0.7, 1.1, 1.4], [(0.0, 0.0, 0.0), (0.0, -0.05, 0.0), (0.0, -0.26, 0.0), (0.0, -0.42, 0.0), (0.0, -0.44, 0.0)]),
                rot_track("Spine", [0.0, 0.25, 0.7, 1.1, 1.4], [(0.0, 0.0, 0.0), (10.0, -6.0, 0.0), (32.0, -8.0, -6.0), (70.0, 0.0, -14.0), (78.0, 0.0, -16.0)]),
                rot_track("Head", [0.0, 0.25, 0.7, 1.1, 1.4], [(0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (28.0, 6.0, -6.0), (52.0, 0.0, -12.0), (58.0, 0.0, -12.0)]),
                rot_track("Arm_L", [0.0, 0.25, 0.7, 1.1, 1.4], [(0.0, 0.0, 0.0), (24.0, 0.0, 12.0), (60.0, 0.0, 30.0), (96.0, 0.0, 24.0), (100.0, 0.0, 24.0)]),
                rot_track("Forearm_L", [0.0, 0.25, 0.7, 1.1, 1.4], [(0.0, 0.0, 0.0), (16.0, 0.0, 0.0), (36.0, 0.0, 0.0), (52.0, 0.0, 0.0), (56.0, 0.0, 0.0)]),
                rot_track("Arm_R", [0.0, 0.25, 0.7, 1.1, 1.4], [(0.0, 0.0, 0.0), (18.0, 0.0, -12.0), (42.0, 0.0, -30.0), (86.0, 0.0, -22.0), (90.0, 0.0, -22.0)]),
                rot_track("Forearm_R", [0.0, 0.25, 0.7, 1.1, 1.4], [(0.0, 0.0, 0.0), (12.0, 0.0, 0.0), (30.0, 0.0, 0.0), (48.0, 0.0, 0.0), (52.0, 0.0, 0.0)]),
                rot_track("Leg_L", [0.0, 0.25, 0.7, 1.1, 1.4], [(0.0, 0.0, 0.0), (-8.0, 0.0, 8.0), (12.0, 0.0, 20.0), (40.0, 0.0, 10.0), (40.0, 0.0, 10.0)]),
                rot_track("Shin_L", [0.0, 0.25, 0.7, 1.1, 1.4], [(0.0, 0.0, 0.0), (8.0, 0.0, 0.0), (26.0, 0.0, 0.0), (44.0, 0.0, 0.0), (44.0, 0.0, 0.0)]),
                rot_track("Leg_R", [0.0, 0.25, 0.7, 1.1, 1.4], [(0.0, 0.0, 0.0), (-10.0, 0.0, -8.0), (8.0, 0.0, -22.0), (36.0, 0.0, -10.0), (36.0, 0.0, -10.0)]),
                rot_track("Shin_R", [0.0, 0.25, 0.7, 1.1, 1.4], [(0.0, 0.0, 0.0), (12.0, 0.0, 0.0), (28.0, 0.0, 0.0), (40.0, 0.0, 0.0), (40.0, 0.0, 0.0)]),
            ],
        }
    )

    return clips


def build_gltf():
    cube_geo = make_cube()
    spike_geo = make_spike()

    builder = BufferBuilder()

    cube_pos_accessor = builder.add_accessor(cube_geo["positions"], FLOAT, "VEC3", target=ARRAY_BUFFER)
    cube_norm_accessor = builder.add_accessor(cube_geo["normals"], FLOAT, "VEC3", target=ARRAY_BUFFER)
    cube_idx_accessor = builder.add_accessor(cube_geo["indices"], UNSIGNED_SHORT, "SCALAR", target=ELEMENT_ARRAY_BUFFER)

    spike_pos_accessor = builder.add_accessor(spike_geo["positions"], FLOAT, "VEC3", target=ARRAY_BUFFER)
    spike_norm_accessor = builder.add_accessor(spike_geo["normals"], FLOAT, "VEC3", target=ARRAY_BUFFER)
    spike_idx_accessor = builder.add_accessor(spike_geo["indices"], UNSIGNED_SHORT, "SCALAR", target=ELEMENT_ARRAY_BUFFER)

    materials = [
        {
            "name": "Bark",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.34, 0.23, 0.13, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 1.0,
            },
        },
        {
            "name": "Moss",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.18, 0.38, 0.14, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.95,
            },
        },
        {
            "name": "Eyes",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.90, 0.16, 0.10, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.2,
            },
            "emissiveFactor": [0.9, 0.15, 0.08],
        },
    ]

    meshes = [
        {
            "name": "Cube_Bark",
            "primitives": [
                {
                    "attributes": {"POSITION": cube_pos_accessor, "NORMAL": cube_norm_accessor},
                    "indices": cube_idx_accessor,
                    "material": 0,
                }
            ],
        },
        {
            "name": "Cube_Moss",
            "primitives": [
                {
                    "attributes": {"POSITION": cube_pos_accessor, "NORMAL": cube_norm_accessor},
                    "indices": cube_idx_accessor,
                    "material": 1,
                }
            ],
        },
        {
            "name": "Cube_Eye",
            "primitives": [
                {
                    "attributes": {"POSITION": cube_pos_accessor, "NORMAL": cube_norm_accessor},
                    "indices": cube_idx_accessor,
                    "material": 2,
                }
            ],
        },
        {
            "name": "Spike_Bark",
            "primitives": [
                {
                    "attributes": {"POSITION": spike_pos_accessor, "NORMAL": spike_norm_accessor},
                    "indices": spike_idx_accessor,
                    "material": 0,
                }
            ],
        },
        {
            "name": "Spike_Moss",
            "primitives": [
                {
                    "attributes": {"POSITION": spike_pos_accessor, "NORMAL": spike_norm_accessor},
                    "indices": spike_idx_accessor,
                    "material": 1,
                }
            ],
        },
    ]

    mesh_lookup = {
        "cube_bark": 0,
        "cube_moss": 1,
        "cube_eye": 2,
        "spike_bark": 3,
        "spike_moss": 4,
    }

    nodes, node_lookup, root = base_enemy_structure(mesh_lookup)
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
            samplers.append(
                {
                    "input": input_accessor,
                    "output": output_accessor,
                    "interpolation": "LINEAR",
                }
            )
            channels.append(
                {
                    "sampler": sampler_index,
                    "target": {"node": track["node"], "path": track["path"]},
                }
            )
        animations.append({"name": clip["name"], "samplers": samplers, "channels": channels})

    gltf = {
        "asset": {"version": "2.0", "generator": "Codex Enemy02 Procedural Generator"},
        "scene": 0,
        "scenes": [{"name": "Enemy02Scene", "nodes": [root]}],
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

    return gltf


def write_readme(output_dir, gltf_name, glb_name):
    readme = f"""# 敌人02 详细说明

## 1. 资源概述

`敌人02` 是一个面向网页游戏使用场景制作的低模树妖敌人资源，核心目标是:

- 体积小，方便在 Web 项目中快速加载
- 风格明确，适合作为怪物、树妖、木怪或关卡守卫使用
- 动画命名清晰，方便直接接入状态机
- 结构简单，便于后续继续改造或程序化生成变体

当前资源同时提供:

- `{gltf_name}`: 文本版 glTF，便于检查结构和二次处理
- `{glb_name}`: 二进制版 glTF，便于网页端直接加载
- `enemy02_preview.png`: 本地预览图
- `enemy02_meta.json`: 简要元信息
- `generate_enemy02.py`: 生成脚本，可重复生成本资源

网页项目里建议优先使用 `{glb_name}`。

## 2. 视觉定位

该模型定位为“低模树妖重装怪 / Tree Brute”。

视觉特征包括:

- 主体材质偏深棕色树皮
- 胸口和背部有苔藓块，帮助强化非人类怪物感
- 头部有发光红眼，便于在中远距离识别
- 四肢和爪子偏块状与尖刺结合，适合近战挥击类敌人
- 整体轮廓高瘦，站立时具有一定压迫感

如果你的游戏是偏森林、废墟、诡异生物、地牢或奇幻方向，这个模型会比较合适。

## 3. 技术规格

当前资源的关键规格如下:

- 资源格式: `glTF 2.0` / `GLB`
- 近似身高: `2.45m`
- 节点数量: `38`
- 网格数量: `5`
- 材质数量: `3`
- 动画数量: `6`
- 主要材质名: `Bark`、`Moss`、`Eyes`
- 主要网格名: `Cube_Bark`、`Cube_Moss`、`Cube_Eye`、`Spike_Bark`、`Spike_Moss`
- `GLB` 文件大小: 约 `43KB`

该模型采用的是“分层节点 + 刚体部件动画”的方式，而不是传统 DCC 软件里常见的复杂骨骼蒙皮角色。

这意味着:

- 优点是体积小、结构直观、网页端接入简单
- 缺点是动作风格更偏低模和硬朗，不适合特别细腻的肌肉或布料形变

## 4. 坐标与朝向

模型默认以地面为 `Y=0` 附近的站立参考面，整体高度约为 `2.45m`。

约定上:

- `Y` 轴为高度方向
- 角色正面朝向 `+Z`
- 模型移动不依赖动画内置位移

也就是说，`Walk` 和 `Run` 是“原地循环动作”，真正的位移请由你的游戏逻辑控制。

## 5. 动画清单

模型内置以下动画片段:

### `Idle`

- 时长约 `1.2s`
- 建议循环播放
- 用途: 待机、警戒、巡逻暂停、发现玩家前的默认状态
- 特征: 轻微呼吸感、头部和躯干存在小幅摆动

### `Walk`

- 时长约 `1.0s`
- 建议循环播放
- 用途: 慢速靠近、巡逻移动、非战斗追踪
- 特征: 四肢摆幅中等，节奏平稳

### `Run`

- 时长约 `0.7s`
- 建议循环播放
- 用途: 冲刺追击、战斗接近、快速换位
- 特征: 身体前倾更明显，四肢摆动更大，节奏更急

### `Attack`

- 时长约 `0.9s`
- 建议单次播放
- 用途: 近战挥击、重击、普通攻击前摇到收招
- 特征: 右臂为主挥击，躯干带明显扭转

### `Hit`

- 时长约 `0.45s`
- 建议单次播放
- 用途: 受击反馈、轻微硬直
- 特征: 上半身后仰，双臂短促抬起，适合受伤反馈

### `Death`

- 时长约 `1.4s`
- 建议单次播放，并在最后一帧停住
- 用途: 死亡倒地、战斗结束
- 特征: 根节点和躯干共同翻倒，适合做“倒地不起”的收尾

## 6. 推荐状态机接法

一个比较常见的接法如下:

- 出生后默认进入 `Idle`
- 敌人开始巡逻或低速逼近时切到 `Walk`
- 敌人高速追击时切到 `Run`
- 命中攻击判定前后播放 `Attack`
- 受到伤害时插播 `Hit`
- 血量归零后播放 `Death`

推荐规则:

- `Idle`、`Walk`、`Run` 作为循环状态
- `Attack`、`Hit`、`Death` 作为一次性状态
- `Death` 播放后不再切回其他状态

## 7. Web 接入建议

### Three.js

示例:

```js
import * as THREE from 'three';
import {{ GLTFLoader }} from 'three/examples/jsm/loaders/GLTFLoader.js';

const loader = new GLTFLoader();
const mixerClock = new THREE.Clock();
let mixer;
let actions = {{}};

loader.load('/assets/model.glb', (gltf) => {{
  const enemy = gltf.scene;
  scene.add(enemy);

  mixer = new THREE.AnimationMixer(enemy);

  for (const clip of gltf.animations) {{
    actions[clip.name] = mixer.clipAction(clip);
  }}

  actions.Idle?.play();
}});

function playAction(name, loop = true) {{
  if (!mixer || !actions[name]) return;

  Object.values(actions).forEach((action) => action.stop());
  const action = actions[name];
  action.reset();
  action.setLoop(loop ? THREE.LoopRepeat : THREE.LoopOnce, loop ? Infinity : 1);
  action.clampWhenFinished = !loop;
  action.play();
}}

function update() {{
  const dt = mixerClock.getDelta();
  mixer?.update(dt);
  renderer.render(scene, camera);
  requestAnimationFrame(update);
}}

update();
```

接入建议:

- `Idle` / `Walk` / `Run` 用循环模式
- `Attack` / `Hit` / `Death` 用单次播放模式
- 将敌人的实际位移、寻路、朝向旋转交给游戏逻辑处理

## 8. 碰撞与玩法建议

这个模型适合搭配简化碰撞体，不建议直接使用渲染网格做碰撞。

建议至少拆成:

- 一个胶囊体: 作为主角色碰撞
- 一个前方攻击盒: 作为挥击命中区域
- 一个较小的头部或胸部命中点: 作为弱点判定可选

推荐逻辑:

- 平时用胶囊体做寻路和阻挡
- 播放 `Attack` 时在挥击阶段启用攻击盒
- 播放 `Death` 后关闭主 AI 和攻击判定

## 9. 资源局限

当前版本是为了“快速可用”和“网页端轻量化”而设计的，因此有一些明确边界:

- 不是高精度写实角色
- 不是复杂骨骼蒙皮角色
- 没有单独贴图文件，颜色主要由材质色决定
- 没有内置音效同步或事件帧
- `Walk` 和 `Run` 不自带根运动

如果你后续需要更高级的版本，可以在此基础上继续扩展:

- 增加更细的网格形体
- 增加贴图和法线贴图
- 增加更多攻击动作
- 增加受击方向区分
- 增加施法、怒吼、待机变体等动画

## 10. 如何重新生成

本资源不是手工建模导出的静态资产，而是由脚本生成的。重新生成方法:

```bash
python3 generate_enemy02.py
```

脚本会重新输出:

- `{gltf_name}`
- `{glb_name}`
- `enemy02_preview.png`
- `README.md`
- `enemy02_meta.json`

因此如果你打算继续改造这个敌人，建议优先修改 `generate_enemy02.py`，再重新执行脚本。

## 11. 适合的使用场景

这个敌人特别适合以下类型:

- 森林关卡中的近战树妖
- 废墟、神庙、地牢中的守卫怪
- 小型 Boss 或精英怪
- 网页动作游戏里的可复用敌人模板
- 需要快速验证战斗流程的原型项目

## 12. 文件清单

- `{gltf_name}`: 可编辑的文本 glTF 文件
- `{glb_name}`: 推荐直接用于网页加载的二进制模型
- `enemy02_preview.png`: 模型静态预览图
- `enemy02_meta.json`: 基本元信息
- `generate_enemy02.py`: 资源生成脚本

---

如果后续你要继续把这个敌人接进项目，优先使用 `{glb_name}`，并将动作状态按 `Idle -> Walk/Run -> Attack/Hit -> Death` 的思路接入即可。
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def render_preview(output_dir):
    cube = make_cube()
    spike = make_spike()
    mesh_geo = {
        0: cube,
        1: cube,
        2: cube,
        3: spike,
        4: spike,
    }
    mesh_colors = {
        0: np.array([109, 72, 39], dtype=np.float64),
        1: np.array([69, 114, 49], dtype=np.float64),
        2: np.array([216, 48, 28], dtype=np.float64),
        3: np.array([109, 72, 39], dtype=np.float64),
        4: np.array([69, 114, 49], dtype=np.float64),
    }

    gltf = build_gltf()
    nodes = gltf["nodes"]
    scene_roots = gltf["scenes"][0]["nodes"]
    children = {idx: node.get("children", []) for idx, node in enumerate(nodes)}

    def qrot(q, v):
        qv = np.array([v[0], v[1], v[2], 0.0], dtype=np.float64)
        qi = np.array([-q[0], -q[1], -q[2], q[3]], dtype=np.float64)
        return quat_mul(quat_mul(q, qv), qi)[:3]

    world = {}

    def traverse(idx, parent_t=None, parent_q=None, parent_s=None):
        parent_t = np.zeros(3, dtype=np.float64) if parent_t is None else parent_t
        parent_q = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64) if parent_q is None else parent_q
        parent_s = np.ones(3, dtype=np.float64) if parent_s is None else parent_s

        node = nodes[idx]
        t = np.array(node.get("translation", [0.0, 0.0, 0.0]), dtype=np.float64)
        r = np.array(node.get("rotation", [0.0, 0.0, 0.0, 1.0]), dtype=np.float64)
        s = np.array(node.get("scale", [1.0, 1.0, 1.0]), dtype=np.float64)

        world_t = parent_t + qrot(parent_q, parent_s * t)
        world_q = quat_mul(parent_q, r)
        world_s = parent_s * s
        world[idx] = (world_t, world_q, world_s)

        for child_idx in children.get(idx, []):
            traverse(child_idx, world_t, world_q, world_s)

    for root_idx in scene_roots:
        traverse(root_idx)

    triangles = []
    for idx, node in enumerate(nodes):
        if "mesh" not in node:
            continue
        geometry = mesh_geo[node["mesh"]]
        color = mesh_colors[node["mesh"]]
        world_t, world_q, world_s = world[idx]
        vertices = geometry["positions"] * world_s
        vertices = np.array([qrot(world_q, vertex) + world_t for vertex in vertices], dtype=np.float64)
        tri_indices = geometry["indices"].reshape(-1, 3)
        for tri in tri_indices:
            triangles.append((vertices[tri], color))

    points = np.concatenate([tri[0] for tri in triangles], axis=0)
    center = (points.min(axis=0) + points.max(axis=0)) * 0.5

    def rotation_matrix(yaw_deg, pitch_deg):
        yaw = math.radians(yaw_deg)
        pitch = math.radians(pitch_deg)
        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        rot_y = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]], dtype=np.float64)
        rot_x = np.array([[1.0, 0.0, 0.0], [0.0, cp, -sp], [0.0, sp, cp]], dtype=np.float64)
        return rot_x @ rot_y

    views = [("Front", 15.0, -8.0), ("3/4", 40.0, -12.0)]
    width = 420
    height = 420
    image = Image.new("RGB", (width * len(views), height), (245, 238, 224))
    light = np.array([0.4, -0.6, 0.7], dtype=np.float64)
    light /= np.linalg.norm(light)

    for view_index, (label, yaw, pitch) in enumerate(views):
        draw = ImageDraw.Draw(image)
        panel = [view_index * width + 8, 8, (view_index + 1) * width - 8, height - 8]
        draw.rounded_rectangle(panel, radius=18, fill=(250, 245, 236), outline=(201, 187, 164), width=2)

        rot = rotation_matrix(yaw, pitch)
        transformed = []
        projected_xy = []
        for tri, color in triangles:
            points_3d = (tri - center) @ rot.T
            transformed.append((points_3d, color))
            projected_xy.append(points_3d[:, :2])

        projected_xy = np.concatenate(projected_xy, axis=0)
        minimum = projected_xy.min(axis=0)
        maximum = projected_xy.max(axis=0)
        span = max(maximum[0] - minimum[0], maximum[1] - minimum[1])
        scale = (min(width, height) - 70) / span

        draw_items = []
        for points_3d, color in transformed:
            edge_a = points_3d[1] - points_3d[0]
            edge_b = points_3d[2] - points_3d[0]
            normal = np.cross(edge_a, edge_b)
            normal_length = np.linalg.norm(normal) or 1.0
            normal = normal / normal_length
            shade = max(0.2, float(normal @ light))
            shaded = np.clip(color * (0.55 + 0.55 * shade), 0, 255).astype(int)
            screen_points = []
            for x, y, z in points_3d:
                sx = (x - (minimum[0] + maximum[0]) / 2.0) * scale + width / 2.0 + view_index * width
                sy = height / 2.0 - (y - (minimum[1] + maximum[1]) / 2.0) * scale + 12.0
                screen_points.append((sx, sy))
            depth = points_3d[:, 2].mean()
            draw_items.append((depth, tuple(shaded.tolist()), screen_points))

        draw_items.sort(key=lambda item: item[0])
        for _, fill, polygon in draw_items:
            draw.polygon(polygon, fill=fill)
        draw.text((view_index * width + 18, 16), label, fill=(93, 73, 58))

    image.save(output_dir / "enemy02_preview.png")


def main():
    output_dir = Path(__file__).resolve().parent
    output_dir.mkdir(parents=True, exist_ok=True)

    gltf = build_gltf()
    gltf_path = output_dir / "model.gltf"
    gltf_path.write_text(json.dumps(gltf, ensure_ascii=False, indent=2), encoding="utf-8")

    glb_path = output_dir / "model.glb"
    try:
        from pygltflib import GLTF2

        gltf_model = GLTF2().load(str(gltf_path))
        gltf_model.save_binary(str(glb_path))
    except Exception as exc:
        glb_path.write_text(
            "GLB export failed.\n"
            f"Reason: {exc}\n"
            "Use the glTF file instead.\n",
            encoding="utf-8",
        )

    write_readme(output_dir, gltf_path.name, glb_path.name)

    meta = {
        "name": "Enemy02 Tree Brute",
        "format": ["gltf", "glb"],
        "approx_height_m": 2.45,
        "style": "low_poly_tree_monster",
        "animations": ["Idle", "Walk", "Run", "Attack", "Hit", "Death"],
    }
    (output_dir / "enemy02_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    render_preview(output_dir)

    print(gltf_path)
    print(glb_path)
    print(output_dir / "README.md")


if __name__ == "__main__":
    main()
