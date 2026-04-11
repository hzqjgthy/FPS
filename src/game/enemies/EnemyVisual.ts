import * as THREE from 'three';

// 这是敌人“逻辑层”和“表现层”之间的公共协议。
// EnemyController 只管传状态，具体怎么动、怎么播动画，由各自的 visual 自己实现。
export interface EnemyVisualState {
  deltaSeconds: number;
  elapsedSeconds: number;
  walkTime: number;
  moveBlend: number;
  alerted: boolean;
  attacking: boolean;
  attackProgress: number;
  hitTriggered: boolean;
  healthRatio: number;
  isDead: boolean;
  deathProgress: number;
}

export interface EnemyVisual {
  root: THREE.Group;
  hitVolumes: THREE.Mesh[];
  update(frame: EnemyVisualState): void;
}
