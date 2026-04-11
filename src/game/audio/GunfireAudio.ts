import type { WeaponAudioDefinition } from '../weapons/WeaponTypes';

export class GunfireAudio {
  private readonly players: HTMLAudioElement[];
  private readonly definition: WeaponAudioDefinition;

  constructor(definition: WeaponAudioDefinition) {
    this.definition = definition;
    this.players = Array.from({ length: definition.shotPoolSize }, () => {
      const audio = new Audio(definition.shotSource);
      audio.preload = 'auto';
      audio.volume = definition.shotVolume;
      return audio;
    });
  }

  private currentIndex = 0;

  public play(): void {
    const player = this.players[this.currentIndex];

    if (!player) {
      return;
    }

    player.pause();
    player.currentTime = 0;
    player.volume = this.definition.shotVolume;

    void player.play().catch(() => {
      // Browsers may temporarily block playback until the page has received user interaction.
    });

    this.currentIndex = (this.currentIndex + 1) % this.players.length;
  }
}
