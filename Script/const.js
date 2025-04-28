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

export const GlData = {
    mouseLeftPressed: false,
    mouseRightPressed: false,
    controlPressed: false,
    lastX: 0.0,
    lastY: 0.0,
    modelSensitivity: 1.0,
}

export const LightPointType = Object.freeze({
    Static : 0,//静态
    Dynamics : 1//动态
}
);

export const ImageType = Object.freeze({
    Default : 0,//默认图片
    Specular : 1,//镜面反射
    Max : 2,//最大值
}
);

export const PlaneModelType = Object.freeze({
    Surface : 0,
    Ring : 1
});

export const MapColorType = Object.freeze({ 
    Gold : 0, //黄铜色
    Rainbow : 1,//七彩色
    Contour : 2,//等高线
    BlackWhite : 3,//黑白色
    Blue : 4,//蓝色
    Rainbow2 : 5,//七彩色2
    Rainbow3 : 6,//七彩色3
    Viridis : 7,//翡翠绿
    ColorMax : 8
});

export const VBOType = Object.freeze({
    Vertex: 0,    // 顶点索引
    Normal: 1,    // 法线索引
    Mapcolor: 2,  // 伪彩色贴图索引
    Texture: 3,   // 贴图索引
    Wall: 4,      // 墙面数组
    Flag: 5,      // 存储标签位，记录丢弃点
    Index: 6,     // 存储索引位，存放每一个点的索引
    Max: 7
});

export const GL_CONST = Object.freeze({
    ALGORITHM_MAX_POINT_SIZE : 2000000,//最大非稀疏点云数
});
export const v_planemodelshader = `#version 300 es
in vec3 aPos; 
in vec3 aNormal;
in vec3 aColor;
uniform mat4 mposition;
uniform mat4 view;
uniform mat4 projection;
uniform mat3 normalMatrix;
out vec3 Normal;
out vec3 FragPos;
out vec3 ColorMap;
void main() {
	 FragPos = vec3(mposition * vec4(aPos, 1.0)); 
    gl_Position = projection * view * vec4(FragPos, 1.0);
     Normal = normalMatrix * aNormal;
     ColorMap = aColor;
}
`;

export const f_planemodelshader = `#version 300 es
precision highp float;
out vec4 FragColor;   
struct Material {
    vec3 ambient;
    vec3 diffuse; 
    vec3 specular;
    float shininess;
};

struct Light {
    vec3 position;
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
    float constant;
    float linear;
    float quadratic;
};
in vec3 Normal;
in vec3 FragPos;
in vec3 ColorMap;
uniform Material material;
uniform Light light;
uniform vec3 viewPos;
uniform vec3 defaultObjectColor;
void main() {
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(light.position - FragPos);
    vec3 viewDir = normalize(viewPos - FragPos);
    float distance = length(light.position - FragPos);
    float attenuation = 1.0 / (light.constant + light.linear * distance + 
                              light.quadratic * (distance * distance));
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = light.diffuse * (diff * ColorMap);
    vec3 halfwayDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(norm, halfwayDir), 0.0), material.shininess);
    vec3 specular = light.specular * (spec * material.specular);
    vec3 ambient = light.ambient * material.ambient;
    ambient *= attenuation;
    diffuse *= attenuation;
    specular *= attenuation;
    vec3 result = ambient + diffuse + specular;
    FragColor = vec4(pow(result, vec3(1.0/2.2)), 1.0);     
}
`;
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
export const f_lineshader = f_defaultshader;//const f_lineshader = f_defaultshader.arg("1.0");
