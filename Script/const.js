export const GlType = Object.freeze({
    Null: 0,  
    WebGl: 1,
    WebGl2:2
});

export const LightType = Object.freeze({
    Parallel : 0,//平行光
    Point : 1//点光源
}
);

export const LightPointType = Object.freeze({
    Static : 0,//静态
    Dynamics : 1//动态
}
);

export const VBOType = Object.freeze({
    Vertex: 0,    // 顶点索引
    Texture: 1,   // 贴图索引
    Normal: 2,    // 法线索引
    Mapcolor: 3,  // 伪彩色贴图索引
    Wall: 4,      // 墙面数组
    Flag: 5,      // 存储标签位，记录丢弃点
    Index: 6,     // 存储索引位，存放每一个点的索引
    Max: 7
});

//shader脚本 不能把头声明放在第二行会报错
export const v_lineshader = `#version 300 es
in vec3 aPos; 
uniform mat4 view;
uniform mat4 projection;
uniform mat4 mposition;
void main() {
	gl_Position = projection * view * vec4(vec3(mposition * vec4(aPos, 1.0)), 1.0);
}
`;

export const f_defaultshader = `#version 300 es
precision mediump float; 
out vec4 FragColor;   
uniform vec3 defaultObjectColor;
void main() {
    FragColor = vec4(defaultObjectColor,1.0);
}
`;
export const f_lineshader = f_defaultshader;
//const f_lineshader = f_defaultshader.arg("1.0");