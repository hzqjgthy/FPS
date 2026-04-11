import type * as THREE from 'three';

import { createDesertFortressWorld } from '../../world/levels/desert_fortress';
import { createDust2ClassicWorld } from '../../world/levels/dust2_classic';
import type { WorldDefinition } from '../../world/WorldTypes';

// 关卡定义不仅负责 UI 文案，也负责提供真正创建三维场景的工厂函数。
export interface LevelDefinition {
  id: string;
  label: string;
  topTag: string;
  modeTag: string;
  introKicker: string;
  introTitle: string;
  introDescription: string;
  introLegend: string;
  introTip: string;
  createWorld(scene: THREE.Scene): WorldDefinition;
}

// 关卡注册表。
// 后续新增地图时，只需要新增一个 definition，然后切换 ACTIVE_LEVEL_ID。
export const LEVEL_CATALOG: Record<string, LevelDefinition> = {
  dust2_classic: {
    id: 'dust2_classic',
    label: 'Dust II Style Blockout',
    topTag: 'Dust II Style Blockout',
    modeTag: 'Enemy AI Online',
    introKicker: 'Classic Desert Arena',
    introTitle: 'Dust II Warmup',
    introDescription:
      '当前版本已经支持敌人刷新、警戒追击、走路动画、挥砍攻击，以及玩家的移动和射击原型。',
    introLegend: 'W 前进 · A 左移 · S 后退 · D 右移 · Space 跳跃',
    introTip: '点击进入战场后，鼠标会锁定到画面里。向前推进后，敌人进入警戒状态会朝你移动。',
    createWorld: createDust2ClassicWorld,
  },
  desert_fortress: {
    id: 'desert_fortress',
    label: 'Desert Fortress Siege',
    topTag: 'Desert Fortress Siege',
    modeTag: 'Multi-Route Combat',
    introKicker: 'Fortress Assault',
    introTitle: 'Citadel Breach',
    introDescription:
      '第二关比第一关更复杂，加入了中庭主战区、双侧绕路、北侧堡垒与更多掩体组合，适合测试推进、绕侧与中远距离交火。',
    introLegend: 'W 前进 · A 左移 · S 后退 · D 右移 · Space 跳跃',
    introTip: '从正门推进，也可以沿左右外侧路线包抄。中央中庭适合中距离交战，北侧堡垒更适合持续压进。',
    createWorld: createDesertFortressWorld,
  },
};

export function getLevelDefinition(id: string): LevelDefinition {
  const level = LEVEL_CATALOG[id];

  if (!level) {
    throw new Error(`Level definition "${id}" was not found.`);
  }

  return level;
}

export function listLevelDefinitions(): LevelDefinition[] {
  return Object.values(LEVEL_CATALOG);
}
