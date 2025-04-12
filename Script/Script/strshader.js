const v_lineshader = `
#version 300 es
in vec3 aPos; 
uniform mat4 view;
uniform mat4 projection;
uniform mat4 mposition;
void main() {
	gl_Position = projection * view * vec4(vec3(mposition * vec4(aPos, 1.0)), 1.0);
}
`;

const f_defaultShader = `
#version 300 es
precision mediump float; 
out vec4 FragColor;   
uniform vec3 defaultObjectColor;
void main() {
    FragColor = vec4(defaultObjectColor, %1);
}
`;
