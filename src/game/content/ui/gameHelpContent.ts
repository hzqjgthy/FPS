export interface GameHelpItem {
  id: string;
  label: string;
  keys: readonly string[];
  description: string;
}

export interface GameHelpSection {
  id: string;
  title: string;
  items: readonly GameHelpItem[];
}

// 游戏帮助内容集中放在这里。
// 后续如果新增换弹、下蹲、开镜、投掷物等操作，
// 只需要在这里补一条内容，不用改 PauseMenu 的结构。
export const GAME_HELP_SECTIONS: readonly GameHelpSection[] = [
  {
    id: 'movement',
    title: '移动操作',
    items: [
      {
        id: 'move-forward',
        label: '前进',
        keys: ['W'],
        description: '向准星当前面朝的方向前进。',
      },
      {
        id: 'move-backward',
        label: '后退',
        keys: ['S'],
        description: '沿当前面朝方向后退。',
      },
      {
        id: 'move-left',
        label: '左移',
        keys: ['A'],
        description: '沿当前朝向的左侧横向移动。',
      },
      {
        id: 'move-right',
        label: '右移',
        keys: ['D'],
        description: '沿当前朝向的右侧横向移动。',
      },
      {
        id: 'sprint',
        label: '冲刺',
        keys: ['Shift'],
        description: '按住时进入冲刺状态，移动速度更快。',
      },
      {
        id: 'jump',
        label: '跳跃',
        keys: ['Space'],
        description: '立刻起跳，可越过较低障碍。',
      },
    ],
  },
  {
    id: 'combat',
    title: '战斗操作',
    items: [
      {
        id: 'look',
        label: '视角控制',
        keys: ['Mouse'],
        description: '移动鼠标观察四周并瞄准目标。',
      },
      {
        id: 'fire',
        label: '开火',
        keys: ['Mouse Left'],
        description: '按住或点击鼠标左键进行射击。',
      },
      {
        id: 'switch-weapon',
        label: '切枪',
        keys: ['1'],
        description: '在当前已装备武器之间循环切换。',
      },
    ],
  },
  {
    id: 'system',
    title: '系统操作',
    items: [
      {
        id: 'pause',
        label: '暂停',
        keys: ['Esc'],
        description: '打开暂停菜单，并释放鼠标锁定。',
      },
    ],
  },
] as const;
