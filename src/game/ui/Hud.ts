export interface HudCombatState {
  health: number;
  aliveEnemies: number;
  kills: number;
  damageFlash: number;
  playerDead: boolean;
}

export interface HudPresentationConfig {
  topTag: string;
  modeTag: string;
  weaponLabel: string;
  weaponAmmoText: string;
  helpText: string;
}

/**
 * HUD 只负责 DOM 展示，不参与游戏规则计算。
 * 它接收外部传入的展示文案和战斗状态，再把这些数据渲染到界面上。
 */
export class Hud {
  private readonly layer = document.createElement('div');
  private readonly weaponLabelValue = document.createElement('strong');
  private readonly weaponAmmoValue = document.createElement('span');
  private readonly helpValue = document.createElement('div');
  private readonly healthValue = document.createElement('strong');
  private readonly enemyValue = document.createElement('strong');
  private readonly killValue = document.createElement('strong');
  private readonly damageOverlay = document.createElement('div');
  private readonly gameOverPanel = document.createElement('div');

  constructor(
    parent: HTMLElement,
    presentation: HudPresentationConfig,
  ) {
    // HUD 的主体结构在构造时一次性生成，
    // 后续每帧只更新少量数字和状态 class / data-attr。
    this.layer.className = 'hud-layer';
    this.layer.dataset.dead = 'false';

    this.layer.innerHTML = `
      <div class="hud-bar hud-bar--top">
        <div class="hud-group hud-group--left">
          <div class="hud-chip">${presentation.topTag}</div>
          <div class="hud-chip">${presentation.modeTag}</div>
        </div>
        <div class="hud-group hud-group--right">
          <div class="hud-chip hud-chip--metric">
            <span>Health</span>
          </div>
          <div class="hud-chip hud-chip--metric">
            <span>Enemies</span>
          </div>
          <div class="hud-chip hud-chip--metric">
            <span>Kills</span>
          </div>
        </div>
      </div>
      <div class="hud-crosshair" aria-hidden="true"></div>
      <div class="hud-bar hud-bar--bottom">
        <div class="hud-chip hud-weapon"></div>
        <div class="hud-chip hud-help"></div>
      </div>
    `;

    this.damageOverlay.className = 'hud-damage';
    this.gameOverPanel.className = 'hud-gameover';
    this.gameOverPanel.innerHTML = `
      <p>Player Down</p>
      <strong>你已倒下</strong>
      <span>刷新页面或继续观察战场。</span>
    `;

    const weaponChip = this.layer.querySelector<HTMLDivElement>('.hud-weapon');
    this.weaponLabelValue.textContent = presentation.weaponLabel;
    this.weaponAmmoValue.textContent = presentation.weaponAmmoText;
    weaponChip?.append(this.weaponLabelValue, this.weaponAmmoValue);

    const helpChip = this.layer.querySelector<HTMLDivElement>('.hud-help');
    this.helpValue.textContent = presentation.helpText;
    helpChip?.appendChild(this.helpValue);

    const metrics = this.layer.querySelectorAll<HTMLDivElement>('.hud-chip--metric');
    metrics[0]?.appendChild(this.healthValue);
    metrics[1]?.appendChild(this.enemyValue);
    metrics[2]?.appendChild(this.killValue);

    this.healthValue.textContent = '100';
    this.enemyValue.textContent = '0';
    this.killValue.textContent = '0';

    this.layer.appendChild(this.damageOverlay);
    this.layer.appendChild(this.gameOverPanel);
    parent.appendChild(this.layer);
  }

  public updateCombatState(state: HudCombatState): void {
    // 这里是 HUD 的高频更新入口。
    this.healthValue.textContent = `${state.health}`;
    this.enemyValue.textContent = `${state.aliveEnemies}`;
    this.killValue.textContent = `${state.kills}`;
    this.damageOverlay.style.opacity = `${THREEClamp(state.damageFlash, 0, 1)}`;
    this.layer.dataset.dead = String(state.playerDead);
  }

  public updateWeaponPresentation(
    presentation: Pick<HudPresentationConfig, 'weaponLabel' | 'weaponAmmoText' | 'helpText'>,
  ): void {
    this.weaponLabelValue.textContent = presentation.weaponLabel;
    this.weaponAmmoValue.textContent = presentation.weaponAmmoText;
    this.helpValue.textContent = presentation.helpText;
  }
}

function THREEClamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}
