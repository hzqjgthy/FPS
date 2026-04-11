import type * as THREE from 'three';

import { DUST2_CLASSIC_WORLD_DATA } from './worldData';
import { createDust2ClassicLayout } from './layout';
import type { WorldDefinition } from '../../WorldTypes';

export function createDust2ClassicWorld(scene: THREE.Scene): WorldDefinition {
  const { colliders, impactSurfaces } = createDust2ClassicLayout(scene);

  return {
    colliders,
    impactSurfaces,
    ...DUST2_CLASSIC_WORLD_DATA,
  };
}
