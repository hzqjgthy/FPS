# 枪01 - AK-47 Animated

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

- 网页项目优先使用 `model.glb`
- `idle` 和 `sprint` 建议循环播放
- `fire`、`reload`、`ads` 建议单次播放

## 4. 文件

- `model.gltf`
- `model.glb`
- `weapon01_preview.png`
- `weapon01_meta.json`
- `generate_weapon01_animated.py`

## 5. 重新生成

```bash
python3 generate_weapon01_animated.py
```
