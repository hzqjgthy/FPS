import * as THREE from 'three';

import { loadEnemyArchetypes } from './EnemyRuntimeCatalog';
import { EnemyController } from './EnemyController';
import type { WeaponDefinition } from '../weapons/WeaponTypes';

export interface EnemyManagerFrameState {
  damageToPlayer: number;
  aliveEnemyCount: number;
}

export interface EnemyShotSummary {
  hit: boolean;
  killed: boolean;
}

export interface EnemyShotHitCandidate {
  enemy: EnemyController;
  distance: number;
  zone: 'body' | 'head';
}

/**
 * 敌人系统的运行时入口。
 * 它负责两件核心事情：
 * 1. 创建并逐帧更新所有敌人
 * 2. 统一处理玩家对敌人的射击命中
 */
export class EnemyManager {
  private enemies: EnemyController[] = [];
  private readonly scene: THREE.Scene;
  private readonly colliders: THREE.Box3[];
  private readonly spawnPoints: readonly THREE.Vector3[];
  private readonly enabledEnemyIds: readonly string[];
  private initializationPromise: Promise<void> | null = null;

  constructor(
    scene: THREE.Scene,
    colliders: THREE.Box3[],
    spawnPoints: THREE.Vector3[],
    enabledEnemyIds: readonly string[],
  ) {
    this.scene = scene;
    this.colliders = colliders;
    this.spawnPoints = spawnPoints;
    this.enabledEnemyIds = enabledEnemyIds;
  }

  public async initialize(): Promise<void> {
    if (this.initializationPromise) {
      return this.initializationPromise;
    }

    this.initializationPromise = this.loadEnemies().catch((error) => {
      this.initializationPromise = null;
      throw error;
    });

    return this.initializationPromise;
  }

  public update(
    deltaSeconds: number,
    elapsedSeconds: number,
    playerFeetPosition: THREE.Vector3,
  ): EnemyManagerFrameState {
    let damageToPlayer = 0;
    let aliveEnemyCount = 0;

    for (const enemy of this.enemies) {
      const frame = enemy.update(deltaSeconds, elapsedSeconds, playerFeetPosition);
      damageToPlayer += frame.damageToPlayer;

      if (enemy.isAlive()) {
        aliveEnemyCount += 1;
      }
    }

    return { damageToPlayer, aliveEnemyCount };
  }

  public findNearestShotHit(
    ray: THREE.Ray,
    maxDistance: number,
  ): EnemyShotHitCandidate | null {
    let closestEnemy: EnemyController | null = null;
    let closestEnemyDistance = maxDistance;
    let closestHitZone: 'body' | 'head' = 'body';

    for (const enemy of this.enemies) {
      const hit = enemy.intersectShot(ray, closestEnemyDistance);

      if (hit === null || hit.distance >= closestEnemyDistance) {
        continue;
      }

      closestEnemy = enemy;
      closestEnemyDistance = hit.distance;
      closestHitZone = hit.zone;
    }

    if (!closestEnemy) {
      return null;
    }

    return {
      enemy: closestEnemy,
      distance: closestEnemyDistance,
      zone: closestHitZone,
    };
  }

  public applyShotHit(
    hit: EnemyShotHitCandidate,
    weapon: WeaponDefinition,
  ): EnemyShotSummary {
    const damage =
      hit.zone === 'head'
        ? weapon.tuning.headshotDamage
        : weapon.tuning.bodyDamage;
    const shotResult = hit.enemy.applyDamage(damage);
    shotResult.zone = hit.zone;
    return shotResult;
  }

  public getAliveEnemyCount(): number {
    return this.enemies.reduce(
      (count, enemy) => count + Number(enemy.isAlive()),
      0,
    );
  }

  private async loadEnemies(): Promise<void> {
    // 敌人原型是异步加载的，所以这里做一次初始化装配。
    const archetypes = await loadEnemyArchetypes(this.enabledEnemyIds);

    this.enemies = this.spawnPoints.map((spawnPoint) => {
      const archetype =
        archetypes[Math.floor(Math.random() * archetypes.length)] ?? archetypes[0];

      if (!archetype) {
        throw new Error('No enemy archetypes are available.');
      }

      return new EnemyController(this.scene, this.colliders, spawnPoint, archetype);
    });
  }
}
