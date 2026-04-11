export class InputController {
  public isPointerLocked = false;
  public onPointerLockChange?: (locked: boolean) => void;

  private readonly lockElement: HTMLElement;
  private readonly pressedKeys = new Set<string>();
  private isPrimaryFireHeld = false;
  private jumpRequested = false;
  private weaponSwitchRequested = false;
  private pauseRequested = false;
  private lookDeltaX = 0;
  private lookDeltaY = 0;

  private readonly handleKeyDown = (event: KeyboardEvent): void => {
    this.pressedKeys.add(event.code);

    if (event.code === 'Space') {
      event.preventDefault();

      if (!event.repeat) {
        this.jumpRequested = true;
      }
    }

    if (event.code === 'Digit1') {
      event.preventDefault();

      if (!event.repeat) {
        this.weaponSwitchRequested = true;
      }
    }

    if (event.code === 'Escape') {
      event.preventDefault();

      if (!event.repeat) {
        this.pauseRequested = true;
      }
    }
  };

  private readonly handleKeyUp = (event: KeyboardEvent): void => {
    this.pressedKeys.delete(event.code);
  };

  private readonly handleMouseMove = (event: MouseEvent): void => {
    if (!this.isPointerLocked) {
      return;
    }

    this.lookDeltaX += event.movementX;
    this.lookDeltaY += event.movementY;
  };

  private readonly handleMouseDown = (event: MouseEvent): void => {
    if (event.button !== 0) {
      return;
    }

    if (!this.isPointerLocked) {
      return;
    }

    this.isPrimaryFireHeld = true;
    event.preventDefault();
  };

  private readonly handleMouseUp = (event: MouseEvent): void => {
    if (event.button === 0) {
      this.isPrimaryFireHeld = false;
    }
  };

  private readonly handleWindowBlur = (): void => {
    this.resetInputs();
  };

  private readonly handleVisibilityChange = (): void => {
    if (document.visibilityState !== 'visible') {
      this.resetInputs();
    }
  };

  private readonly handlePointerLockChange = (): void => {
    this.isPointerLocked = document.pointerLockElement === this.lockElement;

    if (!this.isPointerLocked) {
      this.resetInputs();
    }

    this.onPointerLockChange?.(this.isPointerLocked);
  };

  constructor(lockElement: HTMLElement) {
    this.lockElement = lockElement;
    window.addEventListener('keydown', this.handleKeyDown);
    window.addEventListener('keyup', this.handleKeyUp);
    window.addEventListener('mousemove', this.handleMouseMove);
    window.addEventListener('mousedown', this.handleMouseDown);
    window.addEventListener('mouseup', this.handleMouseUp);
    window.addEventListener('blur', this.handleWindowBlur);
    document.addEventListener('pointerlockchange', this.handlePointerLockChange);
    document.addEventListener('visibilitychange', this.handleVisibilityChange);
  }

  public requestPointerLock(): void {
    void this.lockElement.requestPointerLock();
  }

  public getMovementAxes(): { forward: number; right: number } {
    const forward =
      Number(this.pressedKeys.has('KeyW') || this.pressedKeys.has('ArrowUp')) -
      Number(this.pressedKeys.has('KeyS') || this.pressedKeys.has('ArrowDown'));
    const right =
      Number(this.pressedKeys.has('KeyD') || this.pressedKeys.has('ArrowRight')) -
      Number(this.pressedKeys.has('KeyA') || this.pressedKeys.has('ArrowLeft'));

    return { forward, right };
  }

  public isSprintHeld(): boolean {
    return this.pressedKeys.has('ShiftLeft') || this.pressedKeys.has('ShiftRight');
  }

  public isFireHeld(): boolean {
    return this.isPrimaryFireHeld && this.isPointerLocked;
  }

  public consumeJumpPressed(): boolean {
    const requested = this.jumpRequested && this.isPointerLocked;
    this.jumpRequested = false;
    return requested;
  }

  public consumeWeaponSwitchPressed(): boolean {
    const requested = this.weaponSwitchRequested && this.isPointerLocked;
    this.weaponSwitchRequested = false;
    return requested;
  }

  public consumePausePressed(): boolean {
    const requested = this.pauseRequested;
    this.pauseRequested = false;
    return requested;
  }

  public consumeLookDelta(): { x: number; y: number } {
    const delta = { x: this.lookDeltaX, y: this.lookDeltaY };
    this.lookDeltaX = 0;
    this.lookDeltaY = 0;
    return delta;
  }

  public dispose(): void {
    window.removeEventListener('keydown', this.handleKeyDown);
    window.removeEventListener('keyup', this.handleKeyUp);
    window.removeEventListener('mousemove', this.handleMouseMove);
    window.removeEventListener('mousedown', this.handleMouseDown);
    window.removeEventListener('mouseup', this.handleMouseUp);
    window.removeEventListener('blur', this.handleWindowBlur);
    document.removeEventListener('pointerlockchange', this.handlePointerLockChange);
    document.removeEventListener('visibilitychange', this.handleVisibilityChange);
  }

  private resetInputs(): void {
    this.pressedKeys.clear();
    this.isPrimaryFireHeld = false;
    this.jumpRequested = false;
    this.weaponSwitchRequested = false;
    this.pauseRequested = false;
    this.lookDeltaX = 0;
    this.lookDeltaY = 0;
  }
}
