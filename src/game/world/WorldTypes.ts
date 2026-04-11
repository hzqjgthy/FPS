import type * as THREE from 'three';

export type ImpactSurfaceType =
  | 'plaster'
  | 'trim'
  | 'ground'
  | 'stone'
  | 'crate'
  | 'accent';

export interface ImpactSurface {
  mesh: THREE.Mesh;
  surfaceType: ImpactSurfaceType;
}

// 关卡工厂最终交给运行时的数据。
export interface WorldRuntimeData {
  enemySpawns: THREE.Vector3[];
  spawnPoint: THREE.Vector3;
  spawnYaw: number;
}

export interface WorldDefinition extends WorldRuntimeData {
  colliders: THREE.Box3[];
  impactSurfaces: ImpactSurface[];
}
