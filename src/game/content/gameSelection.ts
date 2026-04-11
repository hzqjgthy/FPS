// 这是当前版本最直接的“默认内容入口”。
// GameDirector 会从这里读取默认开局配置，
// 运行时切关 / 重开则不直接改这里的常量。
export interface GameSelectionConfig {
  levelId: string;
  activeWeaponId: string;
  equippedWeaponIds: readonly string[];
  enabledEnemyIds: readonly string[];
}

// 默认第一关开局。
export const ACTIVE_LEVEL_ID = 'dust2_classic';
export const EQUIPPED_WEAPON_IDS = [
  'weapon_001_ak47_classic',
  'weapon_002_scar_h_battle_rifle',
  'weapon_003_red_dragon_tech_sniper',
] as const;

export const ACTIVE_WEAPON_ID = 'weapon_001_ak47_classic';
// export const ACTIVE_WEAPON_ID = 'weapon_002_scar_h_battle_rifle';
// export const ACTIVE_WEAPON_ID = 'weapon_003_red_dragon_tech_sniper';
export const ENABLED_ENEMY_IDS = [
  'enemy_001_raider',
  'enemy_002_tree_brute',
  'enemy_003_tree_guardian',
  'enemy_004_rotwood_overlord',
] as const;

export function createDefaultGameSelection(): GameSelectionConfig {
  return {
    levelId: ACTIVE_LEVEL_ID,
    activeWeaponId: ACTIVE_WEAPON_ID,
    equippedWeaponIds: [...EQUIPPED_WEAPON_IDS],
    enabledEnemyIds: [...ENABLED_ENEMY_IDS],
  };
}
