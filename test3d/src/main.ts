import { InteractionManager } from './webgl/InteractionManager';
import { WebGLRenderer } from './webgl/WebGLRenderer';
import './style.css';

const canvas = document.querySelector<HTMLCanvasElement>('#webgl-canvas');

if (!canvas) {
  throw new Error('Can not find #webgl-canvas element.');
}

const renderer = new WebGLRenderer(canvas);
const interactionManager = new InteractionManager(renderer,canvas);

console.log('[Scene] WebGL2 scene initialized', {
  camera: {
    position: Array.from(renderer.cameraPosition),
    target: Array.from(renderer.cameraTarget),
  },
  models: renderer.models.map((model) => ({
    name: model.name,
    vertexCount: model.vertices.length / 3,
    vertices: Array.from(model.vertices),
    modelMatrix: Array.from(model.modelMatrix),
  })),
  interactionState: {
    left: {
      rotation: Array.from(interactionManager.state.left.rotation),
      translation: Array.from(interactionManager.state.left.translation),
      transformMatrix: Array.from(interactionManager.state.left.transformMatrix),
    },
    right: {
      rotation: Array.from(interactionManager.state.right.rotation),
      translation: Array.from(interactionManager.state.right.translation),
      transformMatrix: Array.from(interactionManager.state.right.transformMatrix),
    },
  },
});
