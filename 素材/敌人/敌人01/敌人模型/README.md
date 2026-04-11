# 敌人01 - Raider Animated

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

- 网页项目优先使用 `model.glb`
- `Walk` / `Run` 是原地动作，位移由游戏逻辑控制
- `Attack` / `Hit` / `Death` 建议作为单次动作播放

## 4. 材质说明

- `enemy01_bark.png`：基础树皮 / 布料混合风格贴图参考
- `enemy01_moss.png`：苔藓 / 污渍风格贴图参考

## 5. 文件

- `model.gltf`
- `model.glb`
- `enemy01_bark.png`
- `enemy01_moss.png`
- `enemy01_preview.png`
- `enemy01_meta.json`
- `generate_enemy01.py`

## 6. 重新生成

```bash
python3 generate_enemy01.py
```
