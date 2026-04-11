import { SYSTEM_TUNING } from '../config/systemTuning';

const JUMP_SOURCE = new URL('../../../素材/角色/跳跃01.mp3', import.meta.url).href;

export class JumpAudio {
  private readonly players = Array.from(
    { length: SYSTEM_TUNING.audio.jumpPoolSize },
    () => {
      const audio = new Audio(JUMP_SOURCE);
      audio.preload = 'auto';
      audio.volume = SYSTEM_TUNING.audio.jumpVolume;
      return audio;
    },
  );

  private currentIndex = 0;

  public play(): void {
    const player = this.players[this.currentIndex];

    if (!player) {
      return;
    }

    player.pause();
    player.currentTime = 0;
    player.volume = SYSTEM_TUNING.audio.jumpVolume;

    void player.play().catch(() => {
      // Browsers may temporarily block playback until the page has received user interaction.
    });

    this.currentIndex = (this.currentIndex + 1) % this.players.length;
  }
}
