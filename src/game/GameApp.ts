import * as THREE from 'three';

import { FootstepAudio } from './audio/FootstepAudio';
import { GunfireAudio } from './audio/GunfireAudio';
import { JumpAudio } from './audio/JumpAudio';
import { ShotResolver } from './combat/ShotResolver';
import { SYSTEM_TUNING } from './config/systemTuning';
import type { GameSelectionConfig } from './content/gameSelection';
import { getLevelDefinition, type LevelDefinition } from './content/levels/levelCatalog';
import {
  getWeaponDefinition,
} from './content/weapons/weaponCatalog';
import { EnemyManager } from './enemies/EnemyManager';
import { BulletImpactSystem } from './effects/BulletImpactSystem';
import { InputController } from './input/InputController';
import { PlayerController } from './player/PlayerController';
import { Hud } from './ui/Hud';
import type { WeaponDefinition, WeaponViewModel } from './weapons/WeaponTypes';

export interface GameAppCallbacks {
  onPauseRequested?: () => void;
}

/**
 * 游戏运行时总装配器。
 * 这里负责把场景、输入、玩家、武器、敌人、HUD、音频串成一个完整的游戏循环。
 *
 * 如果你后面要扩展新关卡 / 新武器 / 新敌人，通常先从这里看：
 * - 资源和系统是如何被创建的
 * - 每一帧更新时，调用顺序是什么
 * - HUD 文案从哪里注入
 */
export class GameApp {
  private readonly shell = document.createElement('main');
  private readonly viewport = document.createElement('div');
  private readonly renderer = new THREE.WebGLRenderer({ antialias: true });
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(
    SYSTEM_TUNING.camera.fov,
    window.innerWidth / window.innerHeight,
    SYSTEM_TUNING.camera.near,
    SYSTEM_TUNING.camera.far,
  );
  private readonly clock = new THREE.Clock();
  private readonly activeLevel: LevelDefinition;
  private readonly weaponLoadout: WeaponDefinition[];
  private readonly input: InputController;
  private readonly player: PlayerController;
  private readonly hud: Hud;
  private readonly enemies: EnemyManager;
  private readonly bulletImpacts: BulletImpactSystem;
  private readonly shotResolver: ShotResolver;
  private readonly playerFeetPosition = new THREE.Vector3();
  private readonly footsteps = new FootstepAudio();
  private readonly jumpAudio = new JumpAudio();
  private activeWeapon!: WeaponDefinition;
  private weapon!: WeaponViewModel;
  private gunfire!: GunfireAudio;
  private animationFrameId = 0;
  private playerHealth: number = SYSTEM_TUNING.player.maxHealth;
  private killCount = 0;
  private damageFlash = 0;
  private elapsedSeconds = 0;
  private isInitialized = false;
  private isRunning = false;
  private startPromise: Promise<void> | null = null;
  private currentWeaponIndex = 0;
  private readonly callbacks: GameAppCallbacks;

  private readonly handleResize = (): void => {
    // 摄像机投影和渲染尺寸必须一起更新，否则画面会被拉伸。
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();

    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  };

  private readonly animate = (): void => {
    if (!this.isRunning) {
      return;
    }

    // 主循环顺序：
    // 1. 更新玩家输入和位移
    // 2. 更新敌人 AI
    // 3. 更新武器表现
    // 4. 结算射击 / 受伤 / 音效
    // 5. 刷新 HUD
    // 6. 渲染当前帧
    const deltaSeconds = Math.min(this.clock.getDelta(), 0.033);
    this.elapsedSeconds += deltaSeconds;

    if (this.input.consumePausePressed()) {
      this.pause();
      this.callbacks.onPauseRequested?.();
      return;
    }

    const playerAlive = this.playerHealth > 0;
    const playerState = this.player.updateWithControls(deltaSeconds, playerAlive);

    if (playerAlive && this.input.consumeWeaponSwitchPressed()) {
      this.cycleWeaponForward();
    }

    this.player.copyFeetPosition(this.playerFeetPosition);
    const enemyFrame = this.enemies.update(
      deltaSeconds,
      this.elapsedSeconds,
      this.playerFeetPosition,
    );
    const weaponState = this.weapon.update(deltaSeconds, this.elapsedSeconds, playerState, {
      wantsToFire: playerAlive && this.input.isFireHeld(),
    });

    if (weaponState.firedThisFrame) {
      const shot = this.shotResolver.resolve(this.camera, this.activeWeapon);
      this.gunfire.play();
      this.player.applyRecoil(
        weaponState.cameraKickVertical,
        weaponState.cameraKickHorizontal,
      );

      if (shot.kind === 'enemy') {
        const shotResult = this.enemies.applyShotHit(shot.hit, this.activeWeapon);

        if (shotResult.killed) {
          this.killCount += 1;
        }
      } else if (shot.kind === 'world') {
        this.bulletImpacts.spawnImpact(shot.hit, this.activeWeapon);
      }
    }

    if (playerState.jumpedThisFrame) {
      this.jumpAudio.play();
    }

    if (playerState.footstepTriggered) {
      this.footsteps.playNext(playerState.isSprinting);
    }

    if (enemyFrame.damageToPlayer > 0 && playerAlive) {
      this.playerHealth = Math.max(0, this.playerHealth - enemyFrame.damageToPlayer);
      this.damageFlash = 1;
    }

    this.damageFlash = Math.max(0, this.damageFlash - deltaSeconds * 2.8);
    this.bulletImpacts.update(deltaSeconds);
    this.hud.updateCombatState({
      health: this.playerHealth,
      aliveEnemies: enemyFrame.aliveEnemyCount,
      kills: this.killCount,
      damageFlash: this.damageFlash,
      playerDead: this.playerHealth === 0,
    });

    this.renderScene();
    this.animationFrameId = window.requestAnimationFrame(this.animate);
  };

  constructor(
    root: HTMLElement,
    config: GameSelectionConfig,
    callbacks: GameAppCallbacks = {},
  ) {
    this.callbacks = callbacks;
    this.activeLevel = getLevelDefinition(config.levelId);
    const weaponIds = Array.from(new Set([config.activeWeaponId, ...config.equippedWeaponIds]));
    this.weaponLoadout = weaponIds.map((id) => getWeaponDefinition(id));

    const initialWeaponIndex = this.weaponLoadout.findIndex(
      (weapon) => weapon.id === config.activeWeaponId,
    );
    this.currentWeaponIndex = initialWeaponIndex >= 0 ? initialWeaponIndex : 0;
    this.activeWeapon = this.weaponLoadout[this.currentWeaponIndex] ?? this.weaponLoadout[0]!;
    this.gunfire = new GunfireAudio(this.activeWeapon.audio);

    root.replaceChildren();

    this.shell.className = 'game-shell';
    this.viewport.className = 'game-viewport';
    this.shell.appendChild(this.viewport);
    root.appendChild(this.shell);

    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.15;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.viewport.appendChild(this.renderer.domElement);

    // 关卡工厂会把几何体建进 scene，并返回运行时要用的关键数据：
    // 碰撞体、玩家出生点、敌人出生点等。
    const world = this.activeLevel.createWorld(this.scene);

    this.input = new InputController(this.renderer.domElement);
    // HUD 的大部分展示文案已经改成从内容定义里注入，
    // 后续切换关卡或武器时，不需要再改 Hud 组件内部实现。
    this.hud = new Hud(
      this.shell,
      {
        topTag: this.activeLevel.topTag,
        modeTag: this.activeLevel.modeTag,
        weaponLabel: this.activeWeapon.label,
        weaponAmmoText: this.activeWeapon.ammoText,
        helpText: this.buildHelpText(this.activeWeapon),
      },
    );

    // 玩家控制器只关心“如何移动和看向哪里”，
    // 具体拿什么武器、场景叫什么名字，都由外层注入。
    this.player = new PlayerController(
      this.scene,
      this.camera,
      this.input,
      world.colliders,
      world.spawnPoint,
      world.spawnYaw,
      this.activeWeapon.tuning.recoilRecovery,
    );

    // 敌人管理器会根据关卡给出的出生点和启用列表创建敌人。
    this.enemies = new EnemyManager(
      this.scene,
      world.colliders,
      world.enemySpawns,
      config.enabledEnemyIds,
    );
    this.bulletImpacts = new BulletImpactSystem(this.scene);
    this.shotResolver = new ShotResolver(this.enemies, world.impactSurfaces);
    this.weapon = this.activeWeapon.createViewModel(this.camera);
    this.hud.updateCombatState({
      health: this.playerHealth,
      aliveEnemies: this.enemies.getAliveEnemyCount(),
      kills: this.killCount,
      damageFlash: 0,
      playerDead: false,
    });

    this.input.onPointerLockChange = (locked): void => {
      if (!locked && this.isRunning) {
        this.pause();
        this.callbacks.onPauseRequested?.();
      }
    };

    this.renderer.domElement.addEventListener('click', (): void => {
      if (!this.input.isPointerLocked) {
        this.input.requestPointerLock();
      }
    });

    window.addEventListener('resize', this.handleResize);
  }

  public async start(): Promise<void> {
    if (this.startPromise) {
      return this.startPromise;
    }

    this.startPromise = this.startRuntime().catch((error) => {
      this.startPromise = null;
      throw error;
    });

    return this.startPromise;
  }

  public dispose(): void {
    // 这里做运行时资源释放，避免重复创建 GameApp 时残留事件或帧循环。
    this.isRunning = false;
    window.cancelAnimationFrame(this.animationFrameId);
    window.removeEventListener('resize', this.handleResize);
    this.weapon.dispose?.();
    this.bulletImpacts.dispose();
    this.input.dispose();
    this.renderer.dispose();
  }

  private async startRuntime(): Promise<void> {
    // 统一从这里完成异步初始化，方便后续扩展加载界面 / 重开逻辑。
    await this.enemies.initialize();
    this.hud.updateCombatState({
      health: this.playerHealth,
      aliveEnemies: this.enemies.getAliveEnemyCount(),
      kills: this.killCount,
      damageFlash: 0,
      playerDead: false,
    });
    this.isInitialized = true;
    this.renderScene();
  }

  public resume(): void {
    if (!this.isInitialized || this.isRunning) {
      return;
    }

    this.input.consumePausePressed();
    this.clock.start();
    this.isRunning = true;
    this.animationFrameId = window.requestAnimationFrame(this.animate);
  }

  public pause(): void {
    if (!this.isInitialized) {
      return;
    }

    this.isRunning = false;
    window.cancelAnimationFrame(this.animationFrameId);
    this.animationFrameId = 0;
    this.clock.stop();

    if (this.input.isPointerLocked) {
      void document.exitPointerLock();
    }

    this.renderScene();
  }

  public requestPointerLock(): void {
    this.input.requestPointerLock();
  }

  public getLevelDefinition(): LevelDefinition {
    return this.activeLevel;
  }

  private renderScene(): void {
    this.renderer.render(this.scene, this.camera);
  }

  private cycleWeaponForward(): void {
    if (this.weaponLoadout.length <= 1) {
      return;
    }

    const nextIndex = (this.currentWeaponIndex + 1) % this.weaponLoadout.length;
    this.applyWeaponSelection(nextIndex);
  }

  private applyWeaponSelection(index: number): void {
    const nextWeapon = this.weaponLoadout[index];

    if (!nextWeapon || nextWeapon.id === this.activeWeapon.id) {
      return;
    }

    this.weapon.dispose?.();
    this.currentWeaponIndex = index;
    this.activeWeapon = nextWeapon;
    this.weapon = this.activeWeapon.createViewModel(this.camera);
    this.gunfire = new GunfireAudio(this.activeWeapon.audio);
    this.player.setRecoilRecovery(this.activeWeapon.tuning.recoilRecovery);
    this.hud.updateWeaponPresentation({
      weaponLabel: this.activeWeapon.label,
      weaponAmmoText: this.activeWeapon.ammoText,
      helpText: this.buildHelpText(this.activeWeapon),
    });
  }

  private buildHelpText(weapon: WeaponDefinition): string {
    return `WASD 移动 · Shift 冲刺 · Space 跳跃 · 数字键1切枪 · ${weapon.helpText} · 靠近敌人会追击并挥砍`;
  }
}
