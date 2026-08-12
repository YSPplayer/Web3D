export const vertexShaderSource = `#version 300 es
in vec3 aPosition;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;

void main() {
  gl_Position = uProjection * uView * uModel * vec4(aPosition, 1.0);
}
`;

export const fragmentShaderSource = `#version 300 es
precision mediump float;

out vec4 outColor;

void main() {
  outColor = vec4(0.18, 0.82, 0.42, 1.0);
}
`;
