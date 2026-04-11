import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

import { EnemyHealthBar } from '../EnemyHealthBar';
import type { EnemyVisual, EnemyVisualState } from '../EnemyVisual';

interface RotwoodOverlordAsset {
  scene: THREE.Group;
  animations: THREE.AnimationClip[];
}

let rotwoodOverlordAssetPromise: Promise<RotwoodOverlordAsset> | null = null;

export async function loadRotwoodOverlordFactory(): Promise<() => EnemyVisual> {
  const asset = await loadRotwoodOverlordAsset();
  return (): EnemyVisual => new RotwoodOverlordModel(asset);
}

class RotwoodOverlordModel implements EnemyVisual {
  public readonly root: THREE.Group;
  public readonly hitVolumes: THREE.Mesh[] = [];

  private readonly mixer: THREE.AnimationMixer;
  private readonly actions = new Map<string, THREE.AnimationAction>();
  private readonly healthBar = new EnemyHealthBar(4.15, 1.34, 0.26);
  private currentLoopAction = '';
  private hitReactionActive = false;
  private wasAttacking = false;
  private wasDead = false;

  constructor(asset: RotwoodOverlordAsset) {
    this.root = asset.scene.clone(true);
    this.root.name = 'enemy-rotwood-overlord';
    this.mixer = new THREE.AnimationMixer(this.root);

    for (const clip of asset.animations) {
      const action = this.mixer.clipAction(clip);
      action.enabled = true;
      action.clampWhenFinished = true;
      this.actions.set(clip.name, action);
    }

    this.buildHitVolumes();
    this.root.add(this.healthBar.root);
    this.playLoop('Idle');
  }

  public update(frame: EnemyVisualState): void {
    this.mixer.update(frame.deltaSeconds);

    if (frame.isDead) {
      if (!this.wasDead) {
        this.playOnce('Death');
      }

      this.wasDead = true;
      this.wasAttacking = false;
      this.hitReactionActive = false;
    } else {
      this.wasDead = false;

      if (frame.hitTriggered) {
        this.playOnce('Hit');
        this.hitReactionActive = true;
      }

      const hitPlaying = this.hitReactionActive && this.isActionRunning('Hit');

      if (frame.attacking) {
        if (!this.wasAttacking && !hitPlaying) {
          this.playOnce('Attack');
        }
      } else if (!hitPlaying) {
        this.hitReactionActive = false;

        if (frame.moveBlend > 0.6) {
          this.playLoop('Run');
        } else if (frame.moveBlend > 0.08) {
          this.playLoop('Walk');
        } else {
          this.playLoop('Idle');
        }
      }

      if (!hitPlaying && this.hitReactionActive) {
        this.hitReactionActive = false;
      }

      this.wasAttacking = hitPlaying ? false : frame.attacking;
    }

    this.healthBar.update(frame.healthRatio, frame.elapsedSeconds, frame.isDead);
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

  private buildHitVolumes(): void {
    const hitMaterial = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0,
      depthWrite: false,
    });

    const hips = this.root.getObjectByName('Hips') ?? this.root;
    const spine = this.root.getObjectByName('SpineHigh')
      ?? this.root.getObjectByName('SpineLow')
      ?? this.root;
    const headNode = this.root.getObjectByName('Head') ?? this.root;

    const lowerBody = new THREE.Mesh(
      new THREE.BoxGeometry(1.28, 1.64, 1.06),
      hitMaterial,
    );
    lowerBody.position.set(0, 0.18, 0);
    lowerBody.userData.hitZone = 'body';

    const torso = new THREE.Mesh(
      new THREE.BoxGeometry(1.56, 1.42, 1.18),
      hitMaterial,
    );
    torso.position.set(0, 0.28, 0.04);
    torso.userData.hitZone = 'body';

    // Boss 头部只覆盖面部主干与核心头冠区域，不把外侧木刺与冠刺算进爆头。
    const head = new THREE.Mesh(
      new THREE.BoxGeometry(0.34, 0.78, 0.34),
      hitMaterial,
    );
    head.position.set(0, 0.14, 0.02);
    head.userData.hitZone = 'head';

    hips.add(lowerBody);
    spine.add(torso);
    headNode.add(head);

    this.hitVolumes.push(lowerBody, torso, head);
  }
}

async function loadRotwoodOverlordAsset(): Promise<RotwoodOverlordAsset> {
  if (!rotwoodOverlordAssetPromise) {
    const loader = new GLTFLoader();
    const assetUrl = new URL(
      '../../../../素材/敌人/敌人04/敌人模型/model.glb',
      import.meta.url,
    ).href;

    rotwoodOverlordAssetPromise = loader.loadAsync(assetUrl).then((gltf) => ({
      scene: gltf.scene,
      animations: gltf.animations,
    }));
  }

  return rotwoodOverlordAssetPromise;
}
