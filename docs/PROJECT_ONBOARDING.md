# Project Onboarding

这份文档是给“只懂 Python、几乎没接触过前端 / TypeScript / Three.js”的你准备的。

目标只有两个：

1. 让你快速知道这个项目现在到底在做什么
2. 让你知道以后要改功能时，应该先看哪里、改哪里

如果你现在打开代码会觉得陌生，这是非常正常的。
这个项目同时混合了几类东西：

- 浏览器页面
- TypeScript 代码
- Three.js 3D 场景
- 游戏循环
- 音频和输入事件
- 一点前端 UI

你可以把它理解成：

- `Python + Pygame` 的“游戏思维”
- 再加上 `浏览器页面`
- 再加上 `Three.js` 负责 3D

它不是后端项目，没有数据库，没有接口服务，没有 Flask / Django 那种 server 逻辑。
这个项目几乎全部运行在浏览器里。

---

## 1. 先用一句话理解项目

这个项目是一个运行在浏览器里的第一人称 FPS 原型。

当前已经有：

- 两张关卡：`dust2_classic`、`desert_fortress`
- 默认开局先进入第一关，并停在暂停界面
- 暂停菜单支持继续、重开本关、选关、游戏帮助
- 玩家第一人称移动、冲刺、跳跃
- 鼠标视角
- 三把武器：AK-47、SCAR-H、Dragon Sniper
- 开火、枪口闪光、后坐力、枪声音效
- 子弹命中墙面 / 地面后的印记系统
- 脚步声、跳跃音效
- 四种敌人
- 敌人追击、近战攻击、受击、死亡、血条
- HUD、准星、暂停菜单、游戏帮助页

当前默认开局武器是：

- `weapon_001_ak47_classic`

也就是 AK-47。

---

## 2. 技术栈，用 Python 的话来理解

### 2.1 `TypeScript` 是什么

你可以把 TypeScript 理解成：

- 本质上还是 JavaScript
- 但额外加了“类型标注”
- 很像 Python 的类型提示 `type hints`

例如：

```ts
const hp: number = 100;
```

它和 Python 里的：

```python
hp: int = 100
```

很像。

差别是：

- Python 类型提示很多时候是“建议”
- TypeScript 在编辑器和编译阶段会更严格地检查

### 2.2 `Vite` 是什么

`Vite` 是这个项目的开发服务器和打包工具。

你可以把它理解成：

- 开发阶段：像一个“本地热更新启动器”
- 发布阶段：像一个“把代码打包成浏览器能运行版本”的工具

对应命令在 `package.json`：

- `npm run start`
- `npm run dev`
- `npm run build`
- `npm run preview`

### 2.3 `Three.js` 是什么

`Three.js` 是浏览器 3D 引擎库。

你可以把它理解成：

- 帮你创建 3D 世界
- 帮你管理摄像机
- 帮你创建模型、灯光、材质、碰撞辅助对象
- 最后把画面渲染到浏览器 `<canvas>` 上

### 2.4 这个项目没有后端

当前这个项目：

- 不连数据库
- 不连服务器 API
- 不做登录
- 不做账号系统

它是一个纯前端 3D 游戏原型。

也就是说，很多逻辑都直接在浏览器里执行：

- 输入
- 玩家移动
- 敌人 AI
- 射击判定
- 音频播放
- HUD 更新

---

## 3. 项目怎么启动

### 3.1 环境要求

你至少需要：

- Node.js
- npm

### 3.2 第一次安装依赖

在项目根目录运行：

```bash
npm install
```

### 3.3 启动开发环境

运行：

```bash
npm run start
```

或者：

```bash
npm run dev
```

启动后通常会看到类似地址：

```text
http://localhost:5173/
```

浏览器打开它即可。

### 3.4 构建项目

运行：

```bash
npm run build
```

这一步会做两件事：

1. TypeScript 检查代码
2. Vite 打包项目

### 3.5 预览生产版

运行：

```bash
npm run preview
```

通常会给出：

```text
http://localhost:4173/
```

### 3.6 进入游戏以后会发生什么

当前启动流程是：

1. 页面打开
2. 默认加载第一关 `dust2_classic`
3. 默认停在暂停界面
4. 点击“进入战场”后才真正开始这局游戏
5. 游戏中按 `Esc` 会重新打开暂停界面

---

## 4. 先学一点最少够用的 TypeScript 语法

你不需要先学完整门语言，先看懂这些就够开始工作了。

### 4.1 `import` / `export`

Python：

```python
from game.player import PlayerController
```

TypeScript：

```ts
import { PlayerController } from './player/PlayerController';
```

导出：

```ts
export class PlayerController {}
```

意思就是：这个类可以被别的文件 import 进来。

### 4.2 `const` 和 `let`

- `const`：变量本身不重新赋值
- `let`：变量后面会变

例如：

```ts
const maxHp = 100;
let currentHp = 100;
currentHp -= 20;
```

### 4.3 类 `class`

Python：

```python
class Player:
    def __init__(self, hp: int):
        self.hp = hp
```

TypeScript：

```ts
class Player {
  private hp: number;

  constructor(hp: number) {
    this.hp = hp;
  }
}
```

你会经常看到：

- `constructor(...)`
- `this.xxx`
- `private`
- `public`
- `readonly`

含义分别是：

- `constructor`：构造函数
- `this.xxx`：当前对象自己的属性
- `private`：只允许类内部使用
- `public`：外部也能访问
- `readonly`：只能赋值一次，后面不能改

### 4.4 `interface`

你可以把 `interface` 理解成“数据结构约定”。

例如：

```ts
export interface WeaponDefinition {
  id: string;
  label: string;
}
```

意思是：凡是武器定义对象，都应该长成这个样子。

你可以先把它近似理解成：

- `TypedDict`
- `dataclass` 的字段约定
- 协议 / 约定

### 4.5 `async` / `await`

和 Python 非常像。

Python：

```python
async def load():
    data = await fetch()
```

TypeScript：

```ts
async function load() {
  const data = await fetchSomething();
}
```

### 4.6 `Promise`

你可以先把 `Promise` 理解成：

- JavaScript 里“将来会完成的结果”

很像 Python 里异步世界中的 future / coroutine result。

### 4.7 `new URL(..., import.meta.url).href`

这个项目里你会经常看到：

```ts
new URL('../../../素材/角色/脚步声01.mp3', import.meta.url).href
```

它的作用是：

- 告诉 Vite：这个文件是项目资源
- 构建时请把它一起带走
- 最后变成浏览器能访问的真实地址

也就是说，音频和模型并不是“手写字符串路径随便读”的，而是通过打包器接管的。

---

## 5. 现在这个项目的真实架构

这是当前最重要的一章。

你只要把这个结构记住，后面读代码会顺很多。

### 5.1 最外层入口

文件：

- `src/main.ts`

它只做两件事：

1. 找到页面里的 `#app`
2. 创建并启动 `GameDirector`

你可以把它理解成：

- Python 项目里的 `main.py`

### 5.2 应用层总控

文件：

- `src/game/GameDirector.ts`

这是“整局游戏切换器”。

它负责：

- 从 `gameSelection.ts` 读取默认开局配置
- 创建当前这一局的 `GameApp`
- 控制开局暂停界面
- 控制 `Esc` 暂停
- 控制重开当前关卡
- 控制切换关卡

也就是说：

- `GameDirector` 管“这一局怎么被创建、重开、切换”
- `GameApp` 管“这一局里面每一帧怎么跑”

### 5.3 单局运行时

文件：

- `src/game/GameApp.ts`

这是单局游戏真正的总装配器。

它负责：

- 创建 Three.js 渲染器 `renderer`
- 创建场景 `scene`
- 创建摄像机 `camera`
- 从关卡工厂创建世界
- 创建输入系统 `InputController`
- 创建玩家 `PlayerController`
- 创建敌人总管理器 `EnemyManager`
- 创建当前武器视图模型
- 创建 HUD
- 创建枪声、脚步声、跳跃声
- 创建 `ShotResolver`
- 创建 `BulletImpactSystem`
- 驱动每一帧主循环

### 5.4 内容配置层

这层负责“项目里有什么内容”和“默认用什么内容”。

核心文件：

- `src/game/content/gameSelection.ts`
- `src/game/content/weapons/weaponCatalog.ts`
- `src/game/content/enemies/enemyCatalog.ts`
- `src/game/content/levels/levelCatalog.ts`
- `src/game/content/ui/gameHelpContent.ts`

你可以把它理解成：

- `gameSelection.ts`：默认开局选项
- `weaponCatalog.ts`：武器名册
- `enemyCatalog.ts`：敌人数值和整体大小名册
- `levelCatalog.ts`：关卡名册
- `gameHelpContent.ts`：帮助页操作说明

### 5.5 运行时装配层

这层负责把“纯配置”接到“真正可运行的对象”。

典型文件：

- `src/game/enemies/EnemyRuntimeCatalog.ts`
- `src/game/weapons/models/*.ts`
- `src/game/world/levels/*`

你可以把它理解成：

- 内容层告诉你“有什么”
- 运行时装配层告诉你“怎么把它真正跑起来”

---

## 6. 这个项目运行时，到底发生了什么

这是你最需要理解的主线。

### 6.1 页面打开后

顺序大概是：

1. `src/main.ts` 创建 `GameDirector`
2. `GameDirector` 从 `gameSelection.ts` 读取默认开局内容
3. `GameDirector` 创建当前这一局的 `GameApp`
4. `GameApp` 创建世界、玩家、敌人、武器、HUD、音频系统
5. `GameDirector` 显示暂停菜单
6. 你点击“进入战场”
7. `GameDirector` 调用 `GameApp.resume()`
8. `GameApp` 开始每帧主循环

### 6.2 `GameApp` 构造函数大概做什么

你可以把构造函数理解成“单局初始化”。

大致顺序是：

1. 创建 DOM 容器
2. 创建 Three.js 渲染器
3. 设置渲染器阴影、色调映射、输出色彩空间
4. 调用当前关卡工厂，生成世界
5. 创建输入系统
6. 创建 HUD
7. 创建玩家
8. 创建敌人系统
9. 创建子弹印记系统
10. 创建命中解析器
11. 创建当前武器视图模型
12. 绑定窗口 resize
13. 绑定点击进入 pointer lock

### 6.3 `GameApp.start()` 做什么

`GameApp.start()` 不会立刻开始主循环。

它主要负责：

1. 初始化敌人系统
2. 更新初始 HUD
3. 把一局游戏准备好

真正开始跑是在 `resume()` 之后。

### 6.4 `animate()` 主循环顺序

当前每帧大逻辑顺序是：

1. 计算这一帧经过了多少时间 `deltaSeconds`
2. 检查是否按下 `Esc`
3. 更新玩家状态
4. 如果要切枪，切换当前武器
5. 更新敌人状态
6. 更新武器表现
7. 如果这一帧真正开火：
   - 用 `ShotResolver` 判断打中敌人还是打中世界
   - 播放枪声
   - 对敌人结算伤害，或者生成世界表面子弹印记
8. 如果玩家跳跃，播放跳跃声
9. 如果脚步触发，播放脚步声
10. 如果敌人打到玩家，扣血
11. 更新 HUD
12. 更新子弹印记淡出
13. 渲染场景
14. 请求下一帧

如果你只想快速理解，可以记住一句话：

`GameApp.animate()` = 这个游戏的心跳。

---

## 7. 目录结构，先整体看一遍

当前最重要的目录：

```text
src/
  main.ts
  style.css
  game/
    GameDirector.ts
    GameApp.ts
    audio/
    combat/
    config/
    content/
    enemies/
    effects/
    input/
    player/
    ui/
    weapons/
    world/
docs/
  PROJECT_ONBOARDING.md
  TUNING_GUIDE.md
素材/
  角色/
  武器/
  敌人/
```

你可以这样记：

- `src/main.ts`：浏览器入口
- `src/style.css`：页面和 HUD 样式
- `src/game/GameDirector.ts`：整局控制器
- `src/game/GameApp.ts`：单局总装配器
- `src/game/input`：输入
- `src/game/player`：玩家
- `src/game/weapons`：武器协议和第一人称武器模型
- `src/game/enemies`：敌人系统
- `src/game/world`：地图
- `src/game/ui`：HUD 和暂停菜单
- `src/game/content`：内容注册表和默认开局配置
- `src/game/content/ui`：暂停菜单帮助页内容
- `src/game/config`：系统级参数
- `src/game/combat`：命中解析
- `src/game/effects`：子弹印记等特效系统

---

## 8. 先建立一个正确的“架构脑图”

这个项目不是把所有逻辑堆在一个文件里，而是分层的。

最推荐你的脑中结构是：

### 8.1 默认选择层

文件：

- `src/game/content/gameSelection.ts`

作用：

- 决定默认玩哪张图
- 决定默认拿什么武器
- 决定当前允许刷哪些敌人

这是“默认开局开关”。

### 8.2 注册表层

文件：

- `src/game/content/levels/levelCatalog.ts`
- `src/game/content/weapons/weaponCatalog.ts`
- `src/game/content/enemies/enemyCatalog.ts`

作用：

- 定义项目里有哪些关卡
- 定义项目里有哪些武器
- 定义项目里有哪些敌人

这是“内容名册”。

### 8.3 运行时层

文件：

- `src/game/GameApp.ts`
- `src/game/player/PlayerController.ts`
- `src/game/enemies/EnemyManager.ts`
- `src/game/enemies/EnemyController.ts`
- `src/game/combat/ShotResolver.ts`
- `src/game/effects/BulletImpactSystem.ts`

作用：

- 真正每帧运行
- 真正处理输入、移动、战斗、AI、音频、特效

这是“游戏正在发生的部分”。

### 8.4 表现层

文件：

- `src/game/ui/Hud.ts`
- `src/game/ui/PauseMenu.ts`
- `src/style.css`
- `src/game/weapons/models/*.ts`
- `src/game/enemies/models/*.ts`
- `src/game/enemies/EnemyHealthBar.ts`

作用：

- 负责玩家看到的界面和视觉表现
- 不一定直接负责游戏规则

---

## 9. 每个核心文件到底做什么

这一章非常关键。

## 9.1 `src/main.ts`

职责：

- 项目入口

你可以把它理解成：

- Python 项目里的 `main.py`

它几乎不做业务逻辑。

## 9.2 `src/game/GameDirector.ts`

职责：

- 应用层总控
- 负责默认开局
- 负责开局暂停界面
- 负责继续游戏
- 负责重启本关卡
- 负责切换关卡
- 负责在主菜单、选关页、帮助页之间切换

如果把整个项目比作一个 Python 游戏项目，那么 `GameDirector` 很像：

- 管理场景切换的外层控制器
- 管理菜单和“重新开始这一局”的逻辑

## 9.3 `src/game/GameApp.ts`

职责：

- 初始化一局游戏里的所有系统
- 串联所有系统
- 驱动每帧更新

如果把它类比成 Python 游戏，它很像：

- 创建窗口内的世界
- 创建角色
- 创建敌人
- 每一帧 `update()`
- 每一帧 `render()`

你在这里最该优先看什么：

1. 构造函数里，哪些对象被创建了
2. `animate()` 里，更新顺序是什么
3. 开火判定是在什么时候结算的
4. HUD 在什么时候更新

## 9.4 `src/game/input/InputController.ts`

职责：

- 管理键盘输入
- 管理鼠标移动
- 管理鼠标左键开火
- 管理 pointer lock
- 管理 `Esc` 暂停
- 管理数字键 `1` 切枪

它不直接移动玩家。
它只负责记录：

- 哪些键被按住
- 鼠标这一帧移动了多少
- 是否请求跳跃
- 是否在按住开火
- 是否请求暂停
- 是否请求切枪

## 9.5 `src/game/player/PlayerController.ts`

职责：

- 玩家视角旋转
- WASD 平面移动
- 冲刺
- 跳跃
- 与场景碰撞
- 镜头呼吸和移动晃动
- 脚步触发节奏
- 相机后坐力偏移恢复

这是玩家系统的核心文件。

### 重要概念

- `yawPivot`：负责水平旋转
- `pitchPivot`：负责上下俯仰

第一人称相机常见做法就是：

- 外层负责左右转头
- 内层负责上下抬头低头

这样逻辑更清楚，也更稳定。

## 9.6 `src/game/world/levels/<levelId>/index.ts`

职责：

- 作为单张关卡的总入口
- 组合地图布局和关卡运行时数据
- 返回碰撞体、出生点、敌人刷新点、世界表面命中区域

现在地图层已经拆成了：

- `src/game/world/shared/desertWorldKit.ts`
  负责沙漠风格关卡共用搭建工具
- `src/game/world/levels/dust2_classic/index.ts`
- `src/game/world/levels/dust2_classic/layout.ts`
- `src/game/world/levels/dust2_classic/worldData.ts`
- `src/game/world/levels/desert_fortress/index.ts`
- `src/game/world/levels/desert_fortress/layout.ts`
- `src/game/world/levels/desert_fortress/worldData.ts`

推荐这样理解：

- `index.ts`：总装配
- `layout.ts`：地图几何、灯光、碰撞、可命中世界表面
- `worldData.ts`：出生点和刷怪点

## 9.7 `src/game/content/gameSelection.ts`

职责：

- 选择默认开局内容

目前最重要的常量：

- `ACTIVE_LEVEL_ID`
- `ACTIVE_WEAPON_ID`
- `EQUIPPED_WEAPON_IDS`
- `ENABLED_ENEMY_IDS`

如果你只是想快速切换默认内容，而不想改底层逻辑，优先改这个文件。

## 9.8 `src/game/content/levels/levelCatalog.ts`

职责：

- 关卡注册表

这里定义的是“关卡元数据”，包括：

- 关卡 id
- 关卡显示名称
- HUD 顶部标签
- 暂停菜单文案
- `createWorld()` 地图工厂

也就是说：

- `levels/<levelId>/index.ts` 负责组合关卡
- `levels/<levelId>/layout.ts` 真正负责建图
- `levels/<levelId>/worldData.ts` 负责出生点和刷怪点
- `levelCatalog.ts` 负责把这张图注册到系统里

## 9.9 `src/game/config/systemTuning.ts`

职责：

- 存放系统级调参

例如：

- 鼠标灵敏度
- 玩家速度
- 冲刺倍率
- 跳跃高度
- 跳跃时长
- 镜头呼吸幅度
- 行走 bob 幅度
- 脚步声音量
- 子弹印记数量上限
- 子弹印记表面偏移量

这个文件控制的是：

- 共用手感
- 系统级表现

而不是单把武器或单种敌人的独立数据。

## 9.10 `src/game/content/weapons/weaponCatalog.ts`

职责：

- 武器注册表

目前已经有三把枪：

- `weapon_001_ak47_classic`
- `weapon_002_scar_h_battle_rifle`
- `weapon_003_red_dragon_tech_sniper`

它定义了：

- 武器名称
- HUD 弹药文本
- 帮助文字
- 数值 `tuning`
- 音效配置 `audio`
- 子弹印记配置 `impact`
- 如何创建对应的第一人称武器视图模型

### 重要理解

当前这个文件虽然用了内部默认值和辅助函数减少重复输入，但最终导出的每把枪仍然是完整配置对象。

### 如果你想改武器数值

例如：

- 身体伤害
- 爆头伤害
- 射速
- 最大命中距离
- 后坐力强度
- 子弹印记大小和持续时间

优先改这里。

## 9.11 `src/game/weapons/WeaponTypes.ts`

职责：

- 定义武器系统公共接口

这个文件对新手特别重要，因为它告诉你：

- 武器定义对象应该长什么样
- 武器 update 每帧要返回什么
- 音频配置需要哪些字段
- 子弹印记配置需要哪些字段

你可以把它理解成：

- 武器系统的协议文件

## 9.12 `src/game/weapons/models/AK47ViewModel.ts`

职责：

- 创建玩家手上的 AK-47
- 更新武器摆动
- 更新开火闪光
- 更新武器自己的后坐力表现

这个文件是纯“第一人称手上武器表现”。
它不直接决定敌人掉多少血。

那伤害是谁决定的？

- `weaponCatalog.ts` 里的数值
- `EnemyManager.ts` 的命中结算

当前它已经是素材驱动：

- 使用 `素材/武器/枪/枪01/枪的模型/model.glb`

## 9.13 `src/game/weapons/models/ScarHViewModel.ts`

职责：

- 创建玩家手上的 SCAR-H
- 接入模型动画
- 仍然遵守统一的 `WeaponViewModel` 协议

当前它也是素材驱动：

- 使用 `素材/武器/枪/枪02/枪的模型/model.glb`

## 9.14 `src/game/weapons/models/RedDragonSniperViewModel.ts`

职责：

- 创建玩家手上的 Dragon Sniper
- 接入 `idle / fire / reload / ads / sprint` 动画
- 保留项目统一的后坐、枪口闪光和镜头联动逻辑

当前它是素材驱动：

- 使用 `素材/武器/枪/枪03/枪的模型/model.glb`

它更接近 SCAR-H 这种“动画模型直接接入”的类型，而不是纯代码拼装的武器。

## 9.15 `src/game/audio/FootstepAudio.ts`

职责：

- 播放角色脚步音效

当前脚步声素材来自：

- `素材/角色/脚步声01.mp3`

### 重点理解

虽然现在只保留了 1 个脚步声文件，但代码里仍然用了“音频池”。

这样做的原因是：

- 走路时脚步触发比较密
- 如果只用 1 个 `Audio` 实例，新的播放会把上一次直接打断
- 用多个播放器轮流播同一个文件，连续移动时声音会更自然

## 9.16 `src/game/audio/GunfireAudio.ts`

职责：

- 播放枪声

它也用了“音频池”的思路。
原因和脚步声一样：连发时更自然。

## 9.17 `src/game/audio/JumpAudio.ts`

职责：

- 播放跳跃音效

当前素材路径：

- `素材/角色/跳跃01.mp3`

## 9.18 `src/game/content/enemies/enemyCatalog.ts`

职责：

- 敌人数值注册表

目前有四种敌人：

1. `enemy_001_raider`
2. `enemy_002_tree_brute`
3. `enemy_003_tree_guardian`
4. `enemy_004_rotwood_overlord`

### 它做了什么

1. 维护敌人的内部默认值和辅助生成函数
2. 生成每种敌人的完整数值配置
3. 列出项目里有哪些敌人种类可供启用

### 重要理解

这个文件不负责每帧追击逻辑。
这个文件也不直接负责模型加载。

它负责的是：

- “这种敌人是什么”
- “这种敌人有哪些数值”
- “这种敌人在系统里叫什么”

## 9.19 `src/game/enemies/EnemyRuntimeCatalog.ts`

职责：

- 把敌人数值配置接到真实模型和动画

它会：

- 读取 `enemyCatalog.ts` 里的纯配置
- 按需动态导入 `RaiderModel`、`TreeBruteModel`、`TreeGuardianModel`、`RotwoodOverlordModel`
- 最终组装成 `EnemyManager` 真正可用的运行时敌人原型

这一层非常重要，因为它把：

- 内容层
- 运行时表现层

接起来了。

## 9.20 `src/game/enemies/EnemyManager.ts`

职责：

- 创建所有敌人
- 逐帧更新所有敌人
- 统一处理玩家射击敌人的命中逻辑

你可以把它理解成：

- 敌人总管理器

### 重要方法

#### `initialize()`

根据：

- 当前启用的敌人 id
- 地图给出的敌人出生点

创建敌人实例。

它现在是显式初始化的，不再藏在构造函数里。

#### `update()`

循环更新所有敌人，并统计：

- 这一帧敌人对玩家造成的总伤害
- 当前还活着的敌人数

#### `findNearestShotHit()` / `applyShotHit()`

它们负责：

- 找出哪只敌人真正被射线命中
- 根据当前武器数值结算身体伤害或爆头伤害

## 9.21 `src/game/enemies/EnemyController.ts`

职责：

- 单个敌人的 AI 和状态机

你可以把它理解成：

- 一只敌人的脑子

它处理什么：

- 是否发现玩家
- 是否追击
- 是否进入攻击状态
- 什么时候真正对玩家造成伤害
- 什么时候死亡
- 与场景碰撞
- 当前脚下支撑高度
- 子弹射线是否命中它的命中体

## 9.22 `src/game/enemies/EnemyVisual.ts`

职责：

- 规定“敌人逻辑层”和“敌人表现层”的接口

这是非常重要的设计点。

因为这样一来：

- `EnemyController` 只负责 AI 和判定
- `models/*.ts` 只负责表现

也就是说：

- 逻辑和美术表现被拆开了

这对未来扩展很重要。

## 9.23 `src/game/enemies/models/*.ts`

包括：

- `RaiderModel.ts`
- `TreeBruteModel.ts`
- `TreeGuardianModel.ts`
- `RotwoodOverlordModel.ts`

这些文件负责：

- 加载外部 `model.glb`
- 接入动画
- 切换 `Idle / Walk / Run / Attack / Hit / Death`
- 挂接隐藏命中体
- 挂接血条

这一层只负责表现，不负责 AI。

## 9.24 `src/game/enemies/EnemyHealthBar.ts`

职责：

- 给敌人头顶画一个始终朝向相机的血条

它的实现方式不是两个 3D 条，而是：

1. 先画到 Canvas
2. 再把 Canvas 做成纹理
3. 再贴到 `Sprite` 上

这么做的好处是：

- 不容易出现不同角度下血条错位
- 更稳定

## 9.25 `src/game/combat/ShotResolver.ts`

职责：

- 统一判断这一枪到底打中了什么

它会：

1. 从摄像机位置和朝向生成射线
2. 先检查敌人命中
3. 再检查世界表面命中
4. 取最近的有效命中结果

返回结果只有三种：

- `enemy`
- `world`
- `none`

你可以把它理解成：

- 射击命中解析器

## 9.26 `src/game/effects/BulletImpactSystem.ts`

职责：

- 在墙面 / 地面生成子弹印记
- 控制印记数量上限
- 控制印记逐渐淡出

它不关心敌人伤害。
它只关心：

- 打到世界表面以后，印记怎么显示

## 9.27 `src/game/ui/Hud.ts`

职责：

- 管理屏幕上的 2D 战斗界面 DOM

它不是 Three.js 里的 3D 物体。
它就是普通网页 DOM。

包括：

- 顶部状态条
- 准星
- 底部武器信息
- 受伤红色覆盖层
- 死亡提示

它接收两类数据：

1. `presentation`
   - 关卡和武器文案
2. `combat state`
   - 血量、敌人数、击杀数、受伤强度、是否死亡

## 9.28 `src/game/ui/PauseMenu.ts`

职责：

- 管理暂停菜单 DOM

包括：

- 开局“进入战场”
- 游戏中“继续游戏”
- “重启本关卡”
- “选择关卡”
- “游戏帮助”
- “返回菜单”
- 关卡列表按钮

你可以把它理解成：

- 开局面板 + 暂停面板 + 帮助面板

## 9.29 `src/game/content/ui/gameHelpContent.ts`

职责：

- 集中维护暂停菜单帮助页里的键位说明和描述文本

它现在负责的内容包括：

- 前进、后退、左移、右移
- 冲刺
- 跳跃
- 视角控制
- 开火
- 切枪
- 暂停

为什么单独放一个文件？

因为这类内容本质上是“展示数据”，不是 UI 逻辑。
这样以后如果你新增：

- 换弹
- 下蹲
- 开镜
- 投掷物
- 技能键

只需要在这里补一条配置，不用直接改 `PauseMenu.ts` 的结构。

## 9.30 `src/style.css`

职责：

- 定义整个页面样式

包括：

- 页面背景
- HUD 样式
- 准星样式
- 暂停菜单样式
- 帮助页样式
- 按钮样式
- 死亡提示样式

如果你想改：

- HUD 外观
- 暂停菜单外观
- 帮助页外观
- 准星样式
- 字体和配色

优先改这里。

---

## 10. 一个非常重要的“数据流”理解

你可以把这个项目的主要数据流记成下面这几条。

### 10.1 开局链路

`main.ts`
-> `GameDirector.ts`
-> `gameSelection.ts`
-> `GameApp.ts`

意思是：

1. 页面启动
2. 创建应用层控制器
3. 读取默认开局配置
4. 创建当前这一局

### 10.2 关卡链路

`gameSelection.ts`
-> `levelCatalog.ts`
-> `levels/<levelId>/index.ts`
-> `GameApp.ts`

意思是：

1. 先决定默认是哪张图
2. 再从关卡注册表里取定义
3. 再真正创建 3D 场景
4. 再让 `GameApp` 使用这张图返回的数据

### 10.3 武器链路

`gameSelection.ts`
-> `weaponCatalog.ts`
-> `models/AK47ViewModel.ts` / `models/ScarHViewModel.ts` / `models/RedDragonSniperViewModel.ts`
-> `GameApp.ts`

意思是：

1. 先决定当前武器 id
2. 再从武器注册表拿配置
3. 再创建对应的视图模型
4. `GameApp` 每帧更新武器，并在开火时做命中结算

### 10.4 敌人链路

`gameSelection.ts`
-> `enemyCatalog.ts`
-> `EnemyRuntimeCatalog.ts`
-> `EnemyManager.ts`
-> `EnemyController.ts`
-> `models/*.ts`

意思是：

1. 先决定本局允许哪些敌人
2. 敌人内容注册表提供纯数值定义
3. 运行时装配层把这些定义接到具体视觉模型
4. 敌人管理器生成敌人
5. 每个敌人控制器负责自己的 AI
6. 每个敌人控制器驱动对应视觉表现

### 10.5 开火命中链路

`Mouse Left`
-> `InputController`
-> `GameApp`
-> `WeaponViewModel.update()`
-> `ShotResolver`
-> `EnemyManager` 或 `BulletImpactSystem`

意思是：

1. 玩家按住左键
2. 输入系统记录开火状态
3. 武器模型判断这一帧是否真的开火
4. 如果开火，用 `ShotResolver` 判断打中敌人还是打中墙
5. 打中敌人就结算伤害
6. 打中墙面 / 地面就生成印记

---

## 11. 你以后想改功能，该改哪里

这一节最实用。

### 11.1 想换默认关卡

改：

- `src/game/content/gameSelection.ts`

字段：

- `ACTIVE_LEVEL_ID`

### 11.2 想换默认武器

改：

- `src/game/content/gameSelection.ts`

字段：

- `ACTIVE_WEAPON_ID`

### 11.3 想控制按数字键 `1` 能切哪些枪

改：

- `src/game/content/gameSelection.ts`

字段：

- `EQUIPPED_WEAPON_IDS`

### 11.4 想只保留一种敌人

改：

- `src/game/content/gameSelection.ts`

字段：

- `ENABLED_ENEMY_IDS`

例如只保留普通敌人：

```ts
export const ENABLED_ENEMY_IDS = ['enemy_001_raider'] as const;
```

### 11.5 想调玩家移动速度

改：

- `src/game/config/systemTuning.ts`

字段：

- `player.moveSpeed`

### 11.6 想调冲刺速度

改：

- `src/game/config/systemTuning.ts`

字段：

- `player.sprintMultiplier`

### 11.7 想调跳跃高度和时间

改：

- `src/game/config/systemTuning.ts`

字段：

- `player.jumpHeight`
- `player.jumpDuration`

### 11.8 想调鼠标灵敏度

改：

- `src/game/config/systemTuning.ts`

字段：

- `camera.lookSensitivity`

### 11.9 想调武器伤害

改：

- `src/game/content/weapons/weaponCatalog.ts`

字段：

- `bodyDamage`
- `headshotDamage`

### 11.10 想调武器射速

改：

- `src/game/content/weapons/weaponCatalog.ts`

字段：

- `fireInterval`

### 11.11 想调后坐力

改：

- `src/game/content/weapons/weaponCatalog.ts`

字段：

- `recoilKickBack`
- `recoilRotationX`
- `recoilRotationZ`
- `recoilRecovery`
- `cameraKickVertical`
- `cameraKickHorizontal`

### 11.12 想调枪的大小

改：

- `src/game/content/weapons/weaponCatalog.ts`

字段：

- `presentation.viewModelScale`

### 11.13 想调子弹印记数量和表面偏移

改：

- `src/game/config/systemTuning.ts`

字段：

- `effects.maxBulletMarks`
- `effects.bulletMarkSurfaceOffset`

### 11.14 想调某把枪的印记大小和存在时间

改：

- `src/game/content/weapons/weaponCatalog.ts`

字段：

- `impact.markSize`
- `impact.markOpacity`
- `impact.lifetimeSeconds`
- `impact.fadeDurationSeconds`

### 11.15 想调敌人生命值和攻击伤害

改：

- `src/game/content/enemies/enemyCatalog.ts`

字段：

- `maxHealth`
- `attackDamage`

### 11.16 想调敌人的整体大小

改：

- `src/game/content/enemies/enemyCatalog.ts`

字段：

- `sizeScale`

说明：

- 这是严格同比例缩放，不只是视觉放大。
- 它会同时影响敌人的模型、命中体、逻辑碰撞尺寸和攻击距离。

### 11.17 想调敌人追击速度

改：

- `src/game/content/enemies/enemyCatalog.ts`

字段：

- `moveSpeed`

### 11.18 想调敌人警戒范围

改：

- `src/game/content/enemies/enemyCatalog.ts`

字段：

- `alertRange`
- `forgetRange`

### 11.19 想调敌人爆头范围

改：

- `src/game/enemies/models/RaiderModel.ts`
- `src/game/enemies/models/TreeBruteModel.ts`
- `src/game/enemies/models/TreeGuardianModel.ts`
- `src/game/enemies/models/RotwoodOverlordModel.ts`

重点看：

- `buildHitVolumes()`

### 11.20 想调地图布局

改：

- `src/game/world/levels/desert_fortress/layout.ts`
- `src/game/world/levels/dust2_classic/layout.ts`

### 11.21 想调出生点和刷怪点

改：

- `src/game/world/levels/desert_fortress/worldData.ts`
- `src/game/world/levels/dust2_classic/worldData.ts`

### 11.22 想调 HUD 样式

改：

- `src/style.css`

### 11.23 想调 HUD 结构和内容

改：

- `src/game/ui/Hud.ts`

### 11.24 想改暂停菜单结构和按钮

改：

- `src/game/ui/PauseMenu.ts`
- `src/game/GameDirector.ts`

### 11.25 想改帮助页里的键位说明

改：

- `src/game/content/ui/gameHelpContent.ts`

---

## 12. 给 Python 使用者的“阅读顺序建议”

如果你一口气看完整个项目，会非常容易晕。

推荐你按这个顺序读。

### 第 1 轮，只看运行主线

1. `src/main.ts`
2. `src/game/GameDirector.ts`
3. `src/game/GameApp.ts`
4. `src/game/content/gameSelection.ts`
5. `src/game/content/levels/levelCatalog.ts`
6. `src/game/world/levels/dust2_classic/index.ts`

这一轮目标不是看细节，而是回答一个问题：

“页面一打开，这局游戏是怎么被拼出来的？”

### 第 2 轮，看玩家和输入

1. `src/game/input/InputController.ts`
2. `src/game/player/PlayerController.ts`

这一轮回答：

“WASD、鼠标、跳跃、冲刺、Esc、切枪是怎么工作的？”

### 第 3 轮，看武器和命中

1. `src/game/weapons/WeaponTypes.ts`
2. `src/game/content/weapons/weaponCatalog.ts`
3. `src/game/weapons/models/AK47ViewModel.ts`
4. `src/game/weapons/models/ScarHViewModel.ts`
5. `src/game/weapons/models/RedDragonSniperViewModel.ts`
6. `src/game/combat/ShotResolver.ts`
7. `src/game/effects/BulletImpactSystem.ts`

这一轮回答：

“武器配置在哪里？开火怎么结算？子弹印记在哪？”

### 第 4 轮，看敌人

1. `src/game/content/enemies/enemyCatalog.ts`
2. `src/game/enemies/EnemyRuntimeCatalog.ts`
3. `src/game/enemies/EnemyManager.ts`
4. `src/game/enemies/EnemyController.ts`
5. `src/game/enemies/EnemyVisual.ts`
6. `src/game/enemies/models/RaiderModel.ts`
7. `src/game/enemies/models/TreeBruteModel.ts`
8. `src/game/enemies/models/TreeGuardianModel.ts`
9. `src/game/enemies/models/RotwoodOverlordModel.ts`
10. `src/game/enemies/EnemyHealthBar.ts`

这一轮回答：

“敌人怎么出生？怎么追我？怎么被打死？爆头范围在哪？”

### 第 5 轮，看 UI 和音效

1. `src/game/ui/Hud.ts`
2. `src/game/ui/PauseMenu.ts`
3. `src/game/content/ui/gameHelpContent.ts`
4. `src/style.css`
5. `src/game/audio/FootstepAudio.ts`
6. `src/game/audio/GunfireAudio.ts`
7. `src/game/audio/JumpAudio.ts`

这一轮回答：

“屏幕上的元素和声音是怎么来的？”

---

## 13. 给你一个“最小工作流”，帮助你开始改项目

如果你是完全小白，不要上来就改大功能。
先做 5 个最小练习。

### 练习 1：把玩家速度改快

改：

- `src/game/config/systemTuning.ts`

找到：

- `player.moveSpeed`

把它从 `15` 改成 `18`。

然后运行：

```bash
npm run start
```

进游戏体验差异。

### 练习 2：把默认武器切成 SCAR-H

改：

- `src/game/content/gameSelection.ts`

把：

```ts
export const ACTIVE_WEAPON_ID = 'weapon_001_ak47_classic';
```

改成：

```ts
export const ACTIVE_WEAPON_ID = 'weapon_002_scar_h_battle_rifle';
```

这样你会马上理解：

- 默认开局内容是从哪里来的

### 练习 3：把 AK 身体伤害改成 70

改：

- `src/game/content/weapons/weaponCatalog.ts`

找到：

- `bodyDamage: 50`

改成：

```ts
bodyDamage: 70
```

然后试玩，观察敌人是否更快死亡。

### 练习 4：只保留一种敌人

改：

- `src/game/content/gameSelection.ts`

改成：

```ts
export const ENABLED_ENEMY_IDS = ['enemy_001_raider'] as const;
```

这样你就能很直观地理解：

- `gameSelection.ts` 控制的是“本局内容开关”

### 练习 5：把子弹印记保留更久

改：

- `src/game/content/weapons/weaponCatalog.ts`

找到某把枪的：

- `lifetimeSeconds`
- `fadeDurationSeconds`

把它们调大，再进游戏测试打墙效果。

这会帮助你理解：

- 武器数值和表现是怎么结合的

---

## 14. `Three.js` 最少够用词典

你不需要先学完整个 Three.js，先认识这些对象就够用了。

### `Scene`

场景，所有 3D 对象的大容器。

### `PerspectiveCamera`

透视摄像机，相当于玩家眼睛。

### `WebGLRenderer`

渲染器，把 3D 场景画到浏览器画布上。

### `Group`

3D 组，用来装多个对象。

很像：

- 一个节点
- 一个容器
- 一个父对象

### `Mesh`

网格对象，通常由：

- Geometry
- Material

组成。

### `Box3`

3D 包围盒，经常用来做简单碰撞。

### `Vector3`

三维向量：

- x
- y
- z

### `Ray`

射线。

### `Raycaster`

射线检测工具，经常用于：

- 子弹命中
- 鼠标点击检测

### `AnimationMixer`

Three.js 的动画播放器。

当前敌人模型和第二把枪都在用。

### `Sprite`

始终朝向相机的 2D 精灵。

当前敌人血条会用到这个思路。

---

## 15. 这个项目里“规则”和“表现”是分开的

这是一个你越早理解越好的设计点。

### 规则层例子

- 玩家是否能移动
- 敌人是否发现玩家
- 子弹是否命中
- 敌人掉多少血
- 玩家掉多少血

### 表现层例子

- 武器如何摆动
- 枪口闪光长什么样
- 敌人挥砍时手臂怎么摆
- 血条怎么画
- HUD 怎么显示
- 子弹印记长什么样

### 为什么要分开

因为这样以后改起来更稳：

- 改动画，不容易误伤逻辑
- 改逻辑，不容易破坏外观

当前项目中最典型的分离就是：

- `EnemyController.ts` 负责逻辑
- `models/*.ts` 负责表现

---

## 16. 资源文件是怎么被引用的

当前项目里的音频和模型资源主要在 `素材` 文件夹。

例如：

- `素材/角色/脚步声01.mp3`
- `素材/角色/跳跃01.mp3`
- `素材/武器/枪/枪01/枪的音效/枪声.mp3`
- `素材/武器/枪/枪02/枪的音效/枪声.mp3`
- `素材/武器/枪/枪01/枪的模型/model.glb`
- `素材/武器/枪/枪02/枪的模型/model.glb`
- `素材/敌人/敌人01/敌人模型/model.glb`
- `素材/敌人/敌人02/敌人模型/model.glb`
- `素材/敌人/敌人03/敌人模型/model.glb`
- `素材/敌人/敌人04/敌人模型/model.glb`

这些资源在代码里通常这样引用：

```ts
new URL('../../../素材/角色/脚步声01.mp3', import.meta.url).href
```

这意味着：

1. 开发时，Vite 知道这个文件是项目资源
2. 构建时，Vite 会把它复制到 `dist/assets`
3. 浏览器最后访问的是打包后的资源地址

所以：

- 源码阶段这些文件必须存在
- 生产构建后，`dist` 里会有一份打包拷贝

---

## 17. `package.json` 和 `tsconfig.json` 你需要知道什么

### 17.1 `package.json`

它是前端项目的基础配置文件。

你可以把它理解成：

- Python 项目里的 `pyproject.toml` + 命令入口的一部分结合体

这里定义了：

- 项目依赖
- 开发依赖
- 启动命令

当前最重要的是 `scripts`：

- `start`
- `dev`
- `build`
- `preview`

### 17.2 `tsconfig.json`

它是 TypeScript 编译配置。

你不需要一开始就读懂全部内容，但知道这几点就够了：

- TypeScript 负责检查
- Vite 负责真正打包
- 项目运行在浏览器环境，所以会用到 DOM 类型

---

## 18. 新手最常见的迷惑点

### 18.1 为什么有些文件只定义类型，看起来没“干活”？

因为 TypeScript 很多文件是在定义协议。

比如：

- `WeaponTypes.ts`
- `EnemyVisual.ts`

它们的作用不是运行时画面，而是：

- 让代码结构清楚
- 让编辑器能检查

### 18.2 为什么 HUD 不是 Three.js 物体？

因为 HUD 用 DOM 做更简单。

像这种内容：

- 准星
- 文本
- 面板
- 按钮

用普通 HTML/CSS 做起来更直接。

### 18.3 为什么敌人的命中不用可见模型？

因为直接拿可见模型做命中，往往：

- 不稳定
- 难调
- 受模型形状影响太大

所以项目里用了独立 `hitVolumes`。

### 18.4 为什么有 `config`，又有 `content`？

因为它们负责的事情不一样。

- `config`：放系统级共用参数，例如移动、镜头、跳跃、音频节奏、子弹印记数量
- `content`：放武器、敌人、关卡、默认开局内容

简单说：

- `config` 更像“全局手感设置”
- `content` 更像“内容目录和默认选择”

### 18.5 为什么敌人是异步加载？

因为敌人模型在外部资源文件里。

按需加载的好处是：

- 首屏包更轻
- 扩展更多敌人时更合理

---

## 19. 如果你明天要开始真正开发，我建议你这样做

### 第一步

先完整读：

- `docs/PROJECT_ONBOARDING.md`
- `README.md`
- `docs/TUNING_GUIDE.md`

### 第二步

只做参数级小改动，不做结构改动。

优先练这些：

- 改速度
- 改默认武器
- 改伤害
- 改一处出生点
- 改 HUD 文案
- 改子弹印记时间

### 第三步

开始理解这几个“可扩展入口”：

- `src/game/content/gameSelection.ts`
- `src/game/content/weapons/weaponCatalog.ts`
- `src/game/content/enemies/enemyCatalog.ts`
- `src/game/content/levels/levelCatalog.ts`
- `src/game/content/ui/gameHelpContent.ts`

### 第四步

再去动大逻辑：

- 新武器
- 新敌人
- 新关卡
- 新暂停菜单按钮

这样最稳。

---

## 20. 我建议你下一步具体先看哪几个文件

如果你现在马上要开始工作，我建议先打开下面这些文件，按顺序看：

1. `src/main.ts`
2. `src/game/GameDirector.ts`
3. `src/game/GameApp.ts`
4. `src/game/content/gameSelection.ts`
5. `src/game/config/systemTuning.ts`
6. `src/game/content/levels/levelCatalog.ts`
7. `src/game/content/weapons/weaponCatalog.ts`
8. `src/game/content/enemies/enemyCatalog.ts`
9. `src/game/content/ui/gameHelpContent.ts`
10. `src/game/enemies/EnemyRuntimeCatalog.ts`
11. `src/game/player/PlayerController.ts`
12. `src/game/enemies/EnemyManager.ts`
13. `src/game/combat/ShotResolver.ts`
14. `src/game/effects/BulletImpactSystem.ts`

这是当前最划算的阅读路线。

---

## 21. 给你的最后一句建议

你现在不需要先“学会整个前端”再来改这个项目。

更现实、更高效的方法是：

1. 先理解这份文档
2. 先看主线文件
3. 先做很小的改动
4. 每改一次就运行一次
5. 用“改参数 -> 看效果 -> 再理解代码”的方式学习

你已经会 Python，这已经足够你建立“程序结构”和“逻辑流”的理解了。
现在你缺的不是编程思维，而只是：

- 浏览器项目的运行方式
- TypeScript 的表面语法
- Three.js 的少量基础对象

把这三块补上，你就能开始稳定工作。
