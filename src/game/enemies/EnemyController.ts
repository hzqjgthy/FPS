import * as THREE from 'three';

import type { EnemyArchetype } from './EnemyRuntimeCatalog';
import type { EnemyVisual } from './EnemyVisual';

export interface EnemyUpdateResult {
  damageToPlayer: number;
}

export interface EnemyShotResult {
  hit: boolean;
  killed: boolean;
  zone: 'body' | 'head' | null;
}

export interface EnemyHitInfo {
  distance: number;
  zone: 'body' | 'head';
}

/**
 * 单个敌人的逻辑控制器。
 * 这里集中处理：
 * - 警戒 / 追击 / 攻击状态切换
 * - 移动与场景碰撞
 * - 受伤、死亡、命中判定
 * - 把逻辑状态喂给 EnemyVisual
 */
export class EnemyController {
  private readonly enemyBounds = new THREE.Box3();
  private readonly moveDirection = new THREE.Vector3();
  private readonly colliders: THREE.Box3[];
  private readonly raycaster = new THREE.Raycaster();
  private readonly visual: EnemyVisual;

  private yaw = 0;
  private moveBlend = 0;
  private walkTime = Math.random() * Math.PI * 2;
  private alerted = false;
  private attackCooldown = Math.random() * 0.4;
  private attackActive = false;
  private attackElapsed = 0;
  private attackImpactApplied = false;
  private pendingHitReaction = false;
  private health: number;
  private isDead = false;
  private deathElapsed = 0;
  private readonly baseGroundY: number;
  private readonly archetype: EnemyArchetype;

  constructor(
    scene: THREE.Scene,
    colliders: THREE.Box3[],
    spawnPoint: THREE.Vector3,
    archetype: EnemyArchetype,
  ) {
    this.colliders = colliders;
    this.archetype = archetype;
    this.baseGroundY = spawnPoint.y;
    this.visual = archetype.createVisual();
    this.visual.root.scale.setScalar(archetype.sizeScale);
    this.visual.root.position.copy(spawnPoint);
    this.health = archetype.maxHealth;
    scene.add(this.visual.root);
  }

  public update(
    deltaSeconds: number,
    elapsedSeconds: number,
    playerFeetPosition: THREE.Vector3,
  ): EnemyUpdateResult {
    if (this.isDead) {
      // 死亡后不再参与攻击和追击，只保留尸体动画推进。
      this.deathElapsed = Math.min(
        this.deathElapsed + deltaSeconds,
        this.archetype.corpseDuration,
      );
      this.visual.root.position.y = this.getSupportHeight();
      this.visual.update({
        deltaSeconds,
        elapsedSeconds,
        walkTime: this.walkTime,
        moveBlend: 0,
        alerted: false,
        attacking: false,
        attackProgress: 0,
        hitTriggered: false,
        healthRatio: 0,
        isDead: true,
        deathProgress: THREE.MathUtils.clamp(
          this.deathElapsed / this.archetype.corpseDuration,
          0,
          1,
        ),
      });
      this.visual.root.updateMatrixWorld(true);

      return { damageToPlayer: 0 };
    }

    const horizontalToPlayerX = playerFeetPosition.x - this.visual.root.position.x;
    const horizontalToPlayerZ = playerFeetPosition.z - this.visual.root.position.z;
    const horizontalDistance = Math.hypot(horizontalToPlayerX, horizontalToPlayerZ);
    const verticalDistance = Math.abs(playerFeetPosition.y - this.visual.root.position.y);
    const hitTriggered = this.pendingHitReaction;
    this.pendingHitReaction = false;
    let damageToPlayer = 0;

    // 警戒与丢失目标是两个不同阈值，避免在边缘距离来回抖动。
    if (!this.alerted) {
      this.alerted = horizontalDistance <= this.archetype.alertRange && verticalDistance < 6;
    } else if (
      horizontalDistance >= this.archetype.forgetRange ||
      verticalDistance >= 8
    ) {
      this.alerted = false;
    }

    const canAttack =
      this.alerted &&
      horizontalDistance <= this.archetype.attackRange &&
      verticalDistance < 2.8;
    const shouldChase = this.alerted && !canAttack && horizontalDistance > 0.001;

    if (this.attackCooldown > 0) {
      this.attackCooldown = Math.max(0, this.attackCooldown - deltaSeconds);
    }

    if (canAttack && !this.attackActive && this.attackCooldown === 0) {
      // 近战攻击按“启动 -> 命中时刻 -> 结束”这一整段时间轴推进。
      this.attackActive = true;
      this.attackElapsed = 0;
      this.attackImpactApplied = false;
      this.attackCooldown = this.archetype.attackCooldown;
    }

    if (this.attackActive) {
      this.attackElapsed += deltaSeconds;

      if (
        !this.attackImpactApplied &&
        this.attackElapsed >= this.archetype.attackImpactTime
      ) {
        // 真正造成伤害的瞬间不一定是攻击动作开始的瞬间。
        this.attackImpactApplied = true;

        if (horizontalDistance <= this.archetype.attackRange + 0.45 && verticalDistance < 2.8) {
          damageToPlayer = this.archetype.attackDamage;
        }
      }

      if (this.attackElapsed >= this.archetype.attackDuration) {
        this.attackActive = false;
        this.attackElapsed = 0;
        this.attackImpactApplied = false;
      }
    }

    if (this.alerted && horizontalDistance > 0.001) {
      // 敌人始终缓慢朝向玩家，不会直接瞬间扭头。
      const desiredYaw = Math.atan2(horizontalToPlayerX, -horizontalToPlayerZ);
      const deltaYaw = Math.atan2(
        Math.sin(desiredYaw - this.yaw),
        Math.cos(desiredYaw - this.yaw),
      );

      this.yaw += deltaYaw * Math.min(1, this.archetype.turnSpeed * deltaSeconds);
    }

    if (shouldChase) {
      this.moveDirection
        .set(horizontalToPlayerX, 0, horizontalToPlayerZ)
        .normalize();

      // 仍然使用分轴移动，便于和场景碰撞体做简单稳定的阻挡处理。
      const moveDistance = this.archetype.moveSpeed * deltaSeconds;
      this.tryMoveX(this.moveDirection.x * moveDistance);
      this.tryMoveZ(this.moveDirection.z * moveDistance);
    }

    this.visual.root.position.y = this.getSupportHeight();
    this.visual.root.rotation.y = this.yaw;

    const targetMoveBlend = shouldChase ? 1 : 0;
    this.moveBlend = THREE.MathUtils.damp(
      this.moveBlend,
      targetMoveBlend,
      8,
      deltaSeconds,
    );

    if (this.moveBlend > 0.01) {
      this.walkTime += deltaSeconds * (6.5 + this.moveBlend * 1.8);
    }

    this.visual.update({
      deltaSeconds,
      elapsedSeconds,
      walkTime: this.walkTime,
      moveBlend: this.moveBlend,
      alerted: this.alerted,
      attacking: this.attackActive,
      attackProgress: this.attackActive
        ? THREE.MathUtils.clamp(
            this.attackElapsed / this.archetype.attackDuration,
            0,
            1,
          )
        : 0,
      hitTriggered,
      healthRatio: this.health / this.archetype.maxHealth,
      isDead: false,
      deathProgress: 0,
    });
    this.visual.root.updateMatrixWorld(true);

    return { damageToPlayer };
  }

  public applyDamage(damage: number): EnemyShotResult {
    if (this.isDead) {
      return { hit: false, killed: false, zone: null };
    }

    // 这里不区分身体或头部，只消费已经算好的伤害值。
    this.health = Math.max(0, this.health - damage);

    if (this.health === 0) {
      this.isDead = true;
      this.alerted = false;
      this.attackActive = false;
      this.attackElapsed = 0;
      this.attackImpactApplied = false;
      this.moveBlend = 0;
      this.deathElapsed = 0;
      return { hit: true, killed: true, zone: null };
    }

    this.pendingHitReaction = true;
    return { hit: true, killed: false, zone: null };
  }

  public intersectShot(ray: THREE.Ray, maxDistance: number): EnemyHitInfo | null {
    if (this.isDead) {
      return null;
    }

    // 命中检测只对隐藏 hitVolumes 做射线检测，
    // 不直接对可见模型做射线，避免视觉模型复杂度干扰判定。
    this.raycaster.ray.copy(ray);
    this.raycaster.near = 0;
    this.raycaster.far = maxDistance;

    const hits = this.raycaster.intersectObjects(this.visual.hitVolumes, false);
    const nearestHit = hits[0];

    if (!nearestHit) {
      return null;
    }

    const zone =
      nearestHit.object.userData.hitZone === 'head' ? 'head' : 'body';

    return {
      distance: nearestHit.distance,
      zone,
    };
  }

  public isAlive(): boolean {
    return !this.isDead;
  }

  private tryMoveX(deltaX: number): void {
    if (deltaX === 0) {
      return;
    }

    this.visual.root.position.x += deltaX;

    if (this.intersectsWorld()) {
      this.visual.root.position.x -= deltaX;
    }
  }

  private tryMoveZ(deltaZ: number): void {
    if (deltaZ === 0) {
      return;
    }

    this.visual.root.position.z += deltaZ;

    if (this.intersectsWorld()) {
      this.visual.root.position.z -= deltaZ;
    }
  }

  private intersectsWorld(): boolean {
    const feetPosition = this.visual.root.position;
    const enemyBounds = this.enemyBounds;
    enemyBounds.min.set(
      feetPosition.x - this.archetype.radius,
      feetPosition.y,
      feetPosition.z - this.archetype.radius,
    );

    enemyBounds.max.set(
      feetPosition.x + this.archetype.radius,
      feetPosition.y + this.archetype.height,
      feetPosition.z + this.archetype.radius,
    );

    return this.colliders.some((collider) => {
      // 忽略脚下支撑面，否则敌人站上箱子后也会被自己脚下的平台“卡死”。
      if (collider.max.y <= feetPosition.y + this.archetype.supportEpsilon) {
        return false;
      }

      return collider.intersectsBox(enemyBounds);
    });
  }

  private getSupportHeight(): number {
    const feetPosition = this.visual.root.position;
    const minX = feetPosition.x - this.archetype.radius;
    const maxX = feetPosition.x + this.archetype.radius;
    const minZ = feetPosition.z - this.archetype.radius;
    const maxZ = feetPosition.z + this.archetype.radius;

    let supportHeight = this.baseGroundY;

    for (const collider of this.colliders) {
      const overlapsX = maxX > collider.min.x && minX < collider.max.x;
      const overlapsZ = maxZ > collider.min.z && minZ < collider.max.z;

      if (!overlapsX || !overlapsZ) {
        continue;
      }

      const surfaceY = collider.max.y + this.archetype.supportEpsilon;

      // 只把脚下表面视作支撑面，避免头顶结构把敌人吸上去。
      if (surfaceY > feetPosition.y + this.archetype.supportEpsilon) {
        continue;
      }

      supportHeight = Math.max(supportHeight, surfaceY);
    }

    return supportHeight;
  }

}
