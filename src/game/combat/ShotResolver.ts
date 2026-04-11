import * as THREE from 'three';

import type { EnemyShotHitCandidate, EnemyManager } from '../enemies/EnemyManager';
import type { WeaponDefinition } from '../weapons/WeaponTypes';
import type { ImpactSurface, ImpactSurfaceType } from '../world/WorldTypes';

export interface WorldShotHitCandidate {
  distance: number;
  point: THREE.Vector3;
  normal: THREE.Vector3;
  surfaceType: ImpactSurfaceType;
}

export type ShotResolution =
  | { kind: 'none' }
  | { kind: 'enemy'; hit: EnemyShotHitCandidate }
  | { kind: 'world'; hit: WorldShotHitCandidate };

export class ShotResolver {
  private readonly shotOrigin = new THREE.Vector3();
  private readonly shotDirection = new THREE.Vector3();
  private readonly shotRay = new THREE.Ray();
  private readonly worldRaycaster = new THREE.Raycaster();
  private readonly worldObjects: THREE.Object3D[];
  private readonly enemies: EnemyManager;

  constructor(
    enemies: EnemyManager,
    impactSurfaces: readonly ImpactSurface[],
  ) {
    this.enemies = enemies;
    this.worldObjects = impactSurfaces.map((surface) => surface.mesh);
  }

  public resolve(
    camera: THREE.PerspectiveCamera,
    weapon: WeaponDefinition,
  ): ShotResolution {
    camera.getWorldPosition(this.shotOrigin);
    camera.getWorldDirection(this.shotDirection);
    this.shotRay.set(this.shotOrigin, this.shotDirection.normalize());

    const maxDistance = weapon.tuning.hitRange;
    const enemyHit = this.enemies.findNearestShotHit(this.shotRay, maxDistance);
    const worldHit = this.findNearestWorldHit(maxDistance);

    if (enemyHit && (!worldHit || enemyHit.distance <= worldHit.distance)) {
      return { kind: 'enemy', hit: enemyHit };
    }

    if (worldHit) {
      return { kind: 'world', hit: worldHit };
    }

    return { kind: 'none' };
  }

  private findNearestWorldHit(maxDistance: number): WorldShotHitCandidate | null {
    this.worldRaycaster.ray.copy(this.shotRay);
    this.worldRaycaster.near = 0;
    this.worldRaycaster.far = maxDistance;

    const hits = this.worldRaycaster.intersectObjects(this.worldObjects, false);
    const nearestHit = hits[0];

    if (!nearestHit?.face) {
      return null;
    }

    const worldNormal = nearestHit.face.normal
      .clone()
      .transformDirection(nearestHit.object.matrixWorld)
      .normalize();
    const surfaceType = nearestHit.object.userData.impactSurfaceType as ImpactSurfaceType | undefined;

    if (!surfaceType) {
      return null;
    }

    return {
      distance: nearestHit.distance,
      point: nearestHit.point.clone(),
      normal: worldNormal,
      surfaceType,
    };
  }
}
