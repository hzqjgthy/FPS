import * as THREE from 'three';

import { SYSTEM_TUNING } from '../config/systemTuning';
import { InputController } from '../input/InputController';

// 这一帧玩家状态会被武器系统和音频系统继续消费。
export interface PlayerFrameState {
  movementAmount: number;
  lookDeltaX: number;
  lookDeltaY: number;
  isSprinting: boolean;
  footstepTriggered: boolean;
  jumpedThisFrame: boolean;
  isGrounded: boolean;
}

/**
 * 玩家控制器只关心第一人称移动与镜头控制：
 * - 鼠标控制 yaw / pitch
 * - WASD 控制平面移动
 * - 跳跃、脚步计时、镜头呼吸和晃动
 * - 与世界碰撞体交互
 */
export class PlayerController {
  // yawPivot 负责水平转向，pitchPivot 负责上下俯仰。
  // 这种双层结构可以避免旋转职责混在一起。
  private readonly yawPivot = new THREE.Group();
  private readonly pitchPivot = new THREE.Group();
  private readonly playerBounds = new THREE.Box3();
  private readonly movementVector = new THREE.Vector3();
  private readonly forwardVector = new THREE.Vector3();
  private readonly rightVector = new THREE.Vector3();
  private readonly input: InputController;
  private readonly colliders: THREE.Box3[];
  private readonly camera: THREE.PerspectiveCamera;

  private pitch = 0;
  private yaw = 0;
  private recoilPitchOffset = 0;
  private recoilYawOffset = 0;
  private viewMotionTime = 0;
  private walkCycle = 0;
  private footstepTimer = 0;
  private wasMovingLastFrame = false;
  private cameraRoll = 0;
  private isJumping = false;
  private jumpElapsed = 0;
  private jumpStartY = 0;
  private readonly baseGroundY: number;
  private recoilRecovery: number;

  constructor(
    scene: THREE.Scene,
    camera: THREE.PerspectiveCamera,
    input: InputController,
    colliders: THREE.Box3[],
    spawnPoint: THREE.Vector3,
    spawnYaw: number,
    recoilRecovery: number,
  ) {
    this.camera = camera;
    this.input = input;
    this.colliders = colliders;
    this.baseGroundY = spawnPoint.y;
    this.recoilRecovery = recoilRecovery;
    this.pitchPivot.position.y = SYSTEM_TUNING.camera.eyeHeight;
    this.pitchPivot.add(camera);
    this.yawPivot.add(this.pitchPivot);
    this.yawPivot.position.copy(spawnPoint);

    this.yaw = spawnYaw;
    this.yawPivot.rotation.y = this.yaw;

    scene.add(this.yawPivot);
  }

  public update(deltaSeconds: number): PlayerFrameState {
    return this.updateWithControls(deltaSeconds, true);
  }

  public updateWithControls(
    deltaSeconds: number,
    controlsEnabled: boolean,
  ): PlayerFrameState {
    // 先消费这一帧输入，再把结果应用到视角和位移上。
    const look = this.input.consumeLookDelta();
    const jumpedThisFrame = controlsEnabled ? this.tryStartJump() : false;

    if (controlsEnabled && this.input.isPointerLocked) {
      this.yaw -= look.x * SYSTEM_TUNING.camera.lookSensitivity;
      this.pitch -= look.y * SYSTEM_TUNING.camera.lookSensitivity;
      this.pitch = THREE.MathUtils.clamp(this.pitch, -1.2, 1.2);
    }

    this.updateJumpState(deltaSeconds);

    this.recoilPitchOffset = THREE.MathUtils.damp(
      this.recoilPitchOffset,
      0,
      this.recoilRecovery,
      deltaSeconds,
    );
    this.recoilYawOffset = THREE.MathUtils.damp(
      this.recoilYawOffset,
      0,
      this.recoilRecovery,
      deltaSeconds,
    );

    this.yawPivot.rotation.y = this.yaw + this.recoilYawOffset;
    this.pitchPivot.rotation.x = THREE.MathUtils.clamp(
      this.pitch + this.recoilPitchOffset,
      -1.2,
      1.2,
    );

    const axes = controlsEnabled && this.input.isPointerLocked
      ? this.input.getMovementAxes()
      : { forward: 0, right: 0 };
    const hasMovementInput = axes.forward !== 0 || axes.right !== 0;
    const isSprinting =
      controlsEnabled && this.input.isPointerLocked && hasMovementInput && this.input.isSprintHeld();
    const isMoving = controlsEnabled && this.input.isPointerLocked && hasMovementInput;
    const footstepTriggered = this.updateViewMotion(
      deltaSeconds,
      axes,
      isMoving,
      isSprinting,
      !this.isJumping,
    );

    this.movementVector.set(0, 0, 0);

    if (hasMovementInput) {
      // 始终以当前 yawPivot 的朝向作为前后左右基准，
      // 这样无论鼠标转到哪里，WASD 都会和视角水平朝向一致。
      this.forwardVector.set(0, 0, -1).applyQuaternion(this.yawPivot.quaternion).normalize();
      this.rightVector.set(1, 0, 0).applyQuaternion(this.yawPivot.quaternion).normalize();

      this.movementVector.addScaledVector(this.forwardVector, axes.forward);
      this.movementVector.addScaledVector(this.rightVector, axes.right);
      this.movementVector.normalize();

      const moveDistance =
        SYSTEM_TUNING.player.moveSpeed *
        (isSprinting ? SYSTEM_TUNING.player.sprintMultiplier : 1) *
        deltaSeconds;
      this.tryMoveX(this.movementVector.x * moveDistance);
      this.tryMoveZ(this.movementVector.z * moveDistance);
    }

    return {
      movementAmount:
        this.movementVector.length() *
        (isSprinting ? SYSTEM_TUNING.player.sprintMultiplier : 1),
      lookDeltaX: look.x,
      lookDeltaY: look.y,
      isSprinting,
      footstepTriggered,
      jumpedThisFrame,
      isGrounded: !this.isJumping,
    };
  }

  public applyRecoil(verticalKick: number, horizontalKick: number): void {
    this.recoilPitchOffset = THREE.MathUtils.clamp(
      this.recoilPitchOffset + verticalKick,
      -0.12,
      0.2,
    );
    this.recoilYawOffset = THREE.MathUtils.clamp(
      this.recoilYawOffset + horizontalKick,
      -0.08,
      0.08,
    );
    this.yawPivot.rotation.y = this.yaw + this.recoilYawOffset;
    this.pitchPivot.rotation.x = THREE.MathUtils.clamp(
      this.pitch + this.recoilPitchOffset,
      -1.2,
      1.2,
    );
  }

  public setRecoilRecovery(recovery: number): void {
    this.recoilRecovery = recovery;
  }

  public copyFeetPosition(target: THREE.Vector3): void {
    target.copy(this.yawPivot.position);
  }

  private tryMoveX(deltaX: number): void {
    if (deltaX === 0) {
      return;
    }

    this.yawPivot.position.x += deltaX;

    if (this.intersectsWorld()) {
      this.yawPivot.position.x -= deltaX;
    }
  }

  private tryMoveZ(deltaZ: number): void {
    if (deltaZ === 0) {
      return;
    }

    this.yawPivot.position.z += deltaZ;

    if (this.intersectsWorld()) {
      this.yawPivot.position.z -= deltaZ;
    }
  }

  private intersectsWorld(): boolean {
    const feetPosition = this.yawPivot.position;

    this.playerBounds.min.set(
      feetPosition.x - SYSTEM_TUNING.player.radius,
      feetPosition.y,
      feetPosition.z - SYSTEM_TUNING.player.radius,
    );

    this.playerBounds.max.set(
      feetPosition.x + SYSTEM_TUNING.player.radius,
      feetPosition.y + SYSTEM_TUNING.player.height,
      feetPosition.z + SYSTEM_TUNING.player.radius,
    );

    return this.colliders.some((collider) => {
      // 忽略当前脚下正在支撑玩家的表面，
      // 否则站在箱子上时，箱子自己的碰撞体会把水平移动也挡住。
      if (collider.max.y <= feetPosition.y + SYSTEM_TUNING.player.supportEpsilon) {
        return false;
      }

      return collider.intersectsBox(this.playerBounds);
    });
  }

  private updateViewMotion(
    deltaSeconds: number,
    axes: { forward: number; right: number },
    isMoving: boolean,
    isSprinting: boolean,
    isGrounded: boolean,
  ): boolean {
    // 镜头运动由两层组成：
    // 1. 静止时的轻微呼吸
    // 2. 行走 / 冲刺时的 bob 和侧移倾斜
    this.viewMotionTime += deltaSeconds;

    const breathX =
      Math.sin(this.viewMotionTime * 0.9) * SYSTEM_TUNING.camera.breathAmplitudeX;
    const breathY =
      Math.sin(this.viewMotionTime * 1.8) * SYSTEM_TUNING.camera.breathAmplitudeY;

    let targetX = breathX;
    let targetY = breathY;
    let targetRoll = 0;

    if (isMoving && isGrounded) {
      this.walkCycle +=
        deltaSeconds *
        (isSprinting ? SYSTEM_TUNING.camera.sprintBobSpeed : SYSTEM_TUNING.camera.walkBobSpeed);

      const bobAmplitudeX = isSprinting
        ? SYSTEM_TUNING.camera.sprintBobAmplitudeX
        : SYSTEM_TUNING.camera.walkBobAmplitudeX;
      const bobAmplitudeY = isSprinting
        ? SYSTEM_TUNING.camera.sprintBobAmplitudeY
        : SYSTEM_TUNING.camera.walkBobAmplitudeY;

      targetX += Math.sin(this.walkCycle) * bobAmplitudeX;
      targetY += Math.abs(Math.cos(this.walkCycle)) * bobAmplitudeY;
      targetRoll =
        axes.right * SYSTEM_TUNING.camera.strafeLeanAmount +
        Math.sin(this.walkCycle) * SYSTEM_TUNING.camera.strafeLeanAmount * 0.45;
    }

    this.camera.position.x = THREE.MathUtils.damp(
      this.camera.position.x,
      targetX,
      SYSTEM_TUNING.camera.viewSmoothing,
      deltaSeconds,
    );
    this.camera.position.y = THREE.MathUtils.damp(
      this.camera.position.y,
      targetY,
      SYSTEM_TUNING.camera.viewSmoothing,
      deltaSeconds,
    );
    this.cameraRoll = THREE.MathUtils.damp(
      this.cameraRoll,
      targetRoll,
      SYSTEM_TUNING.camera.viewSmoothing,
      deltaSeconds,
    );
    this.camera.rotation.z = this.cameraRoll;

    return this.updateFootstepTimer(deltaSeconds, isMoving && isGrounded, isSprinting);
  }

  private updateFootstepTimer(
    deltaSeconds: number,
    isMoving: boolean,
    isSprinting: boolean,
  ): boolean {
    // 这里只负责“什么时候该触发一次脚步事件”，真正播放哪个音频在外层处理。
    if (!isMoving) {
      this.wasMovingLastFrame = false;
      this.footstepTimer = 0;
      return false;
    }

    if (!this.wasMovingLastFrame) {
      this.wasMovingLastFrame = true;
      this.footstepTimer = 0.05;
    }

    this.footstepTimer -= deltaSeconds;

    if (this.footstepTimer > 0) {
      return false;
    }

    this.footstepTimer += isSprinting
      ? SYSTEM_TUNING.audio.sprintStepInterval
      : SYSTEM_TUNING.audio.walkStepInterval;
    return true;
  }

  private tryStartJump(): boolean {
    const wantsToJump = this.input.consumeJumpPressed();

    if (!wantsToJump || this.isJumping) {
      return false;
    }

    this.jumpStartY = this.getSupportHeight();
    this.jumpElapsed = 0;
    this.isJumping = true;
    // 起跳瞬间先把脚底高度对齐到当前支撑面，避免从斜坡/箱子边缘起跳时抖动。
    this.yawPivot.position.y = this.jumpStartY;
    return true;
  }

  private updateJumpState(deltaSeconds: number): void {
    if (!this.isJumping) {
      this.yawPivot.position.y = this.getSupportHeight();
      return;
    }

    const previousFeetY = this.yawPivot.position.y;
    this.jumpElapsed += deltaSeconds;

    const progress = Math.min(
      this.jumpElapsed / SYSTEM_TUNING.player.jumpDuration,
      1,
    );
    // 使用半个正弦波模拟起跳到落地的一整个跳跃弧线。
    const jumpOffset = Math.sin(progress * Math.PI) * SYSTEM_TUNING.player.jumpHeight;
    const targetFeetY = this.jumpStartY + jumpOffset;
    const landingSurfaceY = this.findLandingSurfaceHeight(previousFeetY, targetFeetY);

    if (landingSurfaceY !== null) {
      this.isJumping = false;
      this.jumpElapsed = 0;
      this.yawPivot.position.y = landingSurfaceY;
      return;
    }

    this.yawPivot.position.y = targetFeetY;

    if (progress >= 1) {
      this.isJumping = false;
      this.jumpElapsed = 0;
      this.yawPivot.position.y = this.getSupportHeight();
    }
  }

  private getSupportHeight(): number {
    const minX = this.yawPivot.position.x - SYSTEM_TUNING.player.radius;
    const maxX = this.yawPivot.position.x + SYSTEM_TUNING.player.radius;
    const minZ = this.yawPivot.position.z - SYSTEM_TUNING.player.radius;
    const maxZ = this.yawPivot.position.z + SYSTEM_TUNING.player.radius;
    const currentFeetY = this.yawPivot.position.y;

    let supportHeight = this.baseGroundY;

    for (const collider of this.colliders) {
      const overlapsX = maxX > collider.min.x && minX < collider.max.x;
      const overlapsZ = maxZ > collider.min.z && minZ < collider.max.z;

      if (!overlapsX || !overlapsZ) {
        continue;
      }

      const surfaceY = collider.max.y + SYSTEM_TUNING.player.supportEpsilon;

      // 只把“脚底以下或接近脚底”的表面视作支撑面。
      // 这样头顶门框、横梁之类的几何体就不会把玩家吸到上面去。
      if (surfaceY > currentFeetY + SYSTEM_TUNING.player.supportEpsilon) {
        continue;
      }

      supportHeight = Math.max(supportHeight, surfaceY);
    }

    return supportHeight;
  }

  private findLandingSurfaceHeight(
    previousFeetY: number,
    targetFeetY: number,
  ): number | null {
    // 只在下落阶段寻找落点，避免上升时误判撞到的平台为落地。
    if (targetFeetY >= previousFeetY) {
      return null;
    }

    const minX = this.yawPivot.position.x - SYSTEM_TUNING.player.radius;
    const maxX = this.yawPivot.position.x + SYSTEM_TUNING.player.radius;
    const minZ = this.yawPivot.position.z - SYSTEM_TUNING.player.radius;
    const maxZ = this.yawPivot.position.z + SYSTEM_TUNING.player.radius;
    const minLandingY = targetFeetY - SYSTEM_TUNING.player.supportEpsilon;
    const maxLandingY = previousFeetY + SYSTEM_TUNING.player.supportEpsilon;

    let landingSurfaceY: number | null = null;

    for (const collider of this.colliders) {
      const overlapsX = maxX > collider.min.x && minX < collider.max.x;
      const overlapsZ = maxZ > collider.min.z && minZ < collider.max.z;

      if (!overlapsX || !overlapsZ) {
        continue;
      }

      const surfaceY = collider.max.y + SYSTEM_TUNING.player.supportEpsilon;

      if (surfaceY < minLandingY || surfaceY > maxLandingY) {
        continue;
      }

      landingSurfaceY = landingSurfaceY === null
        ? surfaceY
        : Math.max(landingSurfaceY, surfaceY);
    }

    if (
      this.baseGroundY >= minLandingY &&
      this.baseGroundY <= maxLandingY
    ) {
      landingSurfaceY = landingSurfaceY === null
        ? this.baseGroundY
        : Math.max(landingSurfaceY, this.baseGroundY);
    }

    return landingSurfaceY;
  }
}
