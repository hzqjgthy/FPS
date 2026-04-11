# 修改优化02 - 有浮雕感的龙纹

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
- `有浮雕感龙纹_实现过程.md`

## 3. 重新生成

```bash
python3 build_embossed_dragon_v02.py
```

## 4. 查看

- 直接双击 `viewer.html`
- 或导入 `model.glb` 到 Blender / Babylon / glTF 查看器
