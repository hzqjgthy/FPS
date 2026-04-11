# 敌人02 详细说明

## 1. 资源概述

`敌人02` 是一个面向网页游戏使用场景制作的低模树妖敌人资源，核心目标是:

- 体积小，方便在 Web 项目中快速加载
- 风格明确，适合作为怪物、树妖、木怪或关卡守卫使用
- 动画命名清晰，方便直接接入状态机
- 结构简单，便于后续继续改造或程序化生成变体

当前资源同时提供:

- `model.gltf`: 文本版 glTF，便于检查结构和二次处理
- `model.glb`: 二进制版 glTF，便于网页端直接加载
- `enemy02_preview.png`: 本地预览图
- `enemy02_meta.json`: 简要元信息
- `generate_enemy02.py`: 生成脚本，可重复生成本资源

网页项目里建议优先使用 `model.glb`。

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
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const loader = new GLTFLoader();
const mixerClock = new THREE.Clock();
let mixer;
let actions = {};

loader.load('/assets/model.glb', (gltf) => {
  const enemy = gltf.scene;
  scene.add(enemy);

  mixer = new THREE.AnimationMixer(enemy);

  for (const clip of gltf.animations) {
    actions[clip.name] = mixer.clipAction(clip);
  }

  actions.Idle?.play();
});

function playAction(name, loop = true) {
  if (!mixer || !actions[name]) return;

  Object.values(actions).forEach((action) => action.stop());
  const action = actions[name];
  action.reset();
  action.setLoop(loop ? THREE.LoopRepeat : THREE.LoopOnce, loop ? Infinity : 1);
  action.clampWhenFinished = !loop;
  action.play();
}

function update() {
  const dt = mixerClock.getDelta();
  mixer?.update(dt);
  renderer.render(scene, camera);
  requestAnimationFrame(update);
}

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

- `model.gltf`
- `model.glb`
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

- `model.gltf`: 可编辑的文本 glTF 文件
- `model.glb`: 推荐直接用于网页加载的二进制模型
- `enemy02_preview.png`: 模型静态预览图
- `enemy02_meta.json`: 基本元信息
- `generate_enemy02.py`: 资源生成脚本

---

如果后续你要继续把这个敌人接进项目，优先使用 `model.glb`，并将动作状态按 `Idle -> Walk/Run -> Attack/Hit -> Death` 的思路接入即可。
