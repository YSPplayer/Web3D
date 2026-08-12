import { glMatrix, mat4, vec3 } from 'gl-matrix';
import { WebGLRenderer } from './WebGLRenderer';
type DragButton = 'left' | 'right' | null;
type ActiveModelState = {
  target: 'left' | 'right';
  state: ModelInteractionState;
  islock:Boolean;
};
export type TransformTarget = 'left' | 'right' | 'sync';

export interface ModelInteractionState {
  rotation: vec3;
  translation: vec3;
  transformMatrix: mat4;
}

export interface InteractionState {
  left: ModelInteractionState;
  right: ModelInteractionState;
}


function createModelInteractionState(): ModelInteractionState {
  return {
    rotation: vec3.create(),
    translation: vec3.create(),
    transformMatrix: mat4.create(),
  };
}

export class InteractionManager {
  readonly state: InteractionState = {
    left: createModelInteractionState(),
    right: createModelInteractionState(),
  };
  private readonly syncGroupMatrix = mat4.create() //父组件矩阵
  private readonly syncLocalMatrices = {
    left: mat4.create(),
    right: mat4.create(),
  }
  private activeButton: DragButton = null;
  private activeTarget: TransformTarget = 'left';
  private previousX = 0;
  private previousY = 0;
  private readonly targetButtons: HTMLButtonElement[] = [];

  private readonly rotationSensitivity = 0.01;
  private readonly translationSensitivity = 0.01;

  constructor(private readonly renderer:WebGLRenderer, private readonly canvas: HTMLCanvasElement) {
    canvas.addEventListener('pointerdown', this.handlePointerDown);
    canvas.addEventListener('pointermove', this.handlePointerMove);
    canvas.addEventListener('pointerup', this.handlePointerUp);
    canvas.addEventListener('pointercancel', this.handlePointerUp);
    canvas.addEventListener('contextmenu', this.preventContextMenu);
    this.targetButtons = Array.from(
      document.querySelectorAll<HTMLButtonElement>('[data-transform-target]'),
    );
    this.targetButtons.forEach((button) => {
      button.addEventListener('click', this.handleTargetButtonClick);
    });
    this.updateTargetButtons();
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
    if(target === 'sync'){
      // const states = this.getActiveStates()
      // const leftMatrix = states.length > 1 ? states[0].state.transformMatrix : mat4.create()
      // const rightMatrix = states.length > 1 ? states[1].state.transformMatrix : mat4.create()
      //计算逆矩阵
      const groupInv = mat4.invert(mat4.create(), this.syncGroupMatrix) as mat4
      mat4.multiply(
        this.syncLocalMatrices.left,
        groupInv,
        this.state.left.transformMatrix,
      )
      mat4.multiply(
        this.syncLocalMatrices.right,
        groupInv,
        this.state.right.transformMatrix,
      )
    } else {
      
    }
  };

  private readonly handlePointerDown = (event: PointerEvent): void => {
    if (event.button !== 0 && event.button !== 2) {
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
    const states = this.getActiveStates()
    for(const data of states) {
      const target = data.target
      const state = data.state
      const islock = data.islock
      let modelCenter = vec3.fromValues(0, 0, 0)
      if(!islock) {
          if(target === 'left') {
          modelCenter = this.renderer.models[0].getCenter()
        } else {
          modelCenter = this.renderer.models[1].getCenter()
        }
      } 
      if (this.activeButton === 'left') {
        const rotationZ = deltaX * this.rotationSensitivity;
        const rotationX = deltaY * this.rotationSensitivity;
        state.rotation[2] += rotationZ;
        state.rotation[1] += rotationX;
        if(islock) {
          const deltaMatrix = mat4.create()
          mat4.translate(deltaMatrix, deltaMatrix, modelCenter)
          mat4.rotateX(deltaMatrix, deltaMatrix, rotationX)
          mat4.rotateZ(deltaMatrix, deltaMatrix, rotationZ)
          mat4.translate(deltaMatrix, deltaMatrix, [
          -modelCenter[0],
          -modelCenter[1],
          -modelCenter[2],
        ])
        mat4.multiply( //局部坐标系旋转
            this.syncGroupMatrix,
            this.syncGroupMatrix,
            deltaMatrix
          )
        } else {
          //累计变换矩阵
          const deltaMatrix = mat4.create()
          mat4.translate(deltaMatrix, deltaMatrix, modelCenter)
          mat4.rotateX(deltaMatrix, deltaMatrix, rotationX)
          mat4.rotateZ(deltaMatrix, deltaMatrix, rotationZ)
          mat4.translate(deltaMatrix, deltaMatrix, [
            -modelCenter[0],
            -modelCenter[1],
            -modelCenter[2],
          ])
          mat4.multiply( //局部坐标系旋转
            state.transformMatrix,
            state.transformMatrix,
            deltaMatrix
          )
        }
        } else {
        const transX = deltaX * this.translationSensitivity;
        const transY = -deltaY * this.translationSensitivity;
        state.translation[0] += transX;
        state.translation[1] += transY;
        //累计变换矩阵
        const deltaMatrix = mat4.create()
        mat4.translate(deltaMatrix,deltaMatrix,[transX,0,0])
        mat4.translate(deltaMatrix,deltaMatrix,[0,transY,0])
        mat4.multiply( //世界坐标系平移
          state.transformMatrix,
          deltaMatrix,
          state.transformMatrix
        )
      }
      if(islock) {
        mat4.multiply(
          this.state.left.transformMatrix,
          this.syncGroupMatrix,
          this.syncLocalMatrices.left,
        )
        mat4.multiply(
          this.state.right.transformMatrix,
          this.syncGroupMatrix,
          this.syncLocalMatrices.right,
        )
        this.renderer.models[0].modelMatrix = this.state.left.transformMatrix
        this.renderer.models[1].modelMatrix = this.state.right.transformMatrix
        break
    } else {
     if(target === 'left') {
        this.renderer.models[0].modelMatrix = state.transformMatrix
      } else {
        this.renderer.models[1].modelMatrix = state.transformMatrix
      }
    }
    }
    this.renderer.render()

  };

  private readonly handlePointerUp = (event: PointerEvent): void => {
    if (this.activeButton && this.canvas.hasPointerCapture(event.pointerId)) {
      this.canvas.releasePointerCapture(event.pointerId);
    }
    this.activeButton = null;
  };

  private readonly preventContextMenu = (event: MouseEvent): void => {
    event.preventDefault();
  };

private getActiveStates(): ActiveModelState[] {
    if (this.activeTarget === 'left') {
      return [
        {
          target: 'left',
          state: this.state.left,
          islock:false,
        },
      ];
    }
    if (this.activeTarget === 'right') {
      return [
        {
          target: 'right',
          state: this.state.right,
          islock:false,
        },
      ];
    }
    return [
      {
        target: 'left',
        state: this.state.left,
        islock:true,
      },
      {
        target: 'right',
        state: this.state.right,
        islock:true,
      },
    ];
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
        x: state.rotation[0],
        y: state.rotation[1],
        z: state.rotation[2],
      },
      translation: {
        x: state.translation[0],
        y: state.translation[1],
        z: state.translation[2],
      },
      transformMatrix: Array.from(state.transformMatrix),
    };
  }

  private printState(): void {
    console.log('[InteractionManager] transform record', {
      activeTarget: this.activeTarget,
      left: this.serializeState(this.state.left),
      right: this.serializeState(this.state.right),
    });
  }

  dispose(): void {
    this.canvas.removeEventListener('pointerdown', this.handlePointerDown);
    this.canvas.removeEventListener('pointermove', this.handlePointerMove);
    this.canvas.removeEventListener('pointerup', this.handlePointerUp);
    this.canvas.removeEventListener('pointercancel', this.handlePointerUp);
    this.canvas.removeEventListener('contextmenu', this.preventContextMenu);
    this.targetButtons.forEach((button) => {
      button.removeEventListener('click', this.handleTargetButtonClick);
    });
  }
}
