import * as THREE from 'three';

export class EnemyHealthBar {
  public readonly root = new THREE.Group();

  private readonly canvas = document.createElement('canvas');
  private readonly context: CanvasRenderingContext2D;
  private readonly texture: THREE.CanvasTexture;
  private readonly sprite: THREE.Sprite;
  private readonly yOffset: number;

  constructor(
    yOffset: number,
    width = 1.12,
    height = 0.22,
  ) {
    this.yOffset = yOffset;
    this.canvas.width = 256;
    this.canvas.height = 48;

    const context = this.canvas.getContext('2d');

    if (!context) {
      throw new Error('Unable to create enemy health bar canvas context.');
    }

    this.context = context;
    this.texture = new THREE.CanvasTexture(this.canvas);
    this.texture.anisotropy = 4;
    this.sprite = new THREE.Sprite(
      new THREE.SpriteMaterial({
        map: this.texture,
        transparent: true,
        opacity: 0.96,
        depthWrite: false,
      }),
    );

    this.sprite.scale.set(width, height, 1);
    this.root.add(this.sprite);
    this.root.position.y = this.yOffset;

    this.update(1, 0, false);
  }

  public update(healthRatio: number, elapsedSeconds: number, isDead: boolean): void {
    this.root.visible = !isDead;
    this.root.position.y = this.yOffset + Math.abs(Math.sin(elapsedSeconds * 4)) * 0.04;

    const context = this.context;
    const width = this.canvas.width;
    const height = this.canvas.height;
    const padding = 6;
    const barWidth = width - padding * 2;
    const barHeight = height - padding * 2;
    const clampedHealth = THREE.MathUtils.clamp(healthRatio, 0, 1);
    const fillWidth = Math.round(barWidth * clampedHealth);

    context.clearRect(0, 0, width, height);
    context.fillStyle = 'rgba(0, 0, 0, 0)';
    context.fillRect(0, 0, width, height);

    context.fillStyle = '#241010';
    context.fillRect(padding, padding, barWidth, barHeight);

    if (fillWidth > 0) {
      const red = Math.round(238 - clampedHealth * 120);
      const green = Math.round(102 + clampedHealth * 122);
      context.fillStyle = `rgb(${red}, ${green}, 74)`;
      context.fillRect(padding, padding, fillWidth, barHeight);
    }

    context.strokeStyle = 'rgba(255, 243, 223, 0.58)';
    context.lineWidth = 2;
    context.strokeRect(padding, padding, barWidth, barHeight);

    this.texture.needsUpdate = true;
  }
}
