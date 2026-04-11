import { SYSTEM_TUNING } from '../../config/systemTuning';

// 纯内容层敌人定义。
// 这里不关心模型如何加载，只描述“这个敌人是什么、数值是多少”。
export interface EnemyCatalogEntry {
  id: string; // 敌人唯一 ID，供注册表、选择器和运行时查找使用。
  label: string; // 敌人显示名称，主要用于调试、文档和后续 UI。
  sizeScale: number; // 敌人整体大小倍率，会同比例影响模型、碰撞体和攻击距离。
  alertRange: number; // 敌人开始追击玩家的警戒距离。
  forgetRange: number; // 敌人丢失目标、停止追击的距离。
  maxHealth: number; // 敌人最大生命值。
  attackDamage: number; // 敌人攻击命中玩家时造成的伤害。
  moveSpeed: number; // 敌人追击玩家时的移动速度。
  turnSpeed: number; // 敌人朝向玩家转身的速度。
  radius: number; // 敌人碰撞体半径，影响占地面积和贴墙表现。
  height: number; // 敌人碰撞体高度，影响整体站立体积。
  attackRange: number; // 敌人开始进入攻击判定的距离。
  attackCooldown: number; // 两次攻击之间的最短冷却时间，单位秒。
  attackDuration: number; // 单次攻击动画的总时长，单位秒。
  attackImpactTime: number; // 攻击动画中真正生效的命中时刻，单位秒。
  supportEpsilon: number; // 脚底支撑面的容差，影响站立和落地稳定性。
  corpseDuration: number; // 敌人死亡后尸体在场景中保留的时间，单位秒。
}

type EnemyCatalogDefaults = Omit<
  EnemyCatalogEntry,
  'id' | 'label' | 'maxHealth' | 'attackDamage'
>;

type EnemyCatalogInput = Pick<
  EnemyCatalogEntry,
  'id' | 'label' | 'maxHealth' | 'attackDamage'
> & Partial<EnemyCatalogDefaults>;

// 内部公共默认值。
// 这里的作用只是“减少重复输入”，不是让运行时保存一份不完整配置。
const ENEMY_DEFAULTS: EnemyCatalogDefaults = {
  sizeScale: 1, // 默认整体大小倍率。
  alertRange: 30, // 默认警戒距离。
  forgetRange: 42, // 默认脱战距离。
  moveSpeed: 4.8, // 默认追击速度。
  turnSpeed: 9, // 默认转身速度。
  radius: 0.62, // 默认碰撞半径。
  height: 2.2, // 默认碰撞高度。
  attackRange: 2.8, // 默认攻击判定距离。
  attackCooldown: 1.2, // 默认攻击冷却，单位秒。
  attackDuration: 0.72, // 默认攻击动作时长，单位秒。
  attackImpactTime: 0.38, // 默认攻击生效时刻，单位秒。
  supportEpsilon: SYSTEM_TUNING.player.supportEpsilon, // 默认脚底支撑容差。
  corpseDuration: 2.4, // 默认尸体保留时间，单位秒。
};

// 最终导出的每一只敌人都必须是“完整参数块”。
// 这个函数会把默认值展开后再做基础校验，避免运行时拿到 Partial 配置。
function defineEnemyConfig(input: EnemyCatalogInput): EnemyCatalogEntry {
  const baseConfig: EnemyCatalogEntry = {
    ...ENEMY_DEFAULTS,
    ...input,
  };

  const config: EnemyCatalogEntry = {
    ...baseConfig,
    radius: baseConfig.radius * baseConfig.sizeScale,
    height: baseConfig.height * baseConfig.sizeScale,
    attackRange: baseConfig.attackRange * baseConfig.sizeScale,
    supportEpsilon: baseConfig.supportEpsilon * baseConfig.sizeScale,
  };

  if (config.forgetRange < config.alertRange) {
    throw new Error(
      `Enemy "${config.id}" has forgetRange smaller than alertRange.`,
    );
  }

  if (config.attackImpactTime > config.attackDuration) {
    throw new Error(
      `Enemy "${config.id}" has attackImpactTime larger than attackDuration.`,
    );
  }

  if (config.maxHealth <= 0 || config.attackDamage < 0) {
    throw new Error(`Enemy "${config.id}" has invalid combat stats.`);
  }

  if (config.sizeScale <= 0) {
    throw new Error(`Enemy "${config.id}" has invalid sizeScale.`);
  }

  return config;
}

// 敌人内容注册表。
// 写法上可以只覆盖差异字段，但导出结果始终是完整配置对象。
// 以后新增敌人时，先在这里补纯配置，再去运行时层接模型和动画。
export const ENEMY_CATALOG: Record<string, EnemyCatalogEntry> = {
  enemy_001_raider: defineEnemyConfig({
    id: 'enemy_001_raider', // 敌人唯一 ID。
    label: 'Raider', // 敌人显示名称。
    sizeScale: 0.8, // 敌人整体大小倍率。
    maxHealth: 200, // 最大生命值。
    attackDamage: 16, // 攻击命中玩家时造成的伤害。
    alertRange: 28, // 进入追击状态的距离。
    forgetRange: 40, // 放弃追击的距离。
    moveSpeed: 4.9, // 追击速度。
    turnSpeed: 10.5, // 转向速度。
    radius: 0.62, // 碰撞半径。
    height: 2.2, // 碰撞高度。
    attackRange: 2.75, // 开始挥砍的距离。
    attackCooldown: 1.08, // 两次挥砍之间的冷却时间。
    attackDuration: 0.68, // 单次挥砍动画总时长。
    attackImpactTime: 0.34, // 挥砍真正造成伤害的时间点。
    supportEpsilon: SYSTEM_TUNING.player.supportEpsilon, // 脚底支撑容差。
    corpseDuration: 2.4, // 死亡后尸体保留时间。
  }),
  enemy_002_tree_brute: defineEnemyConfig({
    id: 'enemy_002_tree_brute', // 敌人唯一 ID。
    label: 'Tree Brute', // 敌人显示名称。
    sizeScale: 1, // 敌人整体大小倍率。
    maxHealth: 500, // 最大生命值。
    attackDamage: 50, // 攻击命中玩家时造成的伤害。
    alertRange: 32, // 进入追击状态的距离。
    forgetRange: 45, // 放弃追击的距离。
    moveSpeed: 4.1, // 追击速度。
    turnSpeed: 7.4, // 转向速度。
    radius: 0.82, // 碰撞半径。
    height: 2.55, // 碰撞高度。
    attackRange: 3.35, // 开始挥砍的距离。
    attackCooldown: 1.28, // 两次挥砍之间的冷却时间。
    attackDuration: 0.78, // 单次挥砍动画总时长。
    attackImpactTime: 0.42, // 挥砍真正造成伤害的时间点。
    supportEpsilon: SYSTEM_TUNING.player.supportEpsilon, // 脚底支撑容差。
    corpseDuration: 3.4, // 死亡后尸体保留时间。
  }),
  enemy_003_tree_guardian: defineEnemyConfig({
    id: 'enemy_003_tree_guardian', // 敌人唯一 ID。
    label: 'Tree Guardian', // 敌人显示名称。
    sizeScale: 2, // 敌人整体大小倍率。
    maxHealth: 350, // 最大生命值。
    attackDamage: 32, // 攻击命中玩家时造成的伤害。
    alertRange: 34, // 进入追击状态的距离。
    forgetRange: 48, // 放弃追击的距离。
    moveSpeed: 4.35, // 追击速度。
    turnSpeed: 8.6, // 转向速度。
    radius: 0.76, // 碰撞半径。
    height: 2.72, // 碰撞高度。
    attackRange: 3.15, // 开始挥砍的距离。
    attackCooldown: 1.14, // 两次挥砍之间的冷却时间。
    attackDuration: 0.74, // 单次挥砍动画总时长。
    attackImpactTime: 0.36, // 挥砍真正造成伤害的时间点。
    supportEpsilon: SYSTEM_TUNING.player.supportEpsilon, // 脚底支撑容差。
    corpseDuration: 3.2, // 死亡后尸体保留时间。
  }),
  enemy_004_rotwood_overlord: defineEnemyConfig({
    id: 'enemy_004_rotwood_overlord', // 敌人唯一 ID。
    label: 'Rotwood Overlord', // 敌人显示名称。
    sizeScale: 4, // 敌人整体大小倍率。
    maxHealth: 7000, // 最大生命值。
    attackDamage: 1, // 攻击命中玩家时造成的伤害。
    alertRange: 36, // 进入追击状态的距离。
    forgetRange: 52, // 放弃追击的距离。
    moveSpeed: 3.9, // 追击速度。
    turnSpeed: 6.6, // 转向速度。
    radius: 0.96, // 碰撞半径。
    height: 3.18, // 碰撞高度。
    attackRange: 3.55, // 开始挥砍的距离。
    attackCooldown: 1.35, // 两次挥砍之间的冷却时间。
    attackDuration: 0.86, // 单次挥砍动画总时长。
    attackImpactTime: 0.46, // 挥砍真正造成伤害的时间点。
    supportEpsilon: SYSTEM_TUNING.player.supportEpsilon, // 脚底支撑容差。
    corpseDuration: 4, // 死亡后尸体保留时间。
  }),
};

export function getEnemyCatalogEntry(id: string): EnemyCatalogEntry {
  const enemy = ENEMY_CATALOG[id];

  if (!enemy) {
    throw new Error(`Enemy catalog entry "${id}" was not found.`);
  }

  return enemy;
}

export function listEnemyCatalogEntries(
  ids?: readonly string[],
): EnemyCatalogEntry[] {
  if (!ids || ids.length === 0) {
    return Object.values(ENEMY_CATALOG);
  }

  const allowedIds = new Set(ids);
  return Object.values(ENEMY_CATALOG).filter((enemy) => allowedIds.has(enemy.id));
}
