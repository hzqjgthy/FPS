import type * as THREE from 'three';

import type { PlayerFrameState } from '../player/PlayerController';

// 这组类型是“武器系统的公共协议”：
// GameApp、武器视图模型、音频、敌人结算都通过这些接口对接。
export interface WeaponTuning {
  fireInterval: number;
  bodyDamage: number;
  headshotDamage: number;
  hitRange: number;
  bobSpeed: number;
  bobAmount: number;
  muzzleFlashDuration: number;
  recoilKickBack: number;
  recoilRotationX: number;
  recoilRotationZ: number;
  recoilRecovery: number;
  cameraKickVertical: number;
  cameraKickHorizontal: number;
}

export interface WeaponAudioDefinition {
  shotSource: string;
  shotVolume: number;
  shotPoolSize: number;
}

export interface WeaponImpactDefinition {
  markStyleId: string;
  markSize: number;
  markOpacity: number;
  lifetimeSeconds: number;
  fadeDurationSeconds: number;
}

export interface WeaponPresentationDefinition {
  viewModelScale: number;
}

export interface WeaponFrameInput {
  wantsToFire: boolean;
}

export interface WeaponFrameState {
  firedThisFrame: boolean;
  cameraKickVertical: number;
  cameraKickHorizontal: number;
}

export interface WeaponViewModel {
  // 每帧更新武器的表现层，并返回这一帧是否开火、要施加多少镜头后坐力。
  update(
    deltaSeconds: number,
    elapsedSeconds: number,
    playerState: PlayerFrameState,
    weaponInput: WeaponFrameInput,
  ): WeaponFrameState;
  dispose?(): void;
}

export interface WeaponDefinition {
  id: string;
  label: string;
  ammoText: string;
  helpText: string;
  tuning: WeaponTuning;
  audio: WeaponAudioDefinition;
  impact: WeaponImpactDefinition;
  presentation: WeaponPresentationDefinition;
  // 传入主摄像机是为了让第一人称武器跟随玩家视角。
  createViewModel(camera: THREE.PerspectiveCamera): WeaponViewModel;
}
