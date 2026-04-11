import {
  listEnemyCatalogEntries,
  type EnemyCatalogEntry,
} from '../content/enemies/enemyCatalog';
import type { EnemyVisual } from './EnemyVisual';

// 运行时敌人原型 = 内容层数值配置 + 视觉工厂。
// EnemyController 只消费这份完整结构，不需要关心配置和模型是怎么拼起来的。
export interface EnemyArchetype extends EnemyCatalogEntry {
  createVisual: () => EnemyVisual;
}

type EnemyVisualFactory = () => EnemyVisual;
type EnemyVisualFactoryLoader = () => Promise<EnemyVisualFactory>;

// 视觉工厂注册表。
// 这里负责把“敌人 id”映射到真正的 glb / 动画加载实现，保持内容层纯净。
const ENEMY_VISUAL_LOADERS: Record<string, EnemyVisualFactoryLoader> = {
  enemy_001_raider: async () => {
    const { loadRaiderFactory } = await import('./models/RaiderModel');
    return loadRaiderFactory();
  },
  enemy_002_tree_brute: async () => {
    const { loadTreeBruteFactory } = await import('./models/TreeBruteModel');
    return loadTreeBruteFactory();
  },
  enemy_003_tree_guardian: async () => {
    const { loadTreeGuardianFactory } = await import('./models/TreeGuardianModel');
    return loadTreeGuardianFactory();
  },
  enemy_004_rotwood_overlord: async () => {
    const { loadRotwoodOverlordFactory } = await import('./models/RotwoodOverlordModel');
    return loadRotwoodOverlordFactory();
  },
};

export async function loadEnemyArchetypes(
  ids?: readonly string[],
): Promise<EnemyArchetype[]> {
  const entries = listEnemyCatalogEntries(ids);
  const archetypes = await Promise.all(
    entries.map(async (entry) => {
      const loadVisualFactory = ENEMY_VISUAL_LOADERS[entry.id];

      if (!loadVisualFactory) {
        console.warn(
          `No visual loader is registered for enemy "${entry.id}", skipping it.`,
        );
        return null;
      }

      try {
        const createVisual = await loadVisualFactory();
        return { ...entry, createVisual };
      } catch (error) {
        console.warn(
          `Failed to load ${entry.label} asset, falling back to other enemies only.`,
          error,
        );
        return null;
      }
    }),
  );

  return archetypes.filter(
    (archetype): archetype is EnemyArchetype => archetype !== null,
  );
}
