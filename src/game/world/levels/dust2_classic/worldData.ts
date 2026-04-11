import * as THREE from 'three';

import type { WorldRuntimeData } from '../../WorldTypes';

export const DUST2_CLASSIC_WORLD_DATA = {
  enemySpawns: [
    new THREE.Vector3(0, 0, 54),
    new THREE.Vector3(-73, 0, 24),
    new THREE.Vector3(73, 0, 24),
    new THREE.Vector3(-73, 0, -34),
    new THREE.Vector3(73, 0, -34),
  ],
  spawnPoint: new THREE.Vector3(0, 0, 78),
  spawnYaw: 0,
} satisfies WorldRuntimeData;
