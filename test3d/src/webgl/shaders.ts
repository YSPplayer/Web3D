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

/*
M = I
M = M *  -Center
M = M * Rx
M = M * Rz
M = M * Cnter

OK,分析一下看我下面说的对不对，当前默认的非锁定视口下的左右模型的变换矩阵算法 
Center 是当前的模型点云中心的矩阵
A (累计变换矩阵)
M = I(单位矩阵)
M = M * Center  * Rz  * Rx * -Center
A = A * M

M2 = I(单位矩阵)
M2 = M2 * Ty * Tx
A = A * M2

P' = A * P(点坐标，不考虑相机等视图矩阵的变换)

如果处于锁定模式下:
在鼠标按下的时候重置模型的累计同步矩阵S，并记录当前的左右的初始矩阵A1和B1
M = I(单位矩阵)
M = M * Rz  * Rx (因为原点就是世界坐标系中心所以不变换)
M = M * Ty * Tx 
S = S * M
A = S * A1
B = S * B1
PA' = A * P
PA' = B * P
*/