import { mat4, vec3 } from 'gl-matrix';
import { RectangleModel } from './RectangleModel';
import { fragmentShaderSource, vertexShaderSource } from './shaders';

export class WebGLRenderer {
  readonly cameraPosition = vec3.fromValues(0, 0, 6);
  readonly cameraTarget = vec3.fromValues(0, 0, 0);
  readonly models: RectangleModel[];

  private readonly gl: WebGL2RenderingContext;
  private readonly program: WebGLProgram;
  private readonly viewMatrix = mat4.create();
  private readonly projectionMatrix = mat4.create();
  private readonly modelLocation: WebGLUniformLocation;
  private readonly viewLocation: WebGLUniformLocation;
  private readonly projectionLocation: WebGLUniformLocation;

  constructor(private readonly canvas: HTMLCanvasElement) {
    const gl = canvas.getContext('webgl2', {
      antialias: true,
      alpha: false,
    });

    if (!gl) {
      throw new Error('当前浏览器或显卡环境不支持 WebGL2。');
    }

    this.gl = gl;
    this.program = this.createProgram(vertexShaderSource, fragmentShaderSource);

    const positionLocation = gl.getAttribLocation(this.program, 'aPosition');
    const modelLocation = gl.getUniformLocation(this.program, 'uModel');
    const viewLocation = gl.getUniformLocation(this.program, 'uView');
    const projectionLocation = gl.getUniformLocation(this.program, 'uProjection');

    if (
      positionLocation < 0 ||
      !modelLocation ||
      !viewLocation ||
      !projectionLocation
    ) {
      throw new Error('Shader 属性或矩阵 uniform 初始化失败。');
    }

    this.modelLocation = modelLocation;
    this.viewLocation = viewLocation;
    this.projectionLocation = projectionLocation;

    // 两个模型各有四个顶点，分别完全位于世界坐标的 X 负半轴和正半轴。
    this.models = [
      new RectangleModel(
        gl,
        'negative-x-rectangle',
        new Float32Array([
          -2.25, -1.0, 0.0,
          -0.45, -1.0, 0.0,
          -0.45,  1.0, 0.0,
          -2.25,  1.0, 0.0,
        ]),
        positionLocation,
      ),
      new RectangleModel(
        gl,
        'positive-x-rectangle',
        new Float32Array([
           0.45, -1.0, 0.0,
           2.25, -1.0, 0.0,
           2.25,  1.0, 0.0,
           0.45,  1.0, 0.0,
        ]),
        positionLocation,
      ),
    ];

    mat4.lookAt(
      this.viewMatrix,
      this.cameraPosition,
      this.cameraTarget,
      vec3.fromValues(0, 1, 0),
    );

    gl.enable(gl.DEPTH_TEST);
    gl.clearColor(0.063, 0.075, 0.094, 1.0);

    window.addEventListener('resize', this.render);
    this.render();
  }

  readonly render = (): void => {
    this.resizeCanvasToDisplaySize();

    const { gl, canvas } = this;
    const aspect = canvas.width / Math.max(canvas.height, 1);
    mat4.perspective(this.projectionMatrix, Math.PI / 4, aspect, 0.1, 100);

    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.useProgram(this.program);
    gl.uniformMatrix4fv(this.viewLocation, false, this.viewMatrix);
    gl.uniformMatrix4fv(this.projectionLocation, false, this.projectionMatrix);

    for (const model of this.models) {
      model.draw(this.modelLocation);
    }

    gl.bindVertexArray(null);
  };

  private resizeCanvasToDisplaySize(): void {
    const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
    const displayWidth = Math.max(1, Math.round(this.canvas.clientWidth * pixelRatio));
    const displayHeight = Math.max(1, Math.round(this.canvas.clientHeight * pixelRatio));

    if (this.canvas.width !== displayWidth || this.canvas.height !== displayHeight) {
      this.canvas.width = displayWidth;
      this.canvas.height = displayHeight;
    }
  }

  private createProgram(vertexSource: string, fragmentSource: string): WebGLProgram {
    const vertexShader = this.compileShader(this.gl.VERTEX_SHADER, vertexSource);
    const fragmentShader = this.compileShader(this.gl.FRAGMENT_SHADER, fragmentSource);
    const program = this.gl.createProgram();

    if (!program) {
      throw new Error('无法创建 WebGL Shader Program。');
    }

    this.gl.attachShader(program, vertexShader);
    this.gl.attachShader(program, fragmentShader);
    this.gl.linkProgram(program);

    if (!this.gl.getProgramParameter(program, this.gl.LINK_STATUS)) {
      const message = this.gl.getProgramInfoLog(program) ?? '未知链接错误';
      this.gl.deleteProgram(program);
      throw new Error(`Shader Program 链接失败：${message}`);
    }

    this.gl.deleteShader(vertexShader);
    this.gl.deleteShader(fragmentShader);
    return program;
  }

  private compileShader(type: number, source: string): WebGLShader {
    const shader = this.gl.createShader(type);

    if (!shader) {
      throw new Error('无法创建 WebGL Shader。');
    }

    this.gl.shaderSource(shader, source);
    this.gl.compileShader(shader);

    if (!this.gl.getShaderParameter(shader, this.gl.COMPILE_STATUS)) {
      const message = this.gl.getShaderInfoLog(shader) ?? '未知编译错误';
      this.gl.deleteShader(shader);
      throw new Error(`Shader 编译失败：${message}`);
    }

    return shader;
  }

  dispose(): void {
    window.removeEventListener('resize', this.render);
    for (const model of this.models) {
      model.dispose();
    }
    this.gl.deleteProgram(this.program);
  }
}
