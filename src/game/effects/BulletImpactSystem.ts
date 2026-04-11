import * as THREE from 'three';

import { SYSTEM_TUNING } from '../config/systemTuning';
import type { WeaponDefinition, WeaponImpactDefinition } from '../weapons/WeaponTypes';
import type { WorldShotHitCandidate } from '../combat/ShotResolver';

interface ActiveBulletMark {
  mesh: THREE.Mesh;
  material: THREE.MeshBasicMaterial;
  age: number;
  impact: WeaponImpactDefinition;
}

const FORWARD = new THREE.Vector3(0, 0, 1);
const textureCache = new Map<string, THREE.CanvasTexture>();

export class BulletImpactSystem {
  private readonly root = new THREE.Group();
  private readonly markGeometry = new THREE.PlaneGeometry(1, 1);
  private readonly marks: ActiveBulletMark[] = [];
  private readonly tempQuaternion = new THREE.Quaternion();

  constructor(scene: THREE.Scene) {
    this.root.name = 'bullet-impact-marks';
    scene.add(this.root);
  }

  public update(deltaSeconds: number): void {
    for (let index = this.marks.length - 1; index >= 0; index -= 1) {
      const mark = this.marks[index];
      mark.age += deltaSeconds;

      if (mark.age >= mark.impact.lifetimeSeconds) {
        this.disposeMark(index);
        continue;
      }

      const fadeStart = mark.impact.lifetimeSeconds - mark.impact.fadeDurationSeconds;

      if (mark.age < fadeStart) {
        mark.material.opacity = mark.impact.markOpacity;
        continue;
      }

      const fadeProgress = (mark.age - fadeStart) / mark.impact.fadeDurationSeconds;
      mark.material.opacity = mark.impact.markOpacity * (1 - THREE.MathUtils.clamp(fadeProgress, 0, 1));
    }
  }

  public spawnImpact(hit: WorldShotHitCandidate, weapon: WeaponDefinition): void {
    while (this.marks.length >= SYSTEM_TUNING.effects.maxBulletMarks) {
      this.disposeMark(0);
    }

    const material = new THREE.MeshBasicMaterial({
      map: getImpactTexture(weapon.impact.markStyleId),
      transparent: true,
      opacity: weapon.impact.markOpacity,
      depthWrite: false,
      side: THREE.DoubleSide,
      polygonOffset: true,
      polygonOffsetFactor: -4,
      polygonOffsetUnits: -4,
    });
    const mesh = new THREE.Mesh(this.markGeometry, material);
    mesh.scale.setScalar(weapon.impact.markSize);
    mesh.position.copy(hit.point).addScaledVector(
      hit.normal,
      SYSTEM_TUNING.effects.bulletMarkSurfaceOffset,
    );
    mesh.quaternion.setFromUnitVectors(FORWARD, hit.normal);
    this.tempQuaternion.setFromAxisAngle(hit.normal, Math.random() * Math.PI * 2);
    mesh.quaternion.multiply(this.tempQuaternion);
    mesh.renderOrder = 5;

    this.root.add(mesh);
    this.marks.push({
      mesh,
      material,
      age: 0,
      impact: weapon.impact,
    });
  }

  public dispose(): void {
    for (let index = this.marks.length - 1; index >= 0; index -= 1) {
      this.disposeMark(index);
    }

    this.markGeometry.dispose();
    this.root.removeFromParent();
  }

  private disposeMark(index: number): void {
    const mark = this.marks[index];

    if (!mark) {
      return;
    }

    mark.mesh.removeFromParent();
    mark.material.dispose();
    this.marks.splice(index, 1);
  }
}

function getImpactTexture(styleId: string): THREE.CanvasTexture {
  const cached = textureCache.get(styleId);

  if (cached) {
    return cached;
  }

  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 128;

  const context = canvas.getContext('2d');

  if (!context) {
    throw new Error('Unable to create bullet impact canvas context.');
  }

  context.clearRect(0, 0, canvas.width, canvas.height);

  const isHeavy = styleId === 'weapon_002_scar_h_battle_rifle';
  const isSniper = styleId === 'weapon_003_red_dragon_tech_sniper';
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  const coreRadius = isSniper ? 12 : isHeavy ? 15 : 11;
  const scatterCount = isSniper ? 10 : isHeavy ? 22 : 14;

  for (let index = 0; index < scatterCount; index += 1) {
    const angle = Math.random() * Math.PI * 2;
    const distance = (
      isSniper ? 30 : isHeavy ? 28 : 22
    ) + Math.random() * (isSniper ? 12 : isHeavy ? 18 : 10);
    const radius = 1.5 + Math.random() * (isSniper ? 1.8 : isHeavy ? 3.2 : 2.2);
    const x = centerX + Math.cos(angle) * distance;
    const y = centerY + Math.sin(angle) * distance;
    context.fillStyle = isSniper
      ? 'rgba(26, 18, 14, 0.48)'
      : isHeavy
        ? 'rgba(24, 16, 12, 0.62)'
        : 'rgba(18, 14, 11, 0.54)';
    context.beginPath();
    context.arc(x, y, radius, 0, Math.PI * 2);
    context.fill();
  }

  for (let index = 0; index < (isSniper ? 12 : isHeavy ? 9 : 6); index += 1) {
    const angle = Math.random() * Math.PI * 2;
    const length = (isSniper ? 38 : isHeavy ? 32 : 24) + Math.random() * 8;
    const x = centerX + Math.cos(angle) * length;
    const y = centerY + Math.sin(angle) * length;
    context.strokeStyle = isSniper
      ? 'rgba(40, 26, 18, 0.52)'
      : isHeavy
        ? 'rgba(34, 24, 18, 0.42)'
        : 'rgba(28, 22, 16, 0.34)';
    context.lineWidth = isSniper ? 1.6 : isHeavy ? 2 : 1.5;
    context.beginPath();
    context.moveTo(centerX, centerY);
    context.lineTo(x, y);
    context.stroke();
  }

  const glow = context.createRadialGradient(
    centerX,
    centerY,
    0,
    centerX,
    centerY,
    isSniper ? 34 : isHeavy ? 36 : 28,
  );
  glow.addColorStop(
    0,
    isSniper ? 'rgba(20, 18, 18, 0.96)' : isHeavy ? 'rgba(18, 18, 18, 0.92)' : 'rgba(22, 22, 22, 0.84)',
  );
  glow.addColorStop(
    0.42,
    isSniper ? 'rgba(34, 24, 18, 0.64)' : isHeavy ? 'rgba(30, 20, 14, 0.72)' : 'rgba(30, 22, 18, 0.58)',
  );
  glow.addColorStop(1, 'rgba(0, 0, 0, 0)');
  context.fillStyle = glow;
  context.beginPath();
  context.arc(centerX, centerY, isSniper ? 34 : isHeavy ? 38 : 30, 0, Math.PI * 2);
  context.fill();

  context.fillStyle = isSniper
    ? 'rgba(7, 6, 6, 0.98)'
    : isHeavy
      ? 'rgba(8, 7, 7, 0.96)'
      : 'rgba(12, 10, 9, 0.9)';
  context.beginPath();
  context.arc(centerX, centerY, coreRadius, 0, Math.PI * 2);
  context.fill();

  const texture = new THREE.CanvasTexture(canvas);
  texture.anisotropy = 4;
  texture.colorSpace = THREE.SRGBColorSpace;
  textureCache.set(styleId, texture);
  return texture;
}
