#!/usr/bin/env python3
"""程序化生成带基础动画的 AK-47 资源。

这个脚本会一次性完成几件事：
1. 通过简单几何体拼出武器各部分。
2. 按部件和材质组织网格，写成 glTF 结构。
3. 生成待机、开火、换弹、瞄准、奔跑几个动画片段。
4. 导出 `.gltf` / `.glb`，并额外渲染一张静态预览图和元数据。

如果你对建模完全陌生，可以把这个脚本理解成：

- 不是在 Blender 里“手工捏”枪，而是在 Python 里用数学把形状拼出来。
- 这里用到的基础积木主要只有两种：`box` 盒子 和 `cylinder` 圆柱。
- 每个积木本身只是一个“默认大小、默认朝向”的原型。
- 真正放到枪上时，会对原型做三件事：
  1. `scale` 缩放，决定长宽高
  2. `rotation` 旋转，决定朝向
  3. `translation` 平移，决定放在哪里
- 多个积木拼在一起后，就组成枪身、枪管、弹匣这些大部件。
- 再把这些大部件挂到不同节点上，就能让某些部分单独运动，比如枪机后坐、弹匣拔出。

几个建模里的常见词，在这份脚本里可以这样理解：

- `position` 顶点坐标：一个点在 3D 空间里的位置。
- `normal` 法线：一个朝向向量，用来告诉渲染器“这一面朝哪里”，从而决定明暗。
- `indices` 索引：告诉渲染器哪 3 个顶点组成一个三角形。
- `mesh` 网格：一堆顶点、法线、三角形的集合，也就是“可渲染的形状”。
- `node` 节点：场景层级里的一个变换容器，可以挂 mesh，也可以作为父节点带动孩子一起动。
- `animation` 动画：让某个节点随时间改变位置或旋转。

所以整份脚本的核心思路其实很朴素：
“先拼出静态模型，再把模型按部件挂到节点上，最后给节点写关键帧动画。”
"""

from __future__ import annotations

import base64
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from pygltflib import GLTF2


OUTPUT_DIR = Path(__file__).resolve().parent

# glTF 2.0 中会用到的常量枚举，直接写数字能减少对额外封装的依赖。
# 如果你没接触过 glTF，可以先把它当作“3D 版 JSON 文件格式”。
# 其中：
# - componentType 决定二进制里每个数是 float、uint16 之类的什么类型
# - ARRAY_BUFFER 一般装顶点属性，例如位置、法线
# - ELEMENT_ARRAY_BUFFER 一般装三角形索引
FLOAT = 5126
UNSIGNED_SHORT = 5123
ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963


def normalize_quat(q):
    """归一化四元数，避免后续旋转运算因长度漂移产生误差。

    四元数可以先粗略理解成“专门拿来表示 3D 旋转的四个数”。
    它的长度理想情况下应该是 1；如果不是 1，连续旋转时可能会有误差。
    所以每次使用前先单位化，是一种很常见的稳妥做法。
    """
    q = np.asarray(q, dtype=np.float64)
    norm = np.linalg.norm(q)
    if norm == 0:
        return np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)
    return q / norm


def quat_mul(a, b):
    """四元数乘法，用于叠加旋转。

    如果你想象“先绕一个方向转，再绕另一个方向转”，
    四元数乘法就是把这两个旋转合成一个旋转的办法。
    """
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
    """把轴角旋转转换成四元数。

    `axis` 表示绕哪根轴转，`angle_deg` 表示转多少度。
    例如：
    - `(1, 0, 0), 30` 表示绕 X 轴转 30 度
    - `(0, 0, 1), 90` 表示绕 Z 轴转 90 度
    """
    angle_rad = math.radians(angle_deg) * 0.5
    s = math.sin(angle_rad)
    c = math.cos(angle_rad)
    ax, ay, az = axis
    return np.array([ax * s, ay * s, az * s, c], dtype=np.float64)


def quat_from_euler_xyz(x_deg, y_deg, z_deg):
    """把欧拉角转换成四元数，组合顺序保持为 Z * Y * X。

    欧拉角就是大家更熟悉的“绕 X/Y/Z 分别转多少度”。
    之所以最后转成四元数，是因为：
    - glTF 动画里旋转常直接存四元数
    - 四元数在插值时更稳定
    - 可以避开部分欧拉角万向节锁问题
    """
    qx = quat_from_axis_angle((1.0, 0.0, 0.0), x_deg)
    qy = quat_from_axis_angle((0.0, 1.0, 0.0), y_deg)
    qz = quat_from_axis_angle((0.0, 0.0, 1.0), z_deg)
    return normalize_quat(quat_mul(quat_mul(qz, qy), qx))


def rotate_vector(q, v):
    """使用四元数旋转一个三维向量。

    这里既用于旋转顶点位置，也用于旋转法线方向。
    顶点被旋转后，几何体的形状朝向会改变；
    法线被旋转后，光照方向才能和新的朝向保持一致。
    """
    q = normalize_quat(q)
    vq = np.array([v[0], v[1], v[2], 0.0], dtype=np.float64)
    qi = np.array([-q[0], -q[1], -q[2], q[3]], dtype=np.float64)
    return quat_mul(quat_mul(q, vq), qi)[:3]


def geometry_dict(positions, normals, indices):
    """统一几何数据格式，方便后面合并和导出。

    这一类字典可以理解成“一个最小可渲染网格包”：
    - positions: 所有顶点坐标
    - normals: 每个顶点对应的法线
    - indices: 三角形索引

    为什么一定要三者配套：
    - 只有 positions，知道点在哪，但不知道怎么连成面
    - 只有 indices，知道怎么连，但没有点的位置
    - 没有 normals，虽然能渲染，但明暗会很怪
    """
    return {
        "positions": np.asarray(positions, dtype=np.float32),
        "normals": np.asarray(normals, dtype=np.float32),
        "indices": np.asarray(indices, dtype=np.uint16),
    }


def merge_geometries(geometries):
    """把多个几何块拼成一份连续的顶点/索引数据。

    这是“合并网格”的基本动作。
    例如：
    - 枪身的一块盒子
    - 护木的一块盒子
    - 枪管的一段圆柱

    它们最开始各有各的顶点编号；要并成一个 mesh，就要把后来的索引整体往后偏移。
    这就是 `offset` 的作用。
    """
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


def transform_geometry(
    geo,
    translation=(0.0, 0.0, 0.0),
    rotation=(0.0, 0.0, 0.0, 1.0),
    scale=(1.0, 1.0, 1.0),
):
    """对一个几何体做平移、旋转、缩放。

    这是程序化建模里最重要的基础操作之一。
    你可以把 `geo` 理解成一个“模具”，而这个函数负责把模具放到正确的位置：

    - `scale`：把模具拉长、压扁、缩小
    - `rotation`：把模具转到需要的方向
    - `translation`：把模具移动到最终坐标

    例如一个默认盒子本来是 1x1x1 的立方体，
    经过 `scale=(0.18, 0.12, 0.48)` 后，就变成一个更扁更长的长方体，
    很适合拿来充当枪身的一段。
    """
    translation = np.asarray(translation, dtype=np.float64)
    rotation = normalize_quat(rotation)
    scale = np.asarray(scale, dtype=np.float64)

    positions = []
    normals = []
    for pos, normal in zip(geo["positions"], geo["normals"]):
        p = rotate_vector(rotation, np.asarray(pos, dtype=np.float64) * scale) + translation
        # 法线需要抵消缩放影响后再归一化，否则光照会明显失真。
        n = rotate_vector(rotation, np.asarray(normal, dtype=np.float64) / np.where(scale == 0.0, 1.0, scale))
        n = n / (np.linalg.norm(n) or 1.0)
        positions.append(p)
        normals.append(n)
    return geometry_dict(np.asarray(positions), np.asarray(normals), geo["indices"])


def make_box(size=(1.0, 1.0, 1.0)):
    """生成一个带独立面法线的盒子。

    为什么不是 8 个顶点，而是每个面都单独放 4 个顶点？
    因为这个脚本想让盒子边缘看起来“硬朗”，像机械零件。

    如果多个面共享同一个顶点，渲染器常会把法线平滑插值，
    最终边角看起来就会偏圆滑。
    对枪械这种硬表面物体，通常更希望边界明显一些，
    所以这里每个面都使用自己的顶点和法线。
    """
    sx, sy, sz = size
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    # 下面 6 项分别对应前后左右上下 6 个面。
    # 每个面用 4 个顶点 + 1 个法线来描述。
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
        # 一个四边形面最终仍然会拆成两个三角形，因为 GPU 最终吃的是三角形。
        positions.extend([a, b, c, d])
        normals.extend([normal, normal, normal, normal])
        indices.extend([start, start + 1, start + 2, start, start + 2, start + 3])
    return geometry_dict(positions, normals, indices)


def make_cylinder(length=1.0, radius=0.1, sides=12, radius_end=None):
    """生成圆柱/圆台，主轴沿 X 轴，默认两端封口。

    这里的圆柱不是“数学上无限光滑”的圆，而是很多边组成的近似体。
    `sides=12` 的意思是圆周被切成 12 段。

    对低模或网页资源来说，12 边已经足够表达枪管这类细长结构，
    同时顶点数也不会太高。

    如果 `radius_end != radius`，它就不是等粗圆柱，而会变成圆台。
    """
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
        # ring_a / ring_b 可以理解成“前后两个圆环上的采样点”。
        ring_a.append(np.array([-half, math.cos(angle) * radius, math.sin(angle) * radius], dtype=np.float64))
        ring_b.append(np.array([half, math.cos(angle) * radius_end, math.sin(angle) * radius_end], dtype=np.float64))

    for i in range(sides):
        j = (i + 1) % sides
        a, b, c, d = ring_a[i], ring_a[j], ring_b[j], ring_b[i]
        # 侧面法线由边叉乘得到，能同时兼容圆柱和圆台。
        normal = np.cross(d - a, b - a)
        normal = normal / (np.linalg.norm(normal) or 1.0)
        start = len(positions)
        # 圆柱侧面本质上是一圈一圈的四边形条带，每条带再拆成两个三角形。
        positions.extend([a, b, c, d])
        normals.extend([normal, normal, normal, normal])
        indices.extend([start, start + 1, start + 2, start, start + 2, start + 3])

    def add_cap(center_x, ring, flip):
        """补一个端盖，flip 控制法线方向和三角面绕序。"""
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
    """把一个几何件变换后塞进指定部件组和材质桶里。

    `groups` 的层级结构大致是：

    {
        "receiver": {
            "metal": [几何体1, 几何体2, ...],
            "black": [...],
        },
        "mag": {
            "metal": [...]
        }
    }

    这样组织的好处是：
    - 同一个“会一起动的部件”可以放在同一组
    - 同一组里还能继续按材质拆开，方便 glTF 指定不同材质球
    """
    groups.setdefault(group, {}).setdefault(material, []).append(
        transform_geometry(geo, translation=translation, rotation=rotation, scale=scale)
    )


def build_weapon_groups():
    """搭出武器的主要部件。

    这里先按逻辑部件分组，后面会把这些组分别挂到不同节点上，
    这样 bolt 和 magazine 才能在动画里单独运动。

    可以把这里理解成“搭积木总装车间”。
    每一行 `add_group_part(...)` 都是在说：
    “拿一个基础盒子/圆柱，缩放一下，转一下，摆到某个位置，让它充当枪上的某个零件。”

    这份模型不是写实级别的精细枪模，而是偏概括化、适合网页实时使用的低模方案。
    所以很多零件不是严格一一还原，而是用比较少的块面把视觉特征概括出来。
    """
    box = make_box()
    cylinder = make_cylinder()
    groups = {}

    receiver = "receiver"
    bolt = "bolt"
    mag = "mag"

    metal = "metal"
    black = "black"
    wood = "wood"
    skin = "skin"

    # 坐标理解小提示：
    # - 这个模型里 X/Y/Z 的绝对语义并不重要，关键是整份脚本内部保持一致。
    # - 从这些摆放数字的分布可以看出，枪整体主要沿 Z 方向拉长。
    # - 所以你可以粗略把“更负的 Z”理解成更靠枪口，“更正的 Z”理解成更靠枪托。
    #
    # receiver 组：大部分枪身主体都放在这里，动画时它会跟随整把枪一起运动。
    # 下面几块盒子和圆柱一起构成：
    # - 机匣主体
    # - 上盖/导气部分
    # - 前后木制护木 / 枪托区域
    # - 握把、准星附近的小块
    # - 枪管与导气管
    # - 两个“skin”块用来模拟第一人称视角里露出的双手
    add_group_part(groups, receiver, metal, box, translation=(0.02, 0.00, -0.02), scale=(0.18, 0.12, 0.48))
    # 枪身上方较窄的一层，读起来可以把它当作机匣盖或上部结构。
    add_group_part(groups, receiver, black, box, translation=(0.02, 0.08, 0.02), scale=(0.17, 0.04, 0.32))
    # 靠后的木质块，概括枪托/后护木一带的体量。
    add_group_part(groups, receiver, wood, box, translation=(-0.10, -0.02, 0.28), scale=(0.12, 0.08, 0.30))
    # 靠前的木质块，概括前护木的木质包覆部分。
    add_group_part(groups, receiver, wood, box, translation=(0.05, -0.01, -0.33), scale=(0.16, 0.10, 0.25))
    # 倾斜的黑色块充当手枪式握把，让轮廓更像 AK。
    add_group_part(groups, receiver, black, box, translation=(-0.03, -0.16, 0.10), rotation=quat_from_euler_xyz(0.0, 0.0, -20.0), scale=(0.09, 0.18, 0.06))
    # 上方的小黑块用于增加上机匣区域层次。
    add_group_part(groups, receiver, black, box, translation=(0.02, 0.10, -0.06), scale=(0.05, 0.08, 0.08))
    # 更靠前的小块可看作准星座/枪口前部的轮廓补充。
    add_group_part(groups, receiver, black, box, translation=(0.05, 0.10, -0.70), scale=(0.04, 0.08, 0.04))
    # 长圆柱是枪管主体。原始圆柱沿 X 轴，所以先旋转 90 度让它改为沿 Z 方向伸出。
    add_group_part(groups, receiver, metal, cylinder, translation=(0.05, 0.03, -0.63), rotation=quat_from_euler_xyz(0.0, 0.0, 90.0), scale=(0.82, 0.018, 0.018))
    # 较短较细的圆柱可理解为导气管或上方细长金属部件。
    add_group_part(groups, receiver, metal, cylinder, translation=(0.03, 0.08, -0.44), rotation=quat_from_euler_xyz(0.0, 0.0, 90.0), scale=(0.34, 0.012, 0.012))
    # 枪口最前端再补一小段更粗圆柱，强化枪口层次。
    add_group_part(groups, receiver, metal, cylinder, translation=(0.05, 0.03, -1.02), rotation=quat_from_euler_xyz(0.0, 0.0, 90.0), scale=(0.10, 0.022, 0.022))
    # 第一人称手部不是精细手模，只是两个简化盒子。
    # 目的不是做手指细节，而是让预览和动画里看起来更像“有人端着枪”。
    add_group_part(groups, receiver, skin, box, translation=(0.12, -0.18, -0.28), rotation=quat_from_euler_xyz(-34.0, 4.0, -8.0), scale=(0.12, 0.08, 0.12))
    add_group_part(groups, receiver, skin, box, translation=(-0.08, -0.18, 0.18), rotation=quat_from_euler_xyz(-36.0, 0.0, 7.0), scale=(0.12, 0.08, 0.12))

    # bolt 组：枪机组件。
    # 之所以单独成组，是因为开火时它需要独立后坐一下。
    add_group_part(groups, bolt, metal, box, translation=(0.02, -0.17, -0.08), rotation=quat_from_euler_xyz(-23.0, 3.0, 5.0), scale=(0.10, 0.22, 0.07))
    # 这个黑色小块像枪机上的附属凸起，用来增加轮廓识别度。
    add_group_part(groups, bolt, black, box, translation=(-0.02, 0.05, -0.01), scale=(0.04, 0.02, 0.11))

    # mag 组：弹匣。
    # 它单独成组是为了换弹时可以整体往下拔出、再塞回去。
    # AK 的香蕉弹匣在真实造型里会更弯，这里先用一个倾斜长方体做低模概括。
    add_group_part(groups, mag, metal, box, translation=(0.02, -0.17, -0.08), rotation=quat_from_euler_xyz(-23.0, 3.0, 5.0), scale=(0.10, 0.22, 0.07))

    return groups


def flatten_group_parts(groups):
    """把分组后的部件压平成按材质合并的网格，供预览图渲染使用。

    注意这里是给预览图服务，所以不关心“哪个部件能动、哪个不能动”，
    只关心“最后静态画面里有哪些三角形要画出来”。
    因此它会丢掉节点层级信息，只保留材质分类。
    """
    combined = {}
    for mats in groups.values():
        for material, geos in mats.items():
            combined.setdefault(material, []).extend(geos)
    return {material: merge_geometries(geos) for material, geos in combined.items()}


class BufferBuilder:
    """负责打包 glTF 二进制 buffer、bufferView 和 accessor。

    对 glTF 不熟时，这三层名字很容易绕。可以先这样记：

    - `buffer`：一整块二进制大仓库
    - `bufferView`：这块仓库里的某一段切片
    - `accessor`：告诉读取器“这段切片该按什么格式解释”

    举个例子：
    - `buffer` 里装着很多原始字节
    - 某个 `bufferView` 指出“第 1024 到 2047 字节是一段顶点数据”
    - `accessor` 再说明“这段数据每 3 个 float 表示一个顶点位置”
    """

    def __init__(self):
        self.data = bytearray()
        self.buffer_views = []
        self.accessors = []

    def add_blob(self, blob, target=None):
        """追加一段原始二进制数据，并返回它对应的 bufferView 索引。"""
        # glTF 要求 bufferView 常按 4 字节对齐，避免某些加载器解析异常。
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
        """把 numpy 数组写入 buffer，并登记 accessor 描述。

        `accessor_type` 常见值：
        - `SCALAR`: 单个数，例如索引
        - `VEC3`: 三个数组成一个元素，例如位置 `(x, y, z)`、法线
        - `VEC4`: 四个数组成一个元素，例如四元数旋转
        """
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
            # 索引虽然是标量，但 glTF 仍要求 min/max 用列表表示。
            accessor["min"] = [int(arr.min()) if component_type == UNSIGNED_SHORT else float(arr.min())]
            accessor["max"] = [int(arr.max()) if component_type == UNSIGNED_SHORT else float(arr.max())]
        self.accessors.append(accessor)
        return len(self.accessors) - 1


def build_animations(node_lookup):
    """构建几段基础 FPS 动画。

    动画数据按“基础姿态 + 每个关键帧增量”来写，便于后面继续微调。

    如果你没接触过关键帧动画，可以这样理解：
    - 先记录某个时间点物体在哪里、朝哪边
    - 再记录下一个时间点它在哪里、朝哪边
    - 中间过程交给播放器自动插值

    所以动画本质上就是：
    “在若干时间点，给若干节点，指定位置或旋转的目标值。”
    """
    # 这些值定义了节点在静止状态下的原始位置和朝向。
    base_translation = {
        "WeaponPose": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "BoltGroup": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "MagazineGroup": np.array([0.0, 0.0, 0.0], dtype=np.float64),
    }
    base_euler = {
        "WeaponPose": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "BoltGroup": np.array([0.0, 0.0, 0.0], dtype=np.float64),
        "MagazineGroup": np.array([-22.9, 2.9, 4.6], dtype=np.float64),
    }

    def trans_track(node_name, times, deltas):
        """构造位移动画轨道。

        轨道可以理解成“某个节点在时间轴上的一条属性曲线”。
        这里这条曲线控制的是 `translation`。
        """
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
        """构造旋转轨道，并在这里统一做欧拉角到四元数转换。

        之所以输入时仍然写欧拉角，是因为人工调数更直观；
        但真正导出给 glTF 时仍转换成四元数。
        """
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
    # idle：非常轻微的呼吸/持枪晃动。
    # 振幅故意很小，否则第一人称视角会显得飘。
    clips.append(
        {
            "name": "idle",
            "extras": {"loop": True},
            "tracks": [
                trans_track("WeaponPose", [0.0, 0.5, 1.0, 1.5], [(0.0, 0.0, 0.0), (0.0, 0.004, 0.004), (0.0, 0.0, 0.0), (0.0, -0.002, -0.002)]),
                rot_track("WeaponPose", [0.0, 0.5, 1.0, 1.5], [(0.2, 0.4, 0.0), (0.8, -0.3, -0.4), (0.1, 0.2, 0.1), (0.2, 0.4, 0.0)]),
            ],
        }
    )
    # fire：整枪发生短促后坐，同时 bolt 有一个独立的小后退。
    # 时间很短，因为单发后坐通常是快进快回的动作。
    clips.append(
        {
            "name": "fire",
            "extras": {"loop": False},
            "tracks": [
                trans_track("WeaponPose", [0.0, 0.04, 0.08, 0.16, 0.24], [(0.0, 0.0, 0.0), (0.0, -0.01, 0.08), (0.0, 0.004, 0.03), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
                rot_track("WeaponPose", [0.0, 0.04, 0.08, 0.16, 0.24], [(0.0, 0.0, 0.0), (5.2, 0.0, 1.4), (2.0, 0.0, 0.5), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
                trans_track("BoltGroup", [0.0, 0.03, 0.07, 0.12], [(0.0, 0.0, 0.0), (0.0, 0.0, 0.05), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]),
            ],
        }
    )
    # reload：整把枪先略微倾斜和移动，给“换弹动作”腾出姿态空间；
    # 然后弹匣节点做拔出、下移、回位。
    clips.append(
        {
            "name": "reload",
            "extras": {"loop": False},
            "tracks": [
                trans_track("WeaponPose", [0.0, 0.18, 0.48, 0.82, 1.16], [(0.0, 0.0, 0.0), (0.03, -0.02, 0.05), (0.06, -0.05, 0.10), (0.03, -0.02, 0.05), (0.0, 0.0, 0.0)]),
                rot_track("WeaponPose", [0.0, 0.18, 0.48, 0.82, 1.16], [(0.0, 0.0, 0.0), (12.0, 0.0, 10.0), (22.0, 0.0, 20.0), (8.0, 0.0, 6.0), (0.0, 0.0, 0.0)]),
                trans_track("MagazineGroup", [0.0, 0.2, 0.38, 0.62, 0.90, 1.08], [(0.0, 0.0, 0.0), (0.01, -0.08, 0.02), (0.05, -0.28, 0.04), (0.08, -0.45, 0.05), (0.01, -0.12, 0.01), (0.0, 0.0, 0.0)]),
                rot_track("MagazineGroup", [0.0, 0.2, 0.38, 0.62, 0.90, 1.08], [(0.0, 0.0, 0.0), (6.9, -2.9, -12.6), (12.9, -2.9, -24.6), (14.9, -2.9, -40.6), (4.9, -2.9, -10.6), (0.0, 0.0, 0.0)]),
            ],
        }
    )
    # ads: aim down sights，推进到瞄准姿势。
    # 本质是把整把枪往屏幕中心和更稳定的姿态移动。
    clips.append(
        {
            "name": "ads",
            "extras": {"loop": False},
            "tracks": [
                trans_track("WeaponPose", [0.0, 0.16, 0.34], [(0.0, 0.0, 0.0), (-0.04, 0.02, -0.04), (-0.08, 0.05, -0.08)]),
                rot_track("WeaponPose", [0.0, 0.16, 0.34], [(0.0, 0.0, 0.0), (-1.5, 0.0, -4.5), (-3.0, 0.0, -8.0)]),
            ],
        }
    )
    # sprint：奔跑时把枪压低、外摆，给玩家“正在冲刺”的姿态反馈。
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


def build_gltf():
    """组装完整 glTF 字典，并返回给预览图使用的合并网格。

    这一层是“导出工厂”：
    - 前面构建的是 Python 里的几何和动画数据
    - 这里把它们整理成 glTF 规范要求的 JSON 结构
    """
    groups = build_weapon_groups()
    # 预览图不需要区分节点层级，只需要按材质合并后做静态渲染。
    preview_parts = flatten_group_parts(groups)
    builder = BufferBuilder()
    meshes = []
    materials = [
        {
            "name": "Metal",
            "pbrMetallicRoughness": {"baseColorFactor": [0.12, 0.13, 0.15, 1.0], "metallicFactor": 0.9, "roughnessFactor": 0.5},
        },
        {
            "name": "BlackPolymer",
            "pbrMetallicRoughness": {"baseColorFactor": [0.06, 0.07, 0.08, 1.0], "metallicFactor": 0.1, "roughnessFactor": 0.82},
        },
        {
            "name": "Wood",
            "pbrMetallicRoughness": {"baseColorFactor": [0.49, 0.30, 0.13, 1.0], "metallicFactor": 0.04, "roughnessFactor": 0.92},
        },
        {
            "name": "Skin",
            "pbrMetallicRoughness": {"baseColorFactor": [0.82, 0.65, 0.48, 1.0], "metallicFactor": 0.02, "roughnessFactor": 0.95},
        },
    ]
    material_lookup = {"metal": 0, "black": 1, "wood": 2, "skin": 3}

    mesh_index_lookup = {}
    for group_name, mats in groups.items():
        for material_name, geos in mats.items():
            # 每个“部件组 + 材质”拆成一个 mesh，便于挂到不同节点上。
            # 比如 receiver 里的 metal 和 wood 不会强行揉成一个材质，
            # 否则后面就没法分别指定金属和木头的外观参数。
            geo = merge_geometries(geos)
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

    # 这里不是严格的骨骼蒙皮，而是用节点层级直接驱动刚体部件运动。
    # 你可以把它想象成“把几个硬零件挂在几个可移动的空对象下面”。
    #
    # 层级关系大致是：
    # AK47_Root
    #   └─ WeaponPose         整把枪的大姿态
    #      ├─ ReceiverGroup   主体部分
    #      ├─ MagazineGroup   弹匣
    #      └─ BoltGroup       枪机
    #
    # 这样一来：
    # - 动 WeaponPose = 整把枪一起动
    # - 动 MagazineGroup = 只有弹匣动
    # - 动 BoltGroup = 只有枪机动
    nodes = [
        {"name": "AK47_Root", "children": [1]},
        {"name": "WeaponPose", "translation": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0, 1.0], "children": [2, 3, 4]},
        {"name": "ReceiverGroup", "translation": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0, 1.0], "children": []},
        {"name": "MagazineGroup", "translation": [0.0, 0.0, 0.0], "rotation": list(quat_from_euler_xyz(-22.9, 2.9, 4.6)), "children": []},
        {"name": "BoltGroup", "translation": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0, 1.0], "children": []},
    ]

    group_parent = {"receiver": 2, "mag": 3, "bolt": 4}
    node_lookup = {"WeaponPose": 1, "MagazineGroup": 3, "BoltGroup": 4}

    for group_name, mats in groups.items():
        for material_name in mats.keys():
            mesh_index = mesh_index_lookup[(group_name, material_name)]
            node_index = len(nodes)
            # 每个真实可渲染的 mesh 也对应一个节点，
            # 然后再把这个节点挂到所属的逻辑部件父节点下面。
            nodes.append({"name": f"{group_name}_{material_name}_node", "mesh": mesh_index})
            nodes[group_parent[group_name]].setdefault("children", []).append(node_index)

    clips = build_animations(node_lookup)
    animations = []
    for clip in clips:
        samplers = []
        channels = []
        for track in clip["tracks"]:
            # 每条轨道都拆成时间输入和数值输出两个 accessor。
            # sampler 负责“怎么从时间点 A 过渡到时间点 B”；
            # channel 负责“这条过渡到底作用到哪个节点的哪个属性上”。
            input_accessor = builder.add_accessor(track["times"], FLOAT, "SCALAR")
            output_type = "VEC4" if track["path"] == "rotation" else "VEC3"
            output_accessor = builder.add_accessor(track["values"], FLOAT, output_type)
            sampler_index = len(samplers)
            samplers.append({"input": input_accessor, "output": output_accessor, "interpolation": "LINEAR"})
            channels.append({"sampler": sampler_index, "target": {"node": track["node"], "path": track["path"]}})
        animations.append({"name": clip["name"], "samplers": samplers, "channels": channels, "extras": clip.get("extras", {})})

    gltf = {
        "asset": {"version": "2.0", "generator": "Codex AK47 Animated Python Generator"},
        "scene": 0,
        "scenes": [{"name": "AK47AnimatedScene", "nodes": [0]}],
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
    """用一个简单的软件光照预览把模型渲染成 PNG。

    这不是完整 3D 引擎，也没有真实相机、阴影、材质球系统。
    它做的事情比较像：
    - 把三角形旋转到一个观察角度
    - 丢掉深度后的 Z，只看 2D 投影位置
    - 根据面朝向做一个简化明暗
    - 按远近顺序一层层画到图片上

    目的只是快速产出“资源缩略图”，方便肉眼检查模型轮廓。
    """
    colors = {
        "metal": np.array([46, 48, 52], dtype=np.float64),
        "black": np.array([22, 23, 25], dtype=np.float64),
        "wood": np.array([125, 77, 34], dtype=np.float64),
        "skin": np.array([210, 166, 123], dtype=np.float64),
    }
    triangles = []
    for material, geo in parts.items():
        verts = np.asarray(geo["positions"], dtype=np.float64)
        tri_ids = geo["indices"].reshape(-1, 3)
        for tri in tri_ids:
            # 一个三角形由 3 个顶点决定，这里提前把真实顶点坐标取出来。
            triangles.append((verts[tri], colors[material]))

    points = np.concatenate([tri[0] for tri in triangles], axis=0)
    # 先找出整体包围盒中心，后面旋转和缩放时更容易把物体摆在画面正中。
    center = (points.min(axis=0) + points.max(axis=0)) * 0.5

    def rotation_matrix(yaw_deg, pitch_deg):
        """构造预览相机用的简单旋转矩阵。"""
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
            # 先把三角形绕中心旋转到目标视角。
            p = (tri - center) @ rot.T
            transformed.append((p, color))
            # 这里只保留前两个维度，等价于做一个非常简单的正交投影。
            projected.append(p[:, :2])
        projected = np.concatenate(projected, axis=0)
        minimum = projected.min(axis=0)
        maximum = projected.max(axis=0)
        span = max(maximum[0] - minimum[0], maximum[1] - minimum[1])
        # 根据投影后的整体尺寸自动缩放，让模型稳定地装进画布。
        scale = (min(width, height) - 70) / span
        draw_items = []
        for points_3d, color in transformed:
            # 用平均深度排序，做一个轻量级 painter's algorithm。
            normal = np.cross(points_3d[1] - points_3d[0], points_3d[2] - points_3d[0])
            normal = normal / (np.linalg.norm(normal) or 1.0)
            # normal @ light 就是“面朝光的程度”，值越大就画得越亮。
            shade = max(0.20, float(normal @ light))
            shaded = np.clip(color * (0.54 + 0.56 * shade), 0, 255).astype(int)
            polygon = []
            for x, y, z in points_3d:
                # 把 3D 点换算到最终图片像素坐标。
                sx = (x - (minimum[0] + maximum[0]) * 0.5) * scale + width * 0.5 + view_index * width
                sy = height * 0.54 - (y - (minimum[1] + maximum[1]) * 0.5) * scale
                polygon.append((sx, sy))
            draw_items.append((points_3d[:, 2].mean(), tuple(shaded.tolist()), polygon))
        draw_items.sort(key=lambda item: item[0])
        for _, fill, polygon in draw_items:
            draw.polygon(polygon, fill=fill)
        draw.text((view_index * width + 16, 14), label, fill=(88, 72, 54))

    image.save(output_dir / "weapon01_preview.png")


def write_readme(output_dir, gltf_name, glb_name):
    """生成交付资源的说明文档。

    这一步和建模无关，主要是把导出的资源以说明文档形式整理出来，
    方便之后自己或别人接手时知道有哪些文件、有哪些动画可用。
    """
    readme = f"""# 枪01 - AK-47 Animated

## 1. 资源说明

这是一个面向网页 FPS 使用的 `AK-47` 第一人称武器模型资源，包含基础动作：

- `idle`
- `fire`
- `reload`
- `ads`
- `sprint`

## 2. 动作说明

- `idle`：待机呼吸
- `fire`：单次开火后坐
- `reload`：完整换弹基础动作
- `ads`：推进到瞄准姿态
- `sprint`：奔跑压枪姿态

## 3. 使用建议

- 网页项目优先使用 `{glb_name}`
- `idle` 和 `sprint` 建议循环播放
- `fire`、`reload`、`ads` 建议单次播放

## 4. 文件

- `{gltf_name}`
- `{glb_name}`
- `weapon01_preview.png`
- `weapon01_meta.json`
- `generate_weapon01_animated.py`

## 5. 重新生成

```bash
python3 generate_weapon01_animated.py
```
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def write_meta(output_dir):
    """输出给资产管理或后续流水线读取的元数据。

    这份 JSON 不是 glTF 标准的一部分，而是项目自定义的补充信息。
    常见用途包括：
    - 在资源浏览器里显示武器分类
    - 给游戏逻辑读取武器标签
    - 给后续批处理脚本检索资源属性
    """
    meta = {
        "name": "AK-47",
        "asset_name": "枪01",
        "category": "assault_rifle",
        "style": "web_ready_classic_ak",
        "formats": ["gltf", "glb"],
        "animations": ["idle", "fire", "reload", "ads", "sprint"],
        "weapon_traits": {
            "damage_profile": "high_per_shot",
            "range_profile": "reliable_mid_range",
            "handling": "classic_recoil_fast_bursts",
            "best_for": ["spray_control", "short_bursts", "aggressive_pushes"],
        },
    }
    (output_dir / "weapon01_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    """执行完整导出流程。

    按顺序做的事情是：
    1. 创建输出目录
    2. 生成 glTF 数据
    3. 写出 `model.gltf`
    4. 尝试转成 `model.glb`
    5. 生成预览图
    6. 生成 meta 和 README
    """
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    gltf, preview_parts = build_gltf()
    gltf_path = output_dir / "model.gltf"
    gltf_path.write_text(json.dumps(gltf, ensure_ascii=False, indent=2), encoding="utf-8")

    glb_path = output_dir / "model.glb"
    try:
        # `.gltf` 常是 JSON + 外部/嵌入 buffer；
        # `.glb` 则是打包成单个二进制文件，分发时更方便。
        model = GLTF2().load(str(gltf_path))
        model.save_binary(str(glb_path))
    except Exception as exc:
        # 某些环境缺少完整 glb 依赖时，仍保留可用的 glTF 结果，避免整个流程失败。
        glb_path.write_text(f"GLB export failed.\nReason: {exc}\nUse the glTF file instead.\n", encoding="utf-8")

    render_preview(output_dir, preview_parts)
    write_meta(output_dir)
    write_readme(output_dir, gltf_path.name, glb_path.name)

    print(gltf_path)
    print(glb_path)


if __name__ == "__main__":
    main()
