# 枪03 - Red Dragon Tech Sniper Animated

## 1. 资源说明

这是一个面向网页 FPS 使用的 `Red Dragon Tech Sniper` 第一人称武器模型资源。

- 保留了原始 `枪03` 模型的网格、贴图和主要细节
- 对原始导出结构做了规范化整理
- 增加了适合网页项目使用的基础动作：
  - `idle`
  - `fire`
  - `reload`
  - `ads`
  - `sprint`

## 2. 动作说明

- `idle`：待机呼吸晃动
- `fire`：整枪后坐与镜身抬升
- `reload`：枪身倾斜并带独立弹匣抽离与回装
- `ads`：推进到瞄准姿态
- `sprint`：奔跑压枪姿态

## 3. 结构说明

- 重新建立了 `WeaponPose / ReceiverGroup / MagazineGroup` 层级
- 清理了源文件中的场景位移
- 烘焙了源文件的朝向修正
- 保留了原始材质贴图，并补充了玻璃透明和橙色发光材质设置
- 源模型没有独立枪机网格，所以本版本没有单独的枪机后拉动画

## 4. 使用建议

- 网页项目优先使用 `model.glb`
- `idle` 和 `sprint` 建议循环播放
- `fire`、`reload`、`ads` 建议单次播放
- 如果你后续需要更强的第一人称表现，可以继续在此基础上拆出枪机或拉机柄节点

## 5. 文件

- `model.gltf`
- `model.glb`
- `buffer.bin`
- `viewer.html`
- `viewer-data.js`
- `weapon03_preview.png`
- `weapon03_meta.json`
- `generate_weapon03_animated.py`

## 6. 贴图引用

- 脚本会复制源 PNG 到当前目录
- `model.gltf` 会引用当前目录中的贴图
- `model.glb` 仍会把贴图打包进单文件里

## 7. 重新生成

```bash
python3 generate_weapon03_animated.py
```

## 8. 本地查看

- 直接双击 `viewer.html`
- 查看器会读取同目录下自动生成的 `viewer-data.js`
- 不需要本地起服务
