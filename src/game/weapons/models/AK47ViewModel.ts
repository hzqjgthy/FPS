import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

import type { PlayerFrameState } from '../../player/PlayerController';
import type {
  WeaponFrameInput,
  WeaponFrameState,
  WeaponTuning,
  WeaponViewModel,
} from '../WeaponTypes';

interface AK47Asset {
  scene: THREE.Group;
  animations: THREE.AnimationClip[];
}

let ak47AssetPromise: Promise<AK47Asset> | null = null;

export class AK47ViewModel implements WeaponViewModel {
  private readonly root = new THREE.Group();
  private readonly modelPivot = new THREE.Group();
  private readonly basePosition = new THREE.Vector3(0.42, -0.4, -0.92);
  private readonly baseRotation = new THREE.Euler(-0.08, -0.14, -0.02);
  private readonly sway = new THREE.Vector2();
  private readonly muzzleFlash = new THREE.Group();
  private readonly muzzleFlashMaterials: THREE.MeshBasicMaterial[] = [];
  private readonly muzzleLight = new THREE.PointLight(0xffc15a, 0, 8, 2);
  private readonly actions = new Map<string, THREE.AnimationAction>();
  private readonly tuning: WeaponTuning;
  private readonly viewModelScale: number;

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
    this.root.name = 'ak47-view-model';
    this.modelPivot.name = 'ak47-model-pivot';
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
    const swayTargetX = THREE.MathUtils.clamp(-playerState.lookDeltaX * 0.0012, -0.06, 0.06);
    const swayTargetY = THREE.MathUtils.clamp(-playerState.lookDeltaY * 0.001, -0.04, 0.04);
    let firedThisFrame = false;
    let cameraKickVertical = 0;
    let cameraKickHorizontal = 0;

    this.mixer?.update(deltaSeconds);
    this.fireCooldown = Math.max(0, this.fireCooldown - deltaSeconds);
    this.flashTimer = Math.max(0, this.flashTimer - deltaSeconds);

    if (weaponInput.wantsToFire && this.fireCooldown === 0) {
      this.fireCooldown = this.tuning.fireInterval;
      this.flashTimer = this.tuning.muzzleFlashDuration;
      this.flashScale = THREE.MathUtils.randFloat(0.85, 1.25);
      this.muzzleFlash.rotation.z = Math.random() * Math.PI;
      this.recoilKick = Math.min(this.recoilKick + this.tuning.recoilKickBack, 0.24);
      this.recoilPitch = Math.min(this.recoilPitch + this.tuning.recoilRotationX, 0.18);
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

    this.sway.x = THREE.MathUtils.damp(this.sway.x, swayTargetX, 12, deltaSeconds);
    this.sway.y = THREE.MathUtils.damp(this.sway.y, swayTargetY, 12, deltaSeconds);
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
        (playerState.isSprinting ? 1.3 : 1);
    }

    const movementWeight = playerState.movementAmount * this.tuning.bobAmount;
    const walkSwayX = Math.sin(this.bobTime) * movementWeight;
    const walkSwayY = Math.abs(Math.cos(this.bobTime * 2)) * movementWeight * 0.7;
    const breathing = Math.sin(elapsedSeconds * 1.4) * 0.005;

    this.root.position.set(
      this.basePosition.x + walkSwayX + this.sway.x * 0.65,
      this.basePosition.y - walkSwayY + this.sway.y * 0.4 + breathing - this.recoilKick * 0.25,
      this.basePosition.z +
        Math.abs(Math.sin(this.bobTime)) * movementWeight * 0.4 +
        this.recoilKick,
    );

    this.root.rotation.set(
      this.baseRotation.x + this.sway.y * 0.75 + walkSwayY * 0.4 + this.recoilPitch,
      this.baseRotation.y + this.sway.x * 1.1,
      this.baseRotation.z + this.sway.x * 1.5 + walkSwayX * 0.45 + this.recoilRoll,
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
      const asset = await loadAK47Asset();
      const scene = asset.scene.clone(true);

      this.modelPivot.clear();
      this.modelPivot.add(scene);
      this.modelPivot.position.set(0, 0, 0);
      this.modelPivot.rotation.set(0, 0, 0);
      this.modelPivot.scale.setScalar(this.viewModelScale);

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
      console.warn('Failed to load AK-47 weapon asset.', error);
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
    this.muzzleFlash.position.set(0.05, 0.03, -1.06);
    this.muzzleFlash.visible = false;

    const coreMaterial = new THREE.MeshBasicMaterial({
      color: 0xfff2b0,
      transparent: true,
      opacity: 0.95,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: 0xff9a3c,
      transparent: true,
      opacity: 0.7,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.DoubleSide,
    });

    this.muzzleFlashMaterials.push(coreMaterial, glowMaterial);

    const flareA = new THREE.Mesh(new THREE.PlaneGeometry(0.12, 0.28), coreMaterial);
    const flareB = new THREE.Mesh(new THREE.PlaneGeometry(0.22, 0.12), glowMaterial);
    flareB.rotation.z = Math.PI / 2;

    this.muzzleLight.position.set(0, 0, 0.08);

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
    const flashSize = this.flashScale * (0.85 + flashOpacity * 0.4);

    this.muzzleFlash.visible = true;
    this.muzzleFlash.scale.setScalar(flashSize);
    this.muzzleLight.intensity = 2.4 * flashOpacity;

    if (this.muzzleFlashMaterials[0]) {
      this.muzzleFlashMaterials[0].opacity = 0.55 + flashOpacity * 0.4;
    }

    if (this.muzzleFlashMaterials[1]) {
      this.muzzleFlashMaterials[1].opacity = 0.3 + flashOpacity * 0.35;
    }
  }
}

async function loadAK47Asset(): Promise<AK47Asset> {
  if (!ak47AssetPromise) {
    const loader = new GLTFLoader();
    const assetUrl = new URL(
      '../../../../素材/武器/枪/枪01/枪的模型/model.glb',
      import.meta.url,
    ).href;

    ak47AssetPromise = loader.loadAsync(assetUrl).then((gltf) => ({
      scene: gltf.scene,
      animations: gltf.animations,
    }));
  }

  return ak47AssetPromise;
}
