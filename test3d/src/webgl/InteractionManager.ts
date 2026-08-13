import { mat4, vec3 } from 'gl-matrix';
import { WebGLRenderer } from './WebGLRenderer';

type DragButton = 'left' | 'right' | null;
export type TransformTarget = 'left' | 'right' | 'sync';

export interface ModelInteractionState {
  /** RX、RY、RZ，单位为弧度。 */
  rotation: vec3;
  /** TX、TY、TZ。 */
  translation: vec3;
  /** 根据姿态参数重新构建得到的最终矩阵。 */
  transformMatrix: mat4;
}

export interface InteractionState {
  left: ModelInteractionState;
  right: ModelInteractionState;
  group: ModelInteractionState;
}

function createModelInteractionState(
  translationX = 0,
  translationY = 0,
  translationZ = 0,
): ModelInteractionState {
  return {
    rotation: vec3.create(),
    translation: vec3.fromValues(
      translationX,
      translationY,
      translationZ,
    ),
    transformMatrix: mat4.create(),
  };
}

export class InteractionManager {
  readonly state: InteractionState = {
    left: createModelInteractionState(-1.35, 0, 0),
    right: createModelInteractionState(1.35, 0, 0),
    group: createModelInteractionState(),
  };

  private activeButton: DragButton = null;
  private activeTarget: TransformTarget = 'left';
  private previousX = 0;
  private previousY = 0;
  private rotateZOnly = false;
  private readonly targetButtons: HTMLButtonElement[] = [];

  private readonly rotationSensitivity = 0.01;
  private readonly translationSensitivity = 0.01;

  constructor(
    private readonly renderer: WebGLRenderer,
    private readonly canvas: HTMLCanvasElement,
  ) {
    canvas.addEventListener('pointerdown', this.handlePointerDown);
    canvas.addEventListener('pointermove', this.handlePointerMove);
    canvas.addEventListener('pointerup', this.handlePointerUp);
    canvas.addEventListener('pointercancel', this.handlePointerUp);
    canvas.addEventListener('contextmenu', this.preventContextMenu);
    window.addEventListener('keydown', this.handleKeyDown);
    window.addEventListener('keyup', this.handleKeyUp);

    this.targetButtons = Array.from(
      document.querySelectorAll<HTMLButtonElement>('[data-transform-target]'),
    );
    this.targetButtons.forEach((button) => {
      button.addEventListener('click', this.handleTargetButtonClick);
    });

    this.updateTargetButtons();
    this.rebuildModelMatrices();
    this.renderer.render();
  }

  private readonly handleTargetButtonClick = (event: MouseEvent): void => {
    const button = event.currentTarget as HTMLButtonElement;
    const target = button.dataset.transformTarget;

    if (target !== 'left' && target !== 'right' && target !== 'sync') {
      return;
    }

    this.activeTarget = target;
    this.updateTargetButtons();
    this.printState();
  };

  private readonly handlePointerDown = (event: PointerEvent): void => {
    if (event.button !== 0 && event.button !== 2) {
      return;
    }

    // 当前阶段同步模式只允许旋转，右键平移不产生任何效果。
    if (this.activeTarget === 'sync' && event.button === 2) {
      return;
    }

    this.activeButton = event.button === 0 ? 'left' : 'right';
    this.previousX = event.clientX;
    this.previousY = event.clientY;
    this.canvas.setPointerCapture(event.pointerId);
  };

  private readonly handlePointerMove = (event: PointerEvent): void => {
    if (!this.activeButton) {
      return;
    }

    const deltaX = event.clientX - this.previousX;
    const deltaY = event.clientY - this.previousY;
    this.previousX = event.clientX;
    this.previousY = event.clientY;

    const state = this.getActiveState();

    if (this.activeButton === 'left') {
      if (this.rotateZOnly) {
        state.rotation[2] += deltaX * this.rotationSensitivity;
      } else {
        state.rotation[1] += deltaX * this.rotationSensitivity;
        state.rotation[0] += deltaY * this.rotationSensitivity;
      }
    } else {
      // 同步模式的右键已经在 pointerdown 阶段禁用。
      state.translation[0] += deltaX * this.translationSensitivity;
      state.translation[1] -= deltaY * this.translationSensitivity;
    }

    this.rebuildModelMatrices();
    this.renderer.render();
    this.printState();
  };

  private readonly handlePointerUp = (event: PointerEvent): void => {
    if (this.activeButton && this.canvas.hasPointerCapture(event.pointerId)) {
      this.canvas.releasePointerCapture(event.pointerId);
    }
    this.activeButton = null;
  };

  private readonly handleKeyDown = (event: KeyboardEvent): void => {
    if (event.code === 'KeyZ') {
      this.rotateZOnly = true;
    }
  };

  private readonly handleKeyUp = (event: KeyboardEvent): void => {
    if (event.code === 'KeyZ') {
      this.rotateZOnly = false;
    }
  };

  private readonly preventContextMenu = (event: MouseEvent): void => {
    event.preventDefault();
  };

  private getActiveState(): ModelInteractionState {
    if (this.activeTarget === 'left') {
      return this.state.left;
    }

    if (this.activeTarget === 'right') {
      return this.state.right;
    }

    return this.state.group;
  }

  /**
   * 列向量约定下构造：M = T * RZ * RY * RX。
   * 点的实际执行顺序是 RX -> RY -> RZ -> T，保证先旋转再平移。
   */
  private composePoseMatrix(state: ModelInteractionState): mat4 {
    const translation = mat4.create();
    const rotationX = mat4.create();
    const rotationY = mat4.create();
    const rotationZ = mat4.create();

    mat4.translate(translation, translation, state.translation);
    mat4.rotateX(rotationX, rotationX, state.rotation[0]);
    mat4.rotateY(rotationY, rotationY, state.rotation[1]);
    mat4.rotateZ(rotationZ, rotationZ, state.rotation[2]);

    return this.multiplyMatrices(
      translation,
      rotationZ,
      rotationY,
      rotationX,
    );
  }

  private rebuildModelMatrices(): void {
    const leftLocalMatrix = this.composePoseMatrix(this.state.left);
    const rightLocalMatrix = this.composePoseMatrix(this.state.right);
    const groupMatrix = this.composePoseMatrix(this.state.group);

    mat4.copy(this.state.group.transformMatrix, groupMatrix);
    mat4.multiply(
      this.state.left.transformMatrix,
      groupMatrix,
      leftLocalMatrix,
    );
    mat4.multiply(
      this.state.right.transformMatrix,
      groupMatrix,
      rightLocalMatrix,
    );

    this.renderer.models[0].modelMatrix = this.state.left.transformMatrix;
    this.renderer.models[1].modelMatrix = this.state.right.transformMatrix;
  }

  private multiplyMatrices(...matrices: mat4[]): mat4 {
    const result = mat4.create();
    for (const matrix of matrices) {
      mat4.multiply(result, result, matrix);
    }
    return result;
  }

  private updateTargetButtons(): void {
    this.targetButtons.forEach((button) => {
      button.classList.toggle(
        'is-active',
        button.dataset.transformTarget === this.activeTarget,
      );
    });
  }

  private serializeState(state: ModelInteractionState) {
    return {
      rotationRadians: {
        rx: state.rotation[0],
        ry: state.rotation[1],
        rz: state.rotation[2],
      },
      translation: {
        tx: state.translation[0],
        ty: state.translation[1],
        tz: state.translation[2],
      },
      transformMatrix: Array.from(state.transformMatrix),
    };
  }

  private printState(): void {
    console.log('[InteractionManager] transform record', {
      activeTarget: this.activeTarget,
      rotateZOnly: this.rotateZOnly,
      left: this.serializeState(this.state.left),
      right: this.serializeState(this.state.right),
      group: this.serializeState(this.state.group),
    });
  }

  dispose(): void {
    this.canvas.removeEventListener('pointerdown', this.handlePointerDown);
    this.canvas.removeEventListener('pointermove', this.handlePointerMove);
    this.canvas.removeEventListener('pointerup', this.handlePointerUp);
    this.canvas.removeEventListener('pointercancel', this.handlePointerUp);
    this.canvas.removeEventListener('contextmenu', this.preventContextMenu);
    window.removeEventListener('keydown', this.handleKeyDown);
    window.removeEventListener('keyup', this.handleKeyUp);
    this.targetButtons.forEach((button) => {
      button.removeEventListener('click', this.handleTargetButtonClick);
    });
  }
}
