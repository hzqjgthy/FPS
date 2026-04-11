import { GameApp } from './GameApp';
import {
  createDefaultGameSelection,
  type GameSelectionConfig,
} from './content/gameSelection';
import { GAME_HELP_SECTIONS } from './content/ui/gameHelpContent';
import {
  getLevelDefinition,
  listLevelDefinitions,
} from './content/levels/levelCatalog';
import { PauseMenu, type PauseMenuView } from './ui/PauseMenu';

export class GameDirector {
  private readonly root: HTMLElement;
  private readonly appHost = document.createElement('div');
  private readonly overlayHost = document.createElement('div');
  private readonly pauseMenu: PauseMenu;
  private activeGame: GameApp | null = null;
  private currentConfig: GameSelectionConfig = createDefaultGameSelection();
  private hasEnteredBattle = false;
  private pauseMenuView: PauseMenuView = 'main';
  private busy = false;

  constructor(root: HTMLElement) {
    this.root = root;
    this.root.replaceChildren();
    this.root.classList.add('game-root');
    this.appHost.className = 'game-app-host';
    this.overlayHost.className = 'game-overlay-host';
    this.root.append(this.appHost, this.overlayHost);

    this.pauseMenu = new PauseMenu(this.overlayHost, {
      onResume: () => {
        void this.resumeActiveGame();
      },
      onRestart: () => {
        void this.restartCurrentLevel();
      },
      onOpenLevelSelect: () => {
        this.openLevelSelector();
      },
      onOpenHelp: () => {
        this.openHelpView();
      },
      onBackToMain: () => {
        this.returnToMainMenu();
      },
      onSelectLevel: (levelId) => {
        void this.switchLevel(levelId);
      },
    });
  }

  public async start(): Promise<void> {
    await this.loadGame(createDefaultGameSelection());
    this.renderPauseMenu();
  }

  private async resumeActiveGame(): Promise<void> {
    if (!this.activeGame || this.busy) {
      return;
    }

    this.pauseMenu.hide();
    this.hasEnteredBattle = true;
    this.pauseMenuView = 'main';
    this.activeGame.requestPointerLock();
    this.activeGame.resume();
  }

  private async restartCurrentLevel(): Promise<void> {
    if (this.busy) {
      return;
    }

    await this.loadGame({
      ...this.currentConfig,
      equippedWeaponIds: [...this.currentConfig.equippedWeaponIds],
      enabledEnemyIds: [...this.currentConfig.enabledEnemyIds],
    });
    this.renderPauseMenu();
  }

  private async switchLevel(levelId: string): Promise<void> {
    if (this.busy || levelId === this.currentConfig.levelId) {
      return;
    }

    await this.loadGame({
      ...this.currentConfig,
      levelId,
      equippedWeaponIds: [...this.currentConfig.equippedWeaponIds],
      enabledEnemyIds: [...this.currentConfig.enabledEnemyIds],
    });
    this.renderPauseMenu();
  }

  private async loadGame(config: GameSelectionConfig): Promise<void> {
    this.busy = true;
    this.pauseMenuView = 'main';
    this.renderPauseMenu();

    this.activeGame?.dispose();
    this.activeGame = new GameApp(this.appHost, config, {
      onPauseRequested: () => {
        this.openPauseMenu();
      },
    });

    await this.activeGame.start();
    this.currentConfig = config;
    this.busy = false;
  }

  private openPauseMenu(): void {
    this.pauseMenuView = 'main';
    this.renderPauseMenu();
  }

  private openLevelSelector(): void {
    if (this.busy) {
      return;
    }

    this.pauseMenuView = 'level-select';
    this.renderPauseMenu();
  }

  private openHelpView(): void {
    if (this.busy) {
      return;
    }

    this.pauseMenuView = 'help';
    this.renderPauseMenu();
  }

  private returnToMainMenu(): void {
    if (this.busy) {
      return;
    }

    this.pauseMenuView = 'main';
    this.renderPauseMenu();
  }

  private renderPauseMenu(): void {
    const level = getLevelDefinition(this.currentConfig.levelId);

    this.pauseMenu.update({
      mode: this.hasEnteredBattle ? 'paused' : 'boot',
      view: this.pauseMenuView,
      currentLevelId: level.id,
      currentLevel: {
        label: level.label,
        kicker: level.introKicker,
        title: level.introTitle,
        description: level.introDescription,
        legend: level.introLegend,
        tip: level.introTip,
      },
      levels: listLevelDefinitions().map((entry) => ({
        id: entry.id,
        label: entry.label,
      })),
      helpSections: GAME_HELP_SECTIONS,
      busy: this.busy,
    });
  }
}
