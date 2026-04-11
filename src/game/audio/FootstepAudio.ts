import { SYSTEM_TUNING } from '../config/systemTuning';

const FOOTSTEP_SOURCE = new URL('../../../素材/角色/脚步声01.mp3', import.meta.url).href;

export class FootstepAudio {
  private readonly footstepPlayers = Array.from(
    { length: SYSTEM_TUNING.audio.footstepPoolSize },
    () => {
      const audio = new Audio(FOOTSTEP_SOURCE);
      audio.preload = 'auto';
      audio.volume = SYSTEM_TUNING.audio.footstepVolume;
      return audio;
    },
  );

  private currentIndex = 0;

  public playNext(isSprinting: boolean): void {
    const player = this.footstepPlayers[this.currentIndex];

    if (!player) {
      return;
    }

    player.pause();
    player.currentTime = 0;
    player.volume = SYSTEM_TUNING.audio.footstepVolume;
    player.playbackRate = isSprinting ? 1.08 : 1;

    void player.play().catch(() => {
      // Browsers may temporarily block playback until the page has received user interaction.
    });

    this.currentIndex = (this.currentIndex + 1) % this.footstepPlayers.length;
  }
}
