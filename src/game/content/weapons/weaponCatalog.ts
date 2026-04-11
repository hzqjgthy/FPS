import * as THREE from 'three';

import { AK47ViewModel } from '../../weapons/models/AK47ViewModel';
import { RedDragonSniperViewModel } from '../../weapons/models/RedDragonSniperViewModel';
import { ScarHViewModel } from '../../weapons/models/ScarHViewModel';
import type {
  WeaponAudioDefinition,
  WeaponDefinition,
  WeaponImpactDefinition,
  WeaponPresentationDefinition,
  WeaponTuning,
} from '../../weapons/WeaponTypes';

type WeaponTuningDefaults = Omit<WeaponTuning, 'bodyDamage' | 'headshotDamage'>;
type WeaponTuningInput = Pick<
  WeaponTuning,
  'bodyDamage' | 'headshotDamage'
> & Partial<WeaponTuningDefaults>;
type WeaponAudioInput = Pick<WeaponAudioDefinition, 'shotSource'>
  & Partial<Omit<WeaponAudioDefinition, 'shotSource'>>;
type WeaponImpactInput = WeaponImpactDefinition;
type WeaponPresentationInput = Partial<WeaponPresentationDefinition>;

// 内部默认值。
// 作用是减少重复录入，但最终导出的每把枪仍然会被展开成完整配置对象。
const WEAPON_TUNING_DEFAULTS: WeaponTuningDefaults = {
  fireInterval: 0.1, // 默认射速间隔，单位秒。
  hitRange: 1000, // 默认最大有效射击距离。
  bobSpeed: 10, // 默认武器行走摆动速度。
  bobAmount: 0.045, // 默认武器行走摆动幅度。
  muzzleFlashDuration: 0.045, // 默认枪口闪光持续时间。
  recoilKickBack: 0.12, // 默认武器后坐距离。
  recoilRotationX: 0.085, // 默认武器竖直后坐角度。
  recoilRotationZ: 0.03, // 默认武器横向扭动角度。
  recoilRecovery: 14, // 默认后坐恢复速度。
  cameraKickVertical: 0.028, // 默认镜头竖直后坐量。
  cameraKickHorizontal: 0.01, // 默认镜头水平后坐量。
};

const WEAPON_AUDIO_DEFAULTS: Omit<WeaponAudioDefinition, 'shotSource'> = {
  shotVolume: 0.42, // 默认枪声音量。
  shotPoolSize: 4, // 默认枪声音频池大小。
};

const WEAPON_IMPACT_DEFAULTS: Omit<WeaponImpactDefinition, 'markStyleId'> = {
  markSize: 1.15, // 默认子弹印记大小。
  markOpacity: 0.88, // 默认子弹印记初始透明度。
  lifetimeSeconds: 6, // 默认子弹印记总存在时间。
  fadeDurationSeconds: 2.2, // 默认子弹印记淡出时长。
};

const WEAPON_PRESENTATION_DEFAULTS: WeaponPresentationDefinition = {
  viewModelScale: 1, // 默认第一人称武器模型缩放倍率。
};

// 展开并校验一把枪的完整手感配置。
function defineWeaponTuning(input: WeaponTuningInput): WeaponTuning {
  const tuning: WeaponTuning = {
    ...WEAPON_TUNING_DEFAULTS,
    ...input,
  };

  if (tuning.fireInterval <= 0) {
    throw new Error('Weapon fireInterval must be greater than 0.');
  }

  if (tuning.bodyDamage <= 0 || tuning.headshotDamage <= 0) {
    throw new Error('Weapon damage values must be greater than 0.');
  }

  if (tuning.hitRange <= 0) {
    throw new Error('Weapon hitRange must be greater than 0.');
  }

  if (tuning.recoilRecovery <= 0) {
    throw new Error('Weapon recoilRecovery must be greater than 0.');
  }

  return tuning;
}

// 展开并校验一把枪的完整音效配置。
function defineWeaponAudio(input: WeaponAudioInput): WeaponAudioDefinition {
  const audio: WeaponAudioDefinition = {
    ...WEAPON_AUDIO_DEFAULTS,
    ...input,
  };

  if (!audio.shotSource) {
    throw new Error('Weapon shotSource is required.');
  }

  if (audio.shotPoolSize < 1) {
    throw new Error('Weapon shotPoolSize must be at least 1.');
  }

  if (audio.shotVolume < 0) {
    throw new Error('Weapon shotVolume cannot be negative.');
  }

  return audio;
}

// 展开并校验一把枪的完整子弹印记配置。
function defineWeaponImpact(input: WeaponImpactInput): WeaponImpactDefinition {
  const impact: WeaponImpactDefinition = {
    ...WEAPON_IMPACT_DEFAULTS,
    ...input,
  };

  if (!impact.markStyleId) {
    throw new Error('Weapon impact markStyleId is required.');
  }

  if (impact.markSize <= 0) {
    throw new Error('Weapon impact markSize must be greater than 0.');
  }

  if (impact.lifetimeSeconds <= 0 || impact.fadeDurationSeconds <= 0) {
    throw new Error('Weapon impact timing values must be greater than 0.');
  }

  if (impact.fadeDurationSeconds > impact.lifetimeSeconds) {
    throw new Error('Weapon impact fadeDurationSeconds cannot exceed lifetimeSeconds.');
  }

  return impact;
}

// 展开并校验一把枪的展示配置。
function defineWeaponPresentation(
  input: WeaponPresentationInput = {},
): WeaponPresentationDefinition {
  const presentation: WeaponPresentationDefinition = {
    ...WEAPON_PRESENTATION_DEFAULTS,
    ...input,
  };

  if (presentation.viewModelScale <= 0) {
    throw new Error('Weapon presentation viewModelScale must be greater than 0.');
  }

  return presentation;
}

// 统一校验武器定义入口，避免注册进来的武器缺少关键字段。
function defineWeaponDefinition(input: WeaponDefinition): WeaponDefinition {
  if (!input.id || !input.label) {
    throw new Error('Weapon id and label are required.');
  }

  return input;
}

// 单把武器的数值调优集中放在这里，方便以后复制一份做新枪。
const ak47Tuning = defineWeaponTuning({
  bobSpeed: 10, // 武器走路摆动速度，值越大摆动节奏越快。
  bobAmount: 0.045, // 武器走路摆动幅度，值越大枪体晃动越明显。
  fireInterval: 0.1, // 两次开火之间的最短间隔，单位秒。
  bodyDamage: 50, // 命中身体时造成的伤害。
  headshotDamage: 100, // 命中头部时造成的伤害。
  hitRange: 1000, // 射线判定的最大有效距离。
  muzzleFlashDuration: 0.045, // 枪口闪光持续时间，单位秒。
  recoilKickBack: 0.12, // 开火时武器向后坐的距离。
  recoilRotationX: 0.085, // 开火时武器在 X 轴上的上扬角度。
  recoilRotationZ: 0.03, // 开火时武器在 Z 轴上的侧倾角度。
  recoilRecovery: 14, // 后坐力恢复速度，值越大回正越快。
  cameraKickVertical: 0.028, // 开火时施加给镜头的垂直抬升量。
  cameraKickHorizontal: 0.01, // 开火时施加给镜头的水平偏移量。
});

const ak47Audio = defineWeaponAudio({
  // 射击音效文件路径。
  shotSource: new URL(
    '../../../../素材/武器/枪/枪01/枪的音效/枪声.mp3',
    import.meta.url,
  ).href,
  shotVolume: 0.42, // 枪声音量。
  shotPoolSize: 4, // 枪声音频池大小，连点时更不容易被截断。
});

const ak47Impact = defineWeaponImpact({
  markStyleId: 'weapon_001_ak47_classic', // AK-47 使用的印记风格 ID。
  markSize: 1.05, // AK-47 子弹印记大小。
  markOpacity: 0.88, // AK-47 子弹印记初始透明度。
  lifetimeSeconds: 5.8, // AK-47 子弹印记总存在时间。
  fadeDurationSeconds: 2.1, // AK-47 子弹印记淡出时长。
});

const ak47Presentation = defineWeaponPresentation({
  viewModelScale: 1, // AK-47 第一人称模型缩放倍率。
});

const scarHTuning = defineWeaponTuning({
  bobSpeed: 8.9, // 武器走路摆动速度，值越大摆动节奏越快。
  bobAmount: 0.04, // 武器走路摆动幅度，值越大枪体晃动越明显。
  fireInterval: 0.02, // 两次开火之间的最短间隔，单位秒。
  bodyDamage: 10, // 命中身体时造成的伤害。
  headshotDamage: 20, // 命中头部时造成的伤害。
  hitRange: 1100, // 射线判定的最大有效距离。
  muzzleFlashDuration: 0.05, // 枪口闪光持续时间，单位秒。
  recoilKickBack: 0.18, // 开火时武器向后坐的距离。
  recoilRotationX: 0.12, // 开火时武器在 X 轴上的上扬角度。
  recoilRotationZ: 0.04, // 开火时武器在 Z 轴上的侧倾角度。
  recoilRecovery: 10.5, // 后坐力恢复速度，值越大回正越快。
  cameraKickVertical: 0.04, // 开火时施加给镜头的垂直抬升量。
  cameraKickHorizontal: 0.016, // 开火时施加给镜头的水平偏移量。
});

const scarHAudio = defineWeaponAudio({
  // 射击音效文件路径。
  shotSource: new URL(
    '../../../../素材/武器/枪/枪02/枪的音效/枪声.mp3',
    import.meta.url,
  ).href,
  shotVolume: 0.46, // 枪声音量。
  shotPoolSize: 4, // 枪声音频池大小，连点时更不容易被截断。
});

const scarHImpact = defineWeaponImpact({
  markStyleId: 'weapon_002_scar_h_battle_rifle', // SCAR-H 使用的印记风格 ID。
  markSize: 1.32, // SCAR-H 子弹印记大小。
  markOpacity: 0.92, // SCAR-H 子弹印记初始透明度。
  lifetimeSeconds: 6.8, // SCAR-H 子弹印记总存在时间。
  fadeDurationSeconds: 2.8, // SCAR-H 子弹印记淡出时长。
});

const scarHPresentation = defineWeaponPresentation({
  viewModelScale: 0.94, // SCAR-H 第一人称模型缩放倍率。
});

const redDragonSniperTuning = defineWeaponTuning({
  bobSpeed: 6.4, // 武器走路摆动速度，值越大摆动节奏越快。
  bobAmount: 0.028, // 武器走路摆动幅度，值越大枪体晃动越明显。
  fireInterval: 0.82, // 两次开火之间的最短间隔，单位秒。
  bodyDamage: 4000, // 命中身体时造成的伤害。
  headshotDamage: 8000, // 命中头部时造成的伤害。
  hitRange: 1600, // 射线判定的最大有效距离。
  muzzleFlashDuration: 0.08, // 枪口闪光持续时间，单位秒。
  recoilKickBack: 0.28, // 开火时武器向后坐的距离。
  recoilRotationX: 0.16, // 开火时武器在 X 轴上的上扬角度。
  recoilRotationZ: 0.05, // 开火时武器在 Z 轴上的侧倾角度。
  recoilRecovery: 8.4, // 后坐力恢复速度，值越大回正越快。
  cameraKickVertical: 0.075, // 开火时施加给镜头的垂直抬升量。
  cameraKickHorizontal: 0.012, // 开火时施加给镜头的水平偏移量。
});

const redDragonSniperAudio = defineWeaponAudio({
  // 射击音效文件路径。
  shotSource: new URL(
    '../../../../素材/武器/枪/枪03/枪的音效/枪声.mp3',
    import.meta.url,
  ).href,
  shotVolume: 0.56, // 枪声音量。
  shotPoolSize: 3, // 枪声音频池大小，狙击枪节奏较慢，不需要太大的池。
});

const redDragonSniperImpact = defineWeaponImpact({
  markStyleId: 'weapon_003_red_dragon_tech_sniper', // 红龙狙击枪使用的印记风格 ID。
  markSize: 1.46, // 红龙狙击枪子弹印记大小。
  markOpacity: 0.96, // 红龙狙击枪子弹印记初始透明度。
  lifetimeSeconds: 7.2, // 红龙狙击枪子弹印记总存在时间。
  fadeDurationSeconds: 3.2, // 红龙狙击枪子弹印记淡出时长。
});

const redDragonSniperPresentation = defineWeaponPresentation({
  viewModelScale: 2, // 红龙狙击枪第一人称模型缩放倍率，会乘到自动适配比例上。
});

// 武器注册表。
// 后续新增武器时：
// 1. 写新的 tuning
// 2. 注册新的 definition
// 3. 回到 gameSelection.ts 切换 ACTIVE_WEAPON_ID
export const WEAPON_CATALOG: Record<string, WeaponDefinition> = {
  weapon_001_ak47_classic: defineWeaponDefinition({
    id: 'weapon_001_ak47_classic', // 武器唯一 ID，供切枪、配置选择和系统查找使用。
    label: 'AK-47', // HUD 上显示的武器名称。
    ammoText: '30 / 90 • 7.62mm', // HUD 上显示的弹药说明文本。
    helpText: '左键开火', // HUD 上显示的操作提示文本。
    tuning: ak47Tuning, // 这把枪对应的手感和伤害配置。
    audio: ak47Audio, // 这把枪对应的音效配置。
    impact: ak47Impact, // 这把枪对应的子弹印记配置。
    presentation: ak47Presentation, // 这把枪对应的展示配置。
    // 创建这把枪的第一人称视图模型。
    createViewModel: (camera: THREE.PerspectiveCamera) =>
      new AK47ViewModel(camera, ak47Tuning, ak47Presentation.viewModelScale),
  }),
  weapon_002_scar_h_battle_rifle: defineWeaponDefinition({
    id: 'weapon_002_scar_h_battle_rifle', // 武器唯一 ID，供切枪、配置选择和系统查找使用。
    label: 'SCAR-H', // HUD 上显示的武器名称。
    ammoText: '20 / 60 • 7.62mm NATO', // HUD 上显示的弹药说明文本。
    helpText: '左键开火', // HUD 上显示的操作提示文本。
    tuning: scarHTuning, // 这把枪对应的手感和伤害配置。
    audio: scarHAudio, // 这把枪对应的音效配置。
    impact: scarHImpact, // 这把枪对应的子弹印记配置。
    presentation: scarHPresentation, // 这把枪对应的展示配置。
    // 创建这把枪的第一人称视图模型。
    createViewModel: (camera: THREE.PerspectiveCamera) =>
      new ScarHViewModel(camera, scarHTuning, scarHPresentation.viewModelScale),
  }),
  weapon_003_red_dragon_tech_sniper: defineWeaponDefinition({
    id: 'weapon_003_red_dragon_tech_sniper', // 武器唯一 ID，供切枪、配置选择和系统查找使用。
    label: 'Dragon Sniper', // HUD 上显示的武器名称。
    ammoText: '5 / 25 • 12.7mm', // HUD 上显示的弹药说明文本。
    helpText: '左键重型精确射击', // HUD 上显示的操作提示文本。
    tuning: redDragonSniperTuning, // 这把枪对应的手感和伤害配置。
    audio: redDragonSniperAudio, // 这把枪对应的音效配置。
    impact: redDragonSniperImpact, // 这把枪对应的子弹印记配置。
    presentation: redDragonSniperPresentation, // 这把枪对应的展示配置。
    // 创建这把枪的第一人称视图模型。
    createViewModel: (camera: THREE.PerspectiveCamera) =>
      new RedDragonSniperViewModel(
        camera,
        redDragonSniperTuning,
        redDragonSniperPresentation.viewModelScale,
      ),
  }),
};

export function getWeaponDefinition(id: string): WeaponDefinition {
  const weapon = WEAPON_CATALOG[id];

  if (!weapon) {
    throw new Error(`Weapon definition "${id}" was not found.`);
  }

  return weapon;
}
