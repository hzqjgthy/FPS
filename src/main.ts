import './style.css';
import { GameDirector } from './game/GameDirector';

// 应用入口只做两件事：
// 1. 找到挂载节点
// 2. 创建并启动整个游戏
const appRoot = document.querySelector<HTMLDivElement>('#app');

if (!appRoot) {
  throw new Error('Game root element #app was not found.');
}

const director = new GameDirector(appRoot);
void director.start().catch((error) => {
  console.error('Failed to start game.', error);
});
