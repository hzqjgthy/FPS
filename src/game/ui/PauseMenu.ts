import type { GameHelpSection } from '../content/ui/gameHelpContent';

export type PauseMenuView = 'main' | 'level-select' | 'help';

export interface PauseMenuLevelOption {
  id: string;
  label: string;
}

export interface PauseMenuLevelPresentation {
  label: string;
  kicker: string;
  title: string;
  description: string;
  legend: string;
  tip: string;
}

export interface PauseMenuState {
  mode: 'boot' | 'paused';
  view: PauseMenuView;
  currentLevelId: string;
  currentLevel: PauseMenuLevelPresentation;
  levels: PauseMenuLevelOption[];
  helpSections: readonly GameHelpSection[];
  busy: boolean;
}

export class PauseMenu {
  private readonly layer = document.createElement('div');
  private readonly panel = document.createElement('section');
  private readonly kicker = document.createElement('p');
  private readonly title = document.createElement('h1');
  private readonly description = document.createElement('h2');
  private readonly currentLevelLabel = document.createElement('div');
  private readonly controls = document.createElement('div');
  private readonly mainActions = document.createElement('div');
  private readonly subviewActions = document.createElement('div');
  private readonly continueButton = document.createElement('button');
  private readonly restartButton = document.createElement('button');
  private readonly selectLevelButton = document.createElement('button');
  private readonly helpButton = document.createElement('button');
  private readonly backButton = document.createElement('button');
  private readonly legend = document.createElement('div');
  private readonly tip = document.createElement('div');
  private readonly levelList = document.createElement('div');
  private readonly helpPanel = document.createElement('div');

  constructor(
    parent: HTMLElement,
    handlers: {
      onResume: () => void;
      onRestart: () => void;
      onOpenLevelSelect: () => void;
      onOpenHelp: () => void;
      onBackToMain: () => void;
      onSelectLevel: (levelId: string) => void;
    },
  ) {
    this.layer.className = 'pause-menu-layer';
    this.panel.className = 'pause-menu';
    this.currentLevelLabel.className = 'pause-menu__current';
    this.controls.className = 'pause-menu__controls';
    this.legend.className = 'pause-menu__legend';
    this.tip.className = 'pause-menu__tip';
    this.levelList.className = 'pause-menu__levels';
    this.helpPanel.className = 'pause-menu__help';

    this.continueButton.type = 'button';
    this.continueButton.className = 'intro-button';
    this.continueButton.addEventListener('click', handlers.onResume);

    this.restartButton.type = 'button';
    this.restartButton.className = 'pause-menu__button pause-menu__button--secondary';
    this.restartButton.textContent = '重启本关卡';
    this.restartButton.addEventListener('click', handlers.onRestart);

    this.selectLevelButton.type = 'button';
    this.selectLevelButton.className = 'pause-menu__button pause-menu__button--secondary';
    this.selectLevelButton.textContent = '选择关卡';
    this.selectLevelButton.addEventListener('click', handlers.onOpenLevelSelect);

    this.helpButton.type = 'button';
    this.helpButton.className = 'pause-menu__button pause-menu__button--secondary';
    this.helpButton.textContent = '游戏帮助';
    this.helpButton.addEventListener('click', handlers.onOpenHelp);

    this.backButton.type = 'button';
    this.backButton.className = 'pause-menu__button pause-menu__button--secondary';
    this.backButton.textContent = '返回菜单';
    this.backButton.addEventListener('click', handlers.onBackToMain);

    this.mainActions.className = 'pause-menu__actions';
    this.mainActions.append(
      this.continueButton,
      this.restartButton,
      this.selectLevelButton,
      this.helpButton,
    );

    this.subviewActions.className = 'pause-menu__actions pause-menu__actions--subview';
    this.subviewActions.append(this.backButton);

    this.controls.innerHTML = `
      <div class="intro-controls" aria-hidden="true">
        <div class="intro-controls__keys">
          <span class="intro-key intro-key--w">W</span>
          <span class="intro-key intro-key--a">A</span>
          <span class="intro-key intro-key--s">S</span>
          <span class="intro-key intro-key--d">D</span>
        </div>
        <div class="intro-controls__space">
          <span class="intro-key intro-key--space">Space</span>
        </div>
      </div>
    `;

    this.panel.append(
      this.kicker,
      this.title,
      this.description,
      this.currentLevelLabel,
      this.controls,
      this.legend,
      this.mainActions,
      this.subviewActions,
      this.levelList,
      this.helpPanel,
      this.tip,
    );

    this.layer.appendChild(this.panel);
    parent.appendChild(this.layer);

    this.levelList.addEventListener('click', (event) => {
      const target = event.target as HTMLElement | null;
      const levelId = target?.dataset.levelId;

      if (!levelId) {
        return;
      }

      handlers.onSelectLevel(levelId);
    });
  }

  public update(state: PauseMenuState): void {
    const isMainView = state.view === 'main';
    const isLevelSelectView = state.view === 'level-select';
    const isHelpView = state.view === 'help';

    this.layer.dataset.visible = 'true';
    this.layer.dataset.mode = state.mode;
    this.layer.dataset.view = state.view;

    this.applyHeader(state, isHelpView, isLevelSelectView);
    this.currentLevelLabel.style.display = isHelpView ? 'none' : 'block';
    this.controls.style.display = isMainView ? 'block' : 'none';
    this.legend.style.display = isMainView ? 'block' : 'none';
    this.mainActions.style.display = isMainView ? 'flex' : 'none';
    this.subviewActions.style.display = isMainView ? 'none' : 'flex';
    this.levelList.style.display = isLevelSelectView ? 'grid' : 'none';
    this.helpPanel.style.display = isHelpView ? 'grid' : 'none';

    this.continueButton.textContent =
      state.mode === 'boot' ? '进入战场' : '继续游戏';
    this.continueButton.disabled = state.busy;
    this.restartButton.disabled = state.busy;
    this.selectLevelButton.disabled = state.busy;
    this.helpButton.disabled = state.busy;
    this.backButton.disabled = state.busy;

    this.renderLevelList(state.levels, state.currentLevelId);
    this.renderHelpSections(state.helpSections);
  }

  public hide(): void {
    this.layer.dataset.visible = 'false';
  }

  private applyHeader(
    state: PauseMenuState,
    isHelpView: boolean,
    isLevelSelectView: boolean,
  ): void {
    if (isHelpView) {
      this.kicker.textContent = 'Combat Reference';
      this.title.textContent = '游戏帮助';
      this.description.textContent =
        '查看当前版本的基础移动、战斗和系统键位，熟悉后可返回菜单继续游戏。';
      this.currentLevelLabel.textContent = '';
      this.legend.textContent = '';
      this.tip.textContent = '返回菜单后可继续游戏、重启本关卡，或切换到其它关卡。';
      return;
    }

    if (isLevelSelectView) {
      this.kicker.textContent = 'Select Mission';
      this.title.textContent = '选择关卡';
      this.description.textContent =
        '从已注册关卡中选择一张地图，系统会重新创建当前这一局并进入新关卡。';
      this.currentLevelLabel.textContent = `当前关卡：${state.currentLevel.label}`;
      this.legend.textContent = '';
      this.tip.textContent = `当前共可选择 ${state.levels.length} 张关卡。`;
      return;
    }

    this.kicker.textContent = state.currentLevel.kicker;
    this.title.textContent = state.currentLevel.title;
    this.description.textContent = state.currentLevel.description;
    this.currentLevelLabel.textContent = `当前关卡：${state.currentLevel.label}`;
    this.legend.textContent = state.currentLevel.legend;
    this.tip.textContent = state.currentLevel.tip;
  }

  private renderLevelList(levels: PauseMenuLevelOption[], currentLevelId: string): void {
    this.levelList.replaceChildren(
      ...levels.map((level) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'pause-menu__level-button';
        button.dataset.levelId = level.id;
        button.textContent = level.label;
        button.disabled = level.id === currentLevelId;
        return button;
      }),
    );
  }

  private renderHelpSections(helpSections: readonly GameHelpSection[]): void {
    this.helpPanel.replaceChildren(
      ...helpSections.map((section) => {
        const sectionCard = document.createElement('section');
        sectionCard.className = 'pause-menu__help-section';

        const sectionTitle = document.createElement('h3');
        sectionTitle.className = 'pause-menu__help-title';
        sectionTitle.textContent = section.title;
        sectionCard.appendChild(sectionTitle);

        const sectionList = document.createElement('div');
        sectionList.className = 'pause-menu__help-list';

        section.items.forEach((item) => {
          const itemCard = document.createElement('article');
          itemCard.className = 'pause-menu__help-item';

          const itemHeader = document.createElement('div');
          itemHeader.className = 'pause-menu__help-item-header';

          const label = document.createElement('strong');
          label.className = 'pause-menu__help-label';
          label.textContent = item.label;

          const keys = document.createElement('div');
          keys.className = 'pause-menu__help-keys';
          keys.append(
            ...item.keys.map((key) => {
              const keyBadge = document.createElement('span');
              keyBadge.className = 'pause-menu__key';
              keyBadge.textContent = key;
              return keyBadge;
            }),
          );

          itemHeader.append(label, keys);

          const description = document.createElement('p');
          description.className = 'pause-menu__help-description';
          description.textContent = item.description;

          itemCard.append(itemHeader, description);
          sectionList.appendChild(itemCard);
        });

        sectionCard.appendChild(sectionList);
        return sectionCard;
      }),
    );
  }
}
