import { mat4, vec3 } from 'gl-matrix';

const rectangleIndices = new Uint16Array([
  0, 1, 2,
  0, 2, 3,
]);

export class RectangleModel {
  public modelMatrix = mat4.create();

  private readonly vertexArray: WebGLVertexArrayObject;
  private readonly vertexBuffer: WebGLBuffer;
  private readonly indexBuffer: WebGLBuffer;

  constructor(
    private readonly gl: WebGL2RenderingContext,
    readonly name: string,
    readonly vertices: Float32Array,
    positionLocation: number,
  ) {
    const vertexArray = gl.createVertexArray();
    const vertexBuffer = gl.createBuffer();
    const indexBuffer = gl.createBuffer();

    if (!vertexArray || !vertexBuffer || !indexBuffer) {
      throw new Error(`无法创建模型 ${name} 的 WebGL 缓冲区。`);
    }

    this.vertexArray = vertexArray;
    this.vertexBuffer = vertexBuffer;
    this.indexBuffer = indexBuffer;

    gl.bindVertexArray(this.vertexArray);

    gl.bindBuffer(gl.ARRAY_BUFFER, this.vertexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);
    gl.enableVertexAttribArray(positionLocation);
    gl.vertexAttribPointer(positionLocation, 3, gl.FLOAT, false, 0, 0);

    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.indexBuffer);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, rectangleIndices, gl.STATIC_DRAW);

    gl.bindVertexArray(null);
    gl.bindBuffer(gl.ARRAY_BUFFER, null);
  }

  draw(modelLocation: WebGLUniformLocation): void {
    this.gl.uniformMatrix4fv(modelLocation, false, this.modelMatrix);
    this.gl.bindVertexArray(this.vertexArray);
    this.gl.drawElements(
      this.gl.TRIANGLES,
      rectangleIndices.length,
      this.gl.UNSIGNED_SHORT,
      0,
    );
  }
  getCenter(): vec3 {
    const center = vec3.create();
    const vertexCount = this.vertices.length / 3;
    // 如果没有任何顶点，返回原点
    if (vertexCount === 0) {
        return center;
    }
    // 累加所有顶点的坐标
    for (let index = 0; index < this.vertices.length; index += 3) {
        center[0] += this.vertices[index];
        center[1] += this.vertices[index + 1];
        center[2] += this.vertices[index + 2];
    }
    // 计算平均值（直接缩放 1/vertexCount）
    vec3.scale(center, center, 1 / vertexCount);
    return center;
}

  dispose(): void {
    this.gl.deleteBuffer(this.vertexBuffer);
    this.gl.deleteBuffer(this.indexBuffer);
    this.gl.deleteVertexArray(this.vertexArray);
  }
}
