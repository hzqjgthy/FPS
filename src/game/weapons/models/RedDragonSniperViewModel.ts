import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

import type { PlayerFrameState } from '../../player/PlayerController';
import type {
  WeaponFrameInput,
  WeaponFrameState,
  WeaponTuning,
  WeaponViewModel,
} from '../WeaponTypes';

interface RedDragonSniperAsset {
  scene: THREE.Group;
  animations: THREE.AnimationClip[];
}

let redDragonSniperAssetPromise: Promise<RedDragonSniperAsset> | null = null;

export class RedDragonSniperViewModel implements WeaponViewModel {
  private readonly root = new THREE.Group();
  private readonly modelPivot = new THREE.Group();
  private readonly basePosition = new THREE.Vector3(0.48, -0.46, -0.86);
  private readonly baseRotation = new THREE.Euler(-0.065, -0.14, -0.018);
  private readonly sway = new THREE.Vector2();
  private readonly muzzleFlash = new THREE.Group();
  private readonly muzzleFlashMaterials: THREE.MeshBasicMaterial[] = [];
  private readonly muzzleLight = new THREE.PointLight(0xffc783, 0, 11, 2.2);
  private readonly actions = new Map<string, THREE.AnimationAction>();
  private readonly tuning: WeaponTuning;
  private readonly viewModelScale: number;
  private readonly bounds = new THREE.Box3();
  private readonly boundsSize = new THREE.Vector3();

  private mixer: THREE.AnimationMixer | null = null;
  private currentLoopAction = '';
  private fireReactionActive = false;
  private bobTime = 0;
  private fireCooldown = 0;
  private flashTimer = 0;
  private flashScale = 1;
  private recoilKick = 0;
  private recoilPitch = 0;
  private recoilRoll = 0;

  constructor(
    camera: THREE.PerspectiveCamera,
    tuning: WeaponTuning,
    viewModelScale: number = 1,
  ) {
    this.tuning = tuning;
    this.viewModelScale = viewModelScale;
    this.root.name = 'red-dragon-sniper-view-model';
    this.modelPivot.name = 'red-dragon-sniper-model-pivot';
    this.root.add(this.modelPivot);
    this.buildMuzzleFlash();
    this.root.position.copy(this.basePosition);
    this.root.rotation.copy(this.baseRotation);
    camera.add(this.root);

    void this.loadModel();
  }

  public update(
    deltaSeconds: number,
    elapsedSeconds: number,
    playerState: PlayerFrameState,
    weaponInput: WeaponFrameInput,
  ): WeaponFrameState {
    const swayTargetX = THREE.MathUtils.clamp(-playerState.lookDeltaX * 0.0009, -0.05, 0.05);
    const swayTargetY = THREE.MathUtils.clamp(-playerState.lookDeltaY * 0.0008, -0.035, 0.035);
    let firedThisFrame = false;
    let cameraKickVertical = 0;
    let cameraKickHorizontal = 0;

    this.mixer?.update(deltaSeconds);
    this.fireCooldown = Math.max(0, this.fireCooldown - deltaSeconds);
    this.flashTimer = Math.max(0, this.flashTimer - deltaSeconds);

    if (weaponInput.wantsToFire && this.fireCooldown === 0) {
      this.fireCooldown = this.tuning.fireInterval;
      this.flashTimer = this.tuning.muzzleFlashDuration;
      this.flashScale = THREE.MathUtils.randFloat(1.02, 1.42);
      this.muzzleFlash.rotation.z = Math.random() * Math.PI;
      this.recoilKick = Math.min(this.recoilKick + this.tuning.recoilKickBack, 0.42);
      this.recoilPitch = Math.min(this.recoilPitch + this.tuning.recoilRotationX, 0.28);
      this.recoilRoll = THREE.MathUtils.clamp(
        this.recoilRoll + THREE.MathUtils.randFloatSpread(this.tuning.recoilRotationZ),
        -0.12,
        0.12,
      );
      this.playOnce('fire');
      this.fireReactionActive = true;
      firedThisFrame = true;
      cameraKickVertical = this.tuning.cameraKickVertical;
      cameraKickHorizontal = THREE.MathUtils.randFloatSpread(
        this.tuning.cameraKickHorizontal,
      );
    }

    const firePlaying = this.fireReactionActive && this.isActionRunning('fire');

    if (!firePlaying) {
      this.fireReactionActive = false;

      if (playerState.isSprinting && playerState.movementAmount > 0.01) {
        this.playLoop('sprint');
      } else {
        this.playLoop('idle');
      }
    }

    this.sway.x = THREE.MathUtils.damp(this.sway.x, swayTargetX, 10, deltaSeconds);
    this.sway.y = THREE.MathUtils.damp(this.sway.y, swayTargetY, 10, deltaSeconds);
    this.recoilKick = THREE.MathUtils.damp(
      this.recoilKick,
      0,
      this.tuning.recoilRecovery,
      deltaSeconds,
    );
    this.recoilPitch = THREE.MathUtils.damp(
      this.recoilPitch,
      0,
      this.tuning.recoilRecovery,
      deltaSeconds,
    );
    this.recoilRoll = THREE.MathUtils.damp(
      this.recoilRoll,
      0,
      this.tuning.recoilRecovery,
      deltaSeconds,
    );

    if (playerState.movementAmount > 0) {
      this.bobTime +=
        deltaSeconds *
        this.tuning.bobSpeed *
        (playerState.isSprinting ? 1.22 : 1);
    }

    const movementWeight = playerState.movementAmount * this.tuning.bobAmount;
    const walkSwayX = Math.sin(this.bobTime) * movementWeight;
    const walkSwayY = Math.abs(Math.cos(this.bobTime * 2)) * movementWeight * 0.56;
    const breathing = Math.sin(elapsedSeconds * 1.2) * 0.0038;

    this.root.position.set(
      this.basePosition.x + walkSwayX + this.sway.x * 0.48,
      this.basePosition.y - walkSwayY + this.sway.y * 0.3 + breathing - this.recoilKick * 0.18,
      this.basePosition.z +
        Math.abs(Math.sin(this.bobTime)) * movementWeight * 0.26 +
        this.recoilKick,
    );

    this.root.rotation.set(
      this.baseRotation.x + this.sway.y * 0.62 + walkSwayY * 0.22 + this.recoilPitch,
      this.baseRotation.y + this.sway.x * 0.92,
      this.baseRotation.z + this.sway.x * 1.1 + walkSwayX * 0.28 + this.recoilRoll,
    );

    this.updateMuzzleFlash();

    return {
      firedThisFrame,
      cameraKickVertical,
      cameraKickHorizontal,
    };
  }

  public dispose(): void {
    this.mixer?.stopAllAction();
    this.actions.clear();
    this.modelPivot.clear();
    this.root.removeFromParent();
  }

  private async loadModel(): Promise<void> {
    try {
      const asset = await loadRedDragonSniperAsset();
      const scene = asset.scene.clone(true);

      this.modelPivot.clear();
      this.modelPivot.add(scene);
      this.modelPivot.position.set(0, 0, 0);
      // 枪03 资源的默认前向与当前武器系统约定相反，
      // 这里绕 Y 轴旋转 180 度，把枪口转回朝向屏幕前方。
      this.modelPivot.rotation.set(0, Math.PI, 0);
      this.bounds.setFromObject(scene);
      this.bounds.getSize(this.boundsSize);
      const sourceLength = Math.max(this.boundsSize.z, 0.001);
      const normalizedScale = THREE.MathUtils.clamp(1.18 / sourceLength, 1, 6);
      this.modelPivot.scale.setScalar(normalizedScale * this.viewModelScale);

      scene.traverse((object) => {
        const mesh = object as THREE.Mesh;

        if (!mesh.isMesh) {
          return;
        }

        mesh.castShadow = true;
        mesh.receiveShadow = true;
      });

      this.mixer = new THREE.AnimationMixer(scene);
      this.actions.clear();

      for (const clip of asset.animations) {
        const action = this.mixer.clipAction(clip);
        action.enabled = true;
        action.clampWhenFinished = true;
        this.actions.set(clip.name, action);
      }

      this.playLoop('idle');
    } catch (error) {
      console.warn('Failed to load Red Dragon Tech Sniper weapon asset.', error);
    }
  }

  private playLoop(name: string): void {
    if (this.currentLoopAction === name) {
      return;
    }

    const next = this.actions.get(name);

    if (!next) {
      return;
    }

    for (const action of this.actions.values()) {
      action.stop();
    }

    next.reset();
    next.setLoop(THREE.LoopRepeat, Infinity);
    next.clampWhenFinished = false;
    next.play();
    this.currentLoopAction = name;
  }

  private playOnce(name: string): void {
    const action = this.actions.get(name);

    if (!action) {
      return;
    }

    for (const other of this.actions.values()) {
      other.stop();
    }

    action.reset();
    action.setLoop(THREE.LoopOnce, 1);
    action.clampWhenFinished = true;
    action.play();
    this.currentLoopAction = '';
  }

  private isActionRunning(name: string): boolean {
    const action = this.actions.get(name);

    if (!action) {
      return false;
    }

    return action.isRunning();
  }

  private buildMuzzleFlash(): void {
    this.muzzleFlash.position.set(0.11, 0.055, -1.6);
    this.muzzleFlash.visible = false;

    const coreMaterial = new THREE.MeshBasicMaterial({
      color: 0xfff2c0,
      transparent: true,
      opacity: 0.98,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: 0xff7e32,
      transparent: true,
      opacity: 0.78,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.DoubleSide,
    });

    this.muzzleFlashMaterials.push(coreMaterial, glowMaterial);

    const flareA = new THREE.Mesh(new THREE.PlaneGeometry(0.14, 0.36), coreMaterial);
    const flareB = new THREE.Mesh(new THREE.PlaneGeometry(0.28, 0.14), glowMaterial);
    flareB.rotation.z = Math.PI / 2;

    this.muzzleLight.position.set(0, 0, 0.1);

    this.muzzleFlash.add(flareA, flareB, this.muzzleLight);
    this.root.add(this.muzzleFlash);
  }

  private updateMuzzleFlash(): void {
    if (this.flashTimer <= 0) {
      this.muzzleFlash.visible = false;
      this.muzzleLight.intensity = 0;
      return;
    }

    const normalizedFlash = this.flashTimer / this.tuning.muzzleFlashDuration;
    const flashOpacity = THREE.MathUtils.clamp(normalizedFlash, 0, 1);
    const flashSize = this.flashScale * (0.96 + flashOpacity * 0.42);

    this.muzzleFlash.visible = true;
    this.muzzleFlash.scale.setScalar(flashSize);
    this.muzzleLight.intensity = 3 * flashOpacity;

    if (this.muzzleFlashMaterials[0]) {
      this.muzzleFlashMaterials[0].opacity = 0.62 + flashOpacity * 0.36;
    }

    if (this.muzzleFlashMaterials[1]) {
      this.muzzleFlashMaterials[1].opacity = 0.36 + flashOpacity * 0.34;
    }
  }
}

async function loadRedDragonSniperAsset(): Promise<RedDragonSniperAsset> {
  if (!redDragonSniperAssetPromise) {
    const loader = new GLTFLoader();
    const assetUrl = new URL(
      '../../../../素材/武器/枪/枪03/枪的模型/model.glb',
      import.meta.url,
    ).href;

    redDragonSniperAssetPromise = loader.loadAsync(assetUrl).then((gltf) => ({
      scene: gltf.scene,
      animations: gltf.animations,
    }));
  }

  return redDragonSniperAssetPromise;
}
