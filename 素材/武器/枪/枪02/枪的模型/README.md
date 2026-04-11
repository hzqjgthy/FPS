# 枪02 - SCAR-H Animated

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

- 网页端优先使用 `model.glb`
- `idle` 和 `sprint` 建议循环播放
- `fire`、`reload`、`ads` 建议单次播放
- 如果你后续要做更强的第一人称表现，可以继续细化枪机、枪托、拉机柄、弹匣的可动节点

## 4. 文件

- `model.gltf`
- `model.glb`
- `weapon02_preview.png`
- `weapon02_meta.json`
- `generate_weapon02_animated.py`
