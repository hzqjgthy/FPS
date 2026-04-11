/**
 * 系统级参数中心。
 * 这里放“所有关卡和武器都会共用”的手感参数，例如镜头、移动、跳跃、音频节奏。
 *
 * 内容型配置则放在各自的 catalog 里：
 * - 关卡：content/levels
 * - 武器：content/weapons
 * - 敌人：content/enemies
 */
export const SYSTEM_TUNING = {
  // 第一人称镜头、呼吸、走路摆动等参数。
  camera: {
    fov: 76, // 第一人称摄像机视野角度，值越大画面越广。
    near: 0.1, // 摄像机近裁剪面，小于这个距离的物体不会被渲染。
    far: 320, // 摄像机远裁剪面，大于这个距离的物体不会被渲染。
    eyeHeight: 1.68, // 玩家视角离地高度，决定“眼睛”所在的位置。
    lookSensitivity: 0.0022, // 鼠标视角灵敏度，值越大转头越快。
    breathAmplitudeX: 0.004, // 呼吸晃动在 X 方向的幅度，影响左右轻微摆动。
    breathAmplitudeY: 0.01, // 呼吸晃动在 Y 方向的幅度，影响上下轻微浮动。
    walkBobSpeed: 9.5, // 行走镜头摆动速度，值越大摆动节奏越快。
    sprintBobSpeed: 13.2, // 冲刺镜头摆动速度，值越大摆动节奏越快。
    walkBobAmplitudeX: 0.014, // 行走时镜头左右摆动幅度。
    walkBobAmplitudeY: 0.022, // 行走时镜头上下摆动幅度。
    sprintBobAmplitudeX: 0.02, // 冲刺时镜头左右摆动幅度。
    sprintBobAmplitudeY: 0.032, // 冲刺时镜头上下摆动幅度。
    strafeLeanAmount: 0.012, // 左右横移时镜头侧倾幅度。
    viewSmoothing: 11, // 镜头跟随和回正的平滑强度，值越大越跟手。
  },
  // 玩家物理体积、基础速度、跳跃曲线时长等参数。
  player: {
    moveSpeed: 15, // 玩家基础移动速度。
    sprintMultiplier: 3, // 冲刺速度倍率，会乘到基础移动速度上。
    radius: 0.7, // 玩家碰撞体半径，影响是否容易擦到墙角和障碍物。
    height: 1.82, // 玩家碰撞体高度，影响角色整体站立体积。
    maxHealth: 100, // 玩家最大生命值。
    jumpDuration: 1, // 一次完整跳跃的总时长，单位秒。
    jumpHeight: 107.8, // 跳跃曲线高度，值越大跳得越高。
    supportEpsilon: 0.04, // 地面吸附/落地容差，用来帮助角色更稳定地判定站在地面上。
  },
  // 场景级统一表现，目前主要是雾效范围。
  world: {
    fogNear: 90, // 雾效开始生效的距离。
    fogFar: 240, // 雾效完全覆盖的距离。
  },
  effects: {
    maxBulletMarks: 64, // 场景中同时保留的最大子弹印记数量，超过后会回收最旧的印记。
    bulletMarkSurfaceOffset: 0.018, // 子弹印记离表面的微小抬起距离，用来避免贴片和墙面互相闪烁。
  },
  // 通用音频节奏参数，脚步和跳跃都会读取这里。
  audio: {
    footstepVolume: 0.34, // 脚步声音量。
    walkStepInterval: 0.28, // 行走时两次脚步声之间的间隔，单位秒。
    sprintStepInterval: 0.14, // 冲刺时两次脚步声之间的间隔，单位秒。
    footstepPoolSize: 3, // 脚步声播放器池大小，值越大越不容易被连续触发打断。
    jumpVolume: 0.4, // 跳跃声音量。
    jumpPoolSize: 2, // 跳跃声播放器池大小，连续触发时更不容易互相截断。
  },
} as const;
