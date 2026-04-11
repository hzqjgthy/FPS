import type * as THREE from 'three';

import { DESERT_FORTRESS_WORLD_DATA } from './worldData';
import { createDesertFortressLayout } from './layout';
import type { WorldDefinition } from '../../WorldTypes';

export function createDesertFortressWorld(scene: THREE.Scene): WorldDefinition {
  const { colliders, impactSurfaces } = createDesertFortressLayout(scene);

  return {
    colliders,
    impactSurfaces,
    ...DESERT_FORTRESS_WORLD_DATA,
  };
}
