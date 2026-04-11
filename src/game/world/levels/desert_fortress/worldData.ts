import * as THREE from 'three';

import type { WorldRuntimeData } from '../../WorldTypes';

export const DESERT_FORTRESS_WORLD_DATA = {
  enemySpawns: [
    new THREE.Vector3(0, 0, 72),
    new THREE.Vector3(-96, 0, 70),
    new THREE.Vector3(96, 0, 70),
    new THREE.Vector3(-74, 0, -8),
    new THREE.Vector3(74, 0, -8),
    new THREE.Vector3(-52, 0, -18),
    new THREE.Vector3(52, 0, -18),
    new THREE.Vector3(0, 0, -20),
    new THREE.Vector3(-92, 0, -86),
    new THREE.Vector3(92, 0, -86),
  ],
  spawnPoint: new THREE.Vector3(0, 0, 102),
  spawnYaw: 0,
} satisfies WorldRuntimeData;
