# 修改优化03 - 真正凸起的立体龙纹

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
