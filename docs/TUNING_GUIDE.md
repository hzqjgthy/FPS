# Tuning Guide

这份文档用于集中说明当前项目中“最适合调参数”的位置。
后续如果你要加更多武器、更多敌人、更多关卡，优先改这些文件，而不是先改核心逻辑。

## 快速入口

建议优先查看这几个文件：

- `src/game/content/gameSelection.ts`
- `src/game/content/ui/gameHelpContent.ts`
- `src/game/config/systemTuning.ts`
- `src/game/content/weapons/weaponCatalog.ts`
- `src/game/content/enemies/enemyCatalog.ts`
- `src/game/content/levels/levelCatalog.ts`
- `src/game/enemies/EnemyRuntimeCatalog.ts`

## 先理解：配置层和运行时层

为了避免改错地方，先记住下面这条边界：

- `systemTuning.ts`
  放全局共享手感参数，例如镜头、移动、跳跃、音频节奏、子弹印记上限。
- `gameSelection.ts`
  放默认开局内容，例如默认关卡、默认武器、启用哪些敌人。
- `weaponCatalog.ts`
  放每把武器自己的配置，例如伤害、射速、音效、子弹印记、视图模型工厂。
- `enemyCatalog.ts`
  只放敌人的纯数值配置，例如生命、攻击、移动、碰撞。
- `levelCatalog.ts`
  放关卡注册和暂停菜单展示文案。
- `content/ui/gameHelpContent.ts`
  放暂停菜单帮助页里的键位说明、操作名称和描述文本。
- `EnemyRuntimeCatalog.ts`
  放敌人的运行时装配，例如具体模型、动画、受击反馈、爆头命中体。

一句话总结：

- 想改“手感”，先看 `systemTuning.ts`
- 想改“默认开局内容”，先看 `gameSelection.ts`
- 想改“某把枪”，先看 `weaponCatalog.ts`
- 想改“某个敌人的数值”，先看 `enemyCatalog.ts`
- 想改“敌人的模型/动画/爆头判定”，看 `EnemyRuntimeCatalog.ts` 和 `src/game/enemies/models`
- 想改“某一关的文案和创建入口”，看 `levelCatalog.ts`
- 想改“暂停菜单帮助页里的键位说明”，看 `gameHelpContent.ts`

## 1. 当前启用内容

文件：`src/game/content/gameSelection.ts`

这个文件只负责“默认开局配置”。
项目启动时，`GameDirector` 会从这里读取默认值。
游戏运行中通过暂停菜单切关、重开关卡时，不是直接改这里的常量，而是用当前运行时配置重新创建 `GameApp`。

### `ACTIVE_LEVEL_ID`

- 作用：设置启动游戏时默认进入哪一张关卡。
- 改大或改小的影响：这里不是数值参数，本质是切换到另一张图。

### `ACTIVE_WEAPON_ID`

- 作用：设置启动游戏时玩家默认手里的武器。
- 修改后：开局 HUD、武器模型、枪声、伤害参数都会跟着切换。

### `EQUIPPED_WEAPON_IDS`

- 作用：设置当前这一局允许通过切枪系统轮换的武器列表。
- 增加武器：按数字键 `1` 时会在更多武器之间循环。
- 减少武器：切枪范围更小，更适合做单枪测试。

### `ENABLED_ENEMY_IDS`

- 作用：控制当前允许随机刷新的敌人种类。
- 增加敌人种类：随机池更丰富，场上敌人组合更多。
- 减少敌人种类：更容易做单敌人验证和调试。

## 2. 系统调参

文件：`src/game/config/systemTuning.ts`

这个文件存放“所有关卡和武器都会共享”的系统级参数。

### `camera.fov`

- 作用：第一人称视角的视野角度。
- 调大后：视野更广，速度感更强，但边缘透视会更夸张。
- 调小后：视野更窄，更像压缩镜头，画面更稳。

### `camera.near / camera.far`

- 作用：摄像机近裁剪面和远裁剪面。
- 调小 `near`：更近的物体也能显示，但太小可能增加深度精度问题。
- 调大 `far`：能看到更远的物体，但远景深度精度会更吃紧。

### `camera.eyeHeight`

- 作用：玩家视角离地高度，决定“眼睛”的高度。
- 调大后：视点更高，看起来像角色更高。
- 调小后：视点更低，更像角色蹲下一点，但当前并没有完整蹲伏系统。

### `camera.lookSensitivity`

- 作用：鼠标控制视角的灵敏度。
- 调大后：鼠标移动更灵敏，更容易快速转身。
- 调小后：瞄准更稳，但转身更慢。

### `camera.breathAmplitudeX / breathAmplitudeY`

- 作用：站立不动时镜头的轻微呼吸摆动。
- 调大后：呼吸感更明显，更有生命感。
- 调小后：画面更稳，更偏竞技。

### `camera.walkBobSpeed / camera.sprintBobSpeed`

- 作用：行走和冲刺时镜头起伏节奏。
- 调大后：步伐更急促。
- 调小后：移动更平滑。

### `camera.walkBobAmplitudeX / camera.walkBobAmplitudeY`

- 作用：行走时镜头左右和上下起伏幅度。
- 调大后：行走感更重，但也更容易晃。
- 调小后：更接近无头晃的竞技射击。

### `camera.sprintBobAmplitudeX / camera.sprintBobAmplitudeY`

- 作用：冲刺时镜头左右和上下起伏幅度。
- 调大后：冲刺速度感和压迫感更强。
- 调小后：冲刺更稳。

### `camera.strafeLeanAmount`

- 作用：横向移动时镜头侧倾幅度。
- 调大后：左右横移时更有“身体重心转移”的感觉。
- 调小后：视角更稳、更硬核。

### `camera.viewSmoothing`

- 作用：镜头呼吸、头晃和侧倾的缓动速度。
- 调大后：动作收敛更快，镜头更利落。
- 调小后：动作更柔和，但可能会有拖泥带水感。

### `player.moveSpeed`

- 作用：基础移动速度。
- 调大后：玩家整体移动更快。
- 调小后：玩家更慢，更容易观察关卡。

### `player.sprintMultiplier`

- 作用：冲刺相对基础移动速度的倍率。
- 调大后：Shift 冲刺更明显。
- 调小后：冲刺和行走差距更小。

### `player.radius / player.height`

- 作用：玩家碰撞体大小。
- 增大半径：更容易被墙体、门洞、箱子边缘挡住。
- 减小半径：更容易穿过狭窄区域，但也更容易显得碰撞松。
- 增大高度：更高，更容易在低矮位置顶住。
- 减小高度：更容易通过低矮空间。

### `player.maxHealth`

- 作用：玩家最大血量。
- 调大后：玩家更耐打。
- 调小后：游戏更危险、更紧张。

### `player.jumpDuration`

- 作用：一次完整跳跃从起跳到落地的总时长。
- 调大后：跳跃更飘、更慢。
- 调小后：跳跃更干脆、更像竞技 FPS。

### `player.jumpHeight`

- 作用：跳跃最高高度。
- 调大后：能跨过更高障碍。
- 调小后：跳跃更保守，更不容易跳上箱子。

### `player.supportEpsilon`

- 作用：脚底支撑面判定的容差。
- 调大后：更容易站稳在平台边缘，但也可能更容易“吸附”到边缘。
- 调小后：判定更严格，但边缘站立容错更低。

### `world.fogNear / world.fogFar`

- 作用：关卡雾效开始和结束距离。
- 调近后：远处更容易被雾覆盖，气氛更强。
- 调远后：远景更清楚。

### `effects.maxBulletMarks`

- 作用：场景中允许同时存在的最大子弹印记数量。
- 调大后：印记能保留更多，但会增加一些渲染开销。
- 调小后：更省资源，但旧印记会更快被新印记替换。

### `effects.bulletMarkSurfaceOffset`

- 作用：子弹印记离表面的微小抬起距离。
- 调大后：更不容易出现墙面闪烁，但印记可能看起来有点“浮”。
- 调小后：更贴墙，但太小可能出现 z-fighting。

### `audio.footstepVolume`

- 作用：脚步声音量。
- 调大后：脚步更明显。
- 调小后：更安静。

### `audio.walkStepInterval / audio.sprintStepInterval`

- 作用：行走和冲刺时脚步声触发间隔。
- 调大后：脚步更稀疏。
- 调小后：脚步更密集。

### `audio.footstepPoolSize`

- 作用：单个脚步声素材的并发播放器数量。
- 调大后：连续快速移动时，更不容易因为重复触发把前一个脚步声硬切断。
- 调小后：更省一点资源，但高频移动时更容易听起来发闷或被截断。

### `audio.jumpVolume / audio.jumpPoolSize`

- 作用：跳跃音量和同时播放容量。
- 调大音量：跳跃更明显。
- 提高池大小：连续快速触发跳跃时更不容易被上一次播放打断。

## 3. 武器配置

文件：`src/game/content/weapons/weaponCatalog.ts`

这个文件就是“武器内容注册表”。
当前每把枪最终导出的都是完整配置对象。
文件内部虽然用了默认值和辅助函数来减少重复录入，但运行时拿到的依然是完整武器定义。

当前项目已经有：

- `weapon_001_ak47_classic`
- `weapon_002_scar_h_battle_rifle`
- `weapon_003_red_dragon_tech_sniper`

### `id`

- 作用：武器唯一标识。
- 影响：切枪、默认开局选择、日志和查表都依赖它。

### `label`

- 作用：HUD 和文案显示名称。

### `ammoText`

- 作用：HUD 显示弹药文本。
- 当前只是展示文本，不参与真实弹药逻辑。

### `helpText`

- 作用：用于 HUD 操作提示。
- 修改后：HUD 下方帮助文案会变化。

### `presentation.viewModelScale`

- 作用：第一人称武器模型的整体缩放倍率。
- 调大后：枪会同比例变大，更贴近镜头。
- 调小后：枪会同比例变小，更不挡视野。
- 说明：AK 和 SCAR-H 是直接按这个倍率缩放；Dragon Sniper 会先做一次自动适配，再乘这个倍率。

### `audio.shotSource`

- 作用：武器射击音效文件路径。
- 替换后：可以快速切换不同武器的音色。

### `audio.shotVolume`

- 作用：武器射击音量。
- 调大后：枪声更突出。
- 调小后：枪声更柔和。

### `audio.shotPoolSize`

- 作用：连续射击时音频池大小。
- 调大后：更不容易因为短时间连发而切断声音。
- 调小后：节约一点资源，但连发更容易听起来断掉。

### `impact.markStyleId`

- 作用：武器使用哪种子弹印记风格。
- 换掉后：不同武器可以拥有明显不同的命中印记外观。

### `impact.markSize`

- 作用：子弹印记大小。
- 调大后：印记更显眼。
- 调小后：印记更克制。

### `impact.markOpacity`

- 作用：子弹印记初始透明度。
- 调大后：印记更深、更明显。
- 调小后：印记更淡。

### `impact.lifetimeSeconds / impact.fadeDurationSeconds`

- 作用：子弹印记总存在时间和淡出时长。
- 调大总时长：印记保留更久。
- 调大淡出时长：印记消失更慢、更柔和。

### `tuning.fireInterval`

- 作用：射速间隔，单位秒。
- 调大后：射速更慢。
- 调小后：射速更快。

### `tuning.bodyDamage`

- 作用：打身体时的伤害。
- 调大后：身体击杀更快。
- 调小后：更依赖爆头。

### `tuning.headshotDamage`

- 作用：打头时的伤害。
- 调大后：爆头收益更大。
- 调小后：头部和身体伤害差距更小。

### `tuning.hitRange`

- 作用：最大有效射击距离。
- 调大后：远距离敌人也能判定命中。
- 调小后：更强调近中距离作战。

### `tuning.bobSpeed / tuning.bobAmount`

- 作用：武器视图模型的行走晃动速度和幅度。
- 调大后：武器更有“手持”感。
- 调小后：武器更稳。

### `tuning.muzzleFlashDuration`

- 作用：枪口闪光持续时间。
- 调大后：闪光更明显、更长。
- 调小后：更利落。

### `tuning.recoilKickBack`

- 作用：武器模型后坐距离。
- 调大后：枪体后冲更明显。
- 调小后：视觉后坐更轻。

### `tuning.recoilRotationX / tuning.recoilRotationZ`

- 作用：武器抬枪和横向扭动幅度。
- 调大后：枪械后坐更强烈。
- 调小后：枪更稳。

### `tuning.recoilRecovery`

- 作用：武器和镜头后坐力恢复速度。
- 调大后：恢复更快，适合竞技。
- 调小后：后坐力残留更久，适合厚重枪感。

### `tuning.cameraKickVertical / tuning.cameraKickHorizontal`

- 作用：镜头后坐偏移。
- 调大后：开火时准星波动更明显。
- 调小后：瞄准更稳定。

### `createViewModel`

- 作用：真正创建这把枪的第一人称视图模型。
- 什么时候改：只有在你要接入一把新枪的模型或动画时才需要改这里。

## 4. 敌人数值配置

文件：`src/game/content/enemies/enemyCatalog.ts`

这个文件只负责“敌人的纯数值配置”。
这里不负责加载 glb，不负责动画名，不负责爆头命中体，也不负责受击动画。
如果你要改这些运行时表现，要去看第 5 节。

### `id`

- 作用：敌人唯一标识。

### `label`

- 作用：用于调试、文档和后续 UI 显示。

### `sizeScale`

- 作用：敌人的整体大小倍率。
- 调大后：敌人视觉模型、命中体、逻辑碰撞尺寸和攻击距离都会同比例变大。
- 调小后：敌人视觉模型、命中体、逻辑碰撞尺寸和攻击距离都会同比例变小。
- 说明：这不是单纯的视觉缩放，而是严格同比例，会同时影响 `radius / height / attackRange / supportEpsilon`。

### `alertRange`

- 作用：敌人开始追击玩家的警戒距离。
- 调大后：更容易被拉怪。
- 调小后：敌人更迟钝。

### `forgetRange`

- 作用：敌人放弃追击玩家的距离。
- 调大后：更不容易脱战。
- 调小后：更容易拉脱。

### `maxHealth`

- 作用：敌人生命值。
- 调大后：更耐打。
- 调小后：更容易击杀。

### `attackDamage`

- 作用：敌人攻击命中玩家的伤害。
- 调大后：更危险。
- 调小后：玩家容错更高。

### `moveSpeed`

- 作用：敌人追击速度。
- 调大后：压迫感更强。
- 调小后：更容易风筝。

### `turnSpeed`

- 作用：敌人转向玩家的速度。
- 调大后：转身更利索。
- 调小后：更笨重。

### `radius / height`

- 作用：敌人的基础碰撞尺寸。
- 调大后：更占空间，更容易挡路，也更容易被命中。
- 调小后：更灵活，但也可能更容易穿模。

### `attackRange`

- 作用：敌人开始挥砍的距离。
- 调大后：更早进入攻击。
- 调小后：必须贴得更近。

### `attackCooldown`

- 作用：两次攻击之间的冷却。
- 调大后：攻击更慢。
- 调小后：攻击频率更高。

### `attackDuration`

- 作用：攻击动画整体时长。
- 调大后：动作更沉重。
- 调小后：动作更快。

### `attackImpactTime`

- 作用：攻击动画中真正生效的命中帧时间点。
- 调大后：前摇更长。
- 调小后：更快造成伤害。

### `supportEpsilon`

- 作用：敌人脚底支撑容差。
- 调大后：更容易站稳在平台边缘。
- 调小后：判定更严格。

### `corpseDuration`

- 作用：死亡后保留在场景里的时间。
- 调大后：尸体停留更久。
- 调小后：场景清理更快。

## 5. 敌人运行时装配

文件：

- `src/game/enemies/EnemyRuntimeCatalog.ts`
- `src/game/enemies/models/RaiderModel.ts`
- `src/game/enemies/models/TreeBruteModel.ts`
- `src/game/enemies/models/TreeGuardianModel.ts`
- `src/game/enemies/models/RotwoodOverlordModel.ts`

这里负责“把敌人 id 接到真正模型”的那一层。

如果你要改下面这些内容，优先看这里：

- 敌人具体加载哪个 `model.glb`
- 动画名字怎么对应到 idle / walk / attack / death / hit
- 敌人的受击反馈是否接上
- 敌人的爆头命中体怎么定义
- 敌人的视觉工厂怎么返回给运行时

一句话：

- 改敌人伤害、血量、速度：`enemyCatalog.ts`
- 改敌人模型、动画、爆头判定：`EnemyRuntimeCatalog.ts` 和 `src/game/enemies/models`

## 6. 关卡配置

文件：`src/game/content/levels/levelCatalog.ts`

这个文件负责“项目里有哪些关卡”和“这些关卡在暂停菜单里如何展示”。
默认进入哪一关，是 `gameSelection.ts` 决定的。
运行中怎么重开和切关，是 `GameDirector.ts` 和 `PauseMenu.ts` 决定的。

### `id`

- 作用：关卡唯一标识。

### `label`

- 作用：关卡名称。
- 修改后：暂停菜单的关卡名会变化。

### `topTag / modeTag`

- 作用：HUD 顶部标签文案。
- 修改后：游戏内顶部标签会变化。

### `introKicker / introTitle / introDescription / introLegend / introTip`

- 作用：暂停菜单和开局面板文案。
- 修改后：可以快速适配不同关卡、模式或玩法说明。

### `createWorld`

- 作用：真正创建关卡场景。
- 换成别的场景构建器后，就能切换到别的关卡。

## 7. 关卡场景与出生点

文件：

- `src/game/world/levels/dust2_classic/layout.ts`
- `src/game/world/levels/dust2_classic/worldData.ts`
- `src/game/world/levels/desert_fortress/layout.ts`
- `src/game/world/levels/desert_fortress/worldData.ts`

这里适合调：

### `spawnPoint`

- 作用：玩家出生点。
- 修改后：改变玩家进入关卡时的位置。

### `spawnYaw`

- 作用：玩家出生朝向。
- 修改后：改变进入关卡后面朝方向。

### `enemySpawns`

- 作用：敌人出生点列表。
- 增加后：会刷更多敌人。
- 减少后：敌人更少。

### 地图几何 / 掩体 / 路线

- 作用：关卡布局、掩体分布、路线复杂度。
- 修改后：会直接改变推进方式、交战距离和敌人追击路线。

### 世界表面命中区域

- 作用：决定哪些墙面、地面能接收子弹印记。
- 修改后：会影响命中世界表面时，是否出现子弹印记。
- 这部分通常在关卡构建器和共享世界工具里维护。

## 8. 暂停菜单、帮助页与关卡切换流程

文件：

- `src/game/GameDirector.ts`
- `src/game/ui/PauseMenu.ts`
- `src/game/content/ui/gameHelpContent.ts`

这两份文件不是纯配置表，但它们很重要，因为项目现在的关卡流程都在这里：

- 启动后默认停在暂停界面
- 点击“进入战场”开始游戏
- 按 `Esc` 重新打开暂停界面
- 支持“继续游戏”
- 支持“重启本关卡”
- 支持“选择关卡”
- 支持“游戏帮助”

当前暂停菜单内部不是靠多个布尔值硬拼出来的，而是用一个统一视图状态切换：

- `main`
- `level-select`
- `help`

这样做的好处是：

- 主菜单、选关页、帮助页不会互相打架
- 后面如果要加 `settings` 之类的新页面，结构更容易扩展
- `GameDirector.ts` 负责切换当前菜单视图
- `PauseMenu.ts` 负责根据视图渲染对应 DOM
- `gameHelpContent.ts` 负责提供帮助页的内容数据

什么时候改这里：

- 你想给暂停菜单加按钮
- 你想改开局是否默认暂停
- 你想改选关逻辑
- 你想改重开逻辑
- 你想改帮助页的结构或返回逻辑

### `src/game/content/ui/gameHelpContent.ts`

- 作用：集中维护帮助页里的键位和描述内容。
- 适合改什么：移动键、切枪键、暂停键、跳跃键、未来新增的换弹键、开镜键、下蹲键等。
- 为什么单独放一份：帮助文案属于“内容”，不应该硬编码在 `PauseMenu.ts` 里。

### `src/game/ui/PauseMenu.ts`

- 作用：负责暂停菜单 DOM、本关重启按钮、选关列表、帮助页渲染。
- 适合改什么：按钮排列、帮助页布局、返回按钮文案、面板内部层级。

### `src/game/GameDirector.ts`

- 作用：负责当前菜单处于 `main`、`level-select` 还是 `help`。
- 适合改什么：点击按钮以后切换到哪个视图、开局默认展示哪个视图、按 `Esc` 后打开哪个视图。

## 9. 子弹印记与命中流程

相关文件：

- `src/game/config/systemTuning.ts`
- `src/game/content/weapons/weaponCatalog.ts`
- `src/game/combat/ShotResolver.ts`
- `src/game/effects/BulletImpactSystem.ts`

如果你要调“子弹打到墙上之后的表现”，通常分两层：

- 全局层：`systemTuning.ts`
  例如 `effects.maxBulletMarks`、`effects.bulletMarkSurfaceOffset`
- 武器层：`weaponCatalog.ts`
  例如 `impact.markStyleId`、`impact.markSize`、`impact.markOpacity`、`impact.lifetimeSeconds`

职责分工：

- `ShotResolver.ts`
  负责判断这一枪到底打到了敌人还是世界表面。
- `BulletImpactSystem.ts`
  负责在世界表面生成印记、保留印记、淡出印记。

所以：

- 想让所有枪的印记总量更多：改 `systemTuning.ts`
- 想让某一把枪的印记更大、更久、更深：改 `weaponCatalog.ts`
- 想排查为什么某一枪打墙没印记：看 `ShotResolver.ts` 和关卡世界表面注册

## 10. 如何继续扩展

### 新增武器

1. 在 `src/game/content/weapons/weaponCatalog.ts` 增加一条武器配置。
2. 如果需要新视图模型，在 `src/game/weapons/models` 新建一个 `ViewModel` 类。
3. 如果只是测试默认开局，用 `src/game/content/gameSelection.ts` 切换 `ACTIVE_WEAPON_ID`。
4. 如果要让数字键 `1` 能切到它，把它加入 `EQUIPPED_WEAPON_IDS`。

### 新增敌人

1. 在 `src/game/content/enemies/enemyCatalog.ts` 增加一条敌人数值配置。
2. 在 `src/game/enemies/models` 新建对应的模型加载文件。
3. 在 `src/game/enemies/EnemyRuntimeCatalog.ts` 注册这个敌人的视觉工厂。
4. 如果只是测试默认开局，把它加入 `src/game/content/gameSelection.ts` 的 `ENABLED_ENEMY_IDS`。

### 新增关卡

1. 在 `src/game/world/levels` 下新建一个关卡文件夹。
2. 拆成 `index.ts`、`layout.ts`、`worldData.ts` 这类结构。
3. 在 `src/game/content/levels/levelCatalog.ts` 注册。
4. 如果只是测试默认开局，修改 `src/game/content/gameSelection.ts` 的 `ACTIVE_LEVEL_ID`。
5. 如果要让暂停菜单能切过去，确保它已经被注册进 `levelCatalog.ts`。
