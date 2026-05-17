# Model File 设计方案

## 目标

当前网络已经具备训练闭环，下一步需要支持模型持久化：

1. 保存推理模型，后续可以直接加载并预测。
2. 保存训练进度，下次可以继续训练。
3. 文件格式稳定，后续网络结构扩展时仍然可兼容。

因此建议把模型文件分成两类：

```text
inference model: 只保存推理需要的数据
checkpoint: 保存继续训练需要的数据
```

## 文件类型

### 1. 推理模型

推理模型只需要保存：

```text
网络结构
Conv2D 的 kernels / bias
Linear 的 w / b
必要的输入输出元信息
```

不需要保存：

```text
dkernels
dbias
dw
db
oldx
oldy
MaxPool indexs
训练 epoch
学习率
```

推荐扩展名：

```text
*.dlm
```

含义可以理解为：

```text
DeepLr Model
```

### 2. 训练 checkpoint

checkpoint 用于继续训练，除了推理模型内容，还应该保存：

```text
当前 epoch
当前 lr
batch size
训练配置
随机种子状态，可后续再做
优化器状态，可后续再做
```

当前项目使用的是最简单 SGD，没有 momentum、Adam 这类优化器状态，所以第一版 checkpoint 可以不用保存额外优化器参数。

推荐扩展名：

```text
*.dlckpt
```

含义：

```text
DeepLr CheckPoint
```

## 推荐文件格式

第一版建议使用自定义二进制格式，不建议用纯文本。

原因：

```text
参数都是 float，二进制读写简单
文件体积小
加载速度快
不依赖第三方 JSON 库
```

文件整体结构：

```text
Header
ModelMeta
LayerCount
LayerRecords...
CheckpointMeta optional
```

## Header 设计

每个模型文件开头固定写入：

```cpp
struct ModelHeader {
    char magic[8];       // "DLRMODL"
    int32_t version;     // 1
    int32_t fileType;    // 1=model, 2=checkpoint
};
```

作用：

```text
magic: 判断是不是 DeepLr 模型文件
version: 后续升级格式
fileType: 区分推理模型和 checkpoint
```

## ModelMeta 设计

保存模型整体信息：

```cpp
struct ModelMeta {
    int32_t inputC;
    int32_t inputW;
    int32_t inputH;
    int32_t outputW;
    int32_t outputH;
    int32_t outputC;
};
```

当前默认网络可以是：

```text
input  = [1,128,128]
output = [1,10,4]
```

## LayerRecord 设计

每一层保存一条记录：

```cpp
struct LayerHeader {
    int32_t type;
    int32_t c;
    int32_t w;
    int32_t h;
    int32_t paramTensorCount;
};
```

其中：

```text
type: NeuralType
c/w/h: 该层输出 shape 或构建信息
paramTensorCount: 该层有几个参数张量
```

不同层的参数数量：

```text
Conv2D: 2 个参数组，kernels + bias
Linear: 2 个参数，w + b
ReLU: 0
MaxPool: 0
Flatten: 0
SoftMax: 0
```

## Tensor 保存格式

每个 Tensor3D 使用统一格式保存：

```cpp
struct TensorHeader {
    int32_t c;
    int32_t w;
    int32_t h;
    int32_t count;
};
```

后面直接写入：

```text
count 个 float
```

也就是：

```cpp
file.write(reinterpret_cast<char*>(data.data()), count * sizeof(float));
```

当前 `Tensor3D::data` 是 private，所以需要给 `Tensor3D` 增加专门的保存/加载成员函数，而不是暴露 data。

建议接口：

```cpp
bool Tensor3D::Save(std::ostream& out) const;
bool Tensor3D::Load(std::istream& in);
```

## Conv2D 保存内容

当前 Conv2D 参数：

```cpp
std::vector<Tensor3D> kernels;
Tensor3D bias;
```

保存时：

```text
先保存 kernels.size()
再逐个保存 kernels[i]
最后保存 bias
```

不保存：

```text
dkernels
dbias
oldx
```

加载时必须校验：

```text
kernels.size() == ksize
bias shape == [ksize,1,1]
kernel shape == [inputChannel,3,3]
```

## Linear 保存内容

当前 Linear 参数：

```cpp
Tensor3D w;
Tensor3D b;
```

保存：

```text
w
b
```

不保存：

```text
dw
db
oldx
oldy
```

加载时校验：

```text
w shape == [1, lasth, h]
b shape == [1, 1, h]
```

## Checkpoint 保存内容

Checkpoint 在推理模型基础上额外保存：

```cpp
struct CheckpointMeta {
    int32_t epoch;
    int32_t batchSize;
    float lr;
};
```

第一版不保存梯度缓存：

```text
dw/db/dkernels/dbias 不保存
```

原因：

```text
当前项目是 batch 结束后立刻 Update，然后清空梯度
恢复训练时从下一个 epoch 或 batch 重新开始即可
```

如果以后要支持“训练到 batch 中间暂停”，才需要保存梯度和当前 batch index。

## 类接口建议

### Tensor3D

```cpp
bool Save(std::ostream& out) const;
bool Load(std::istream& in);
```

### Layer

基类增加虚函数：

```cpp
virtual bool Save(std::ostream& out) const = 0;
virtual bool Load(std::istream& in) = 0;
```

无参数层可以只保存/读取空内容：

```cpp
ReLU::Save
MaxPool::Save
Flatten::Save
SoftMax::Save
```

### Conv2D

```cpp
bool Save(std::ostream& out) const override;
bool Load(std::istream& in) override;
```

### Linear

```cpp
bool Save(std::ostream& out) const override;
bool Load(std::istream& in) override;
```

### Neural

推理模型：

```cpp
bool SaveModel(const std::string& path) const;
static std::shared_ptr<Neural> LoadModel(const std::string& path);
```

训练 checkpoint：

```cpp
bool SaveCheckpoint(const std::string& path, int32_t epoch, int32_t batchSize, float lr) const;
static std::shared_ptr<Neural> LoadCheckpoint(const std::string& path);
```

## 加载流程

加载推理模型：

```text
1. 读取 Header
2. 校验 magic/version/fileType
3. 读取 ModelMeta
4. 读取 layerCount
5. 逐层读取 LayerHeader
6. 根据 type 构建对应 Layer 对象
7. 调用 layer->Load(in)
8. 返回 Neural 对象
```

加载 checkpoint：

```text
1. 前面流程和推理模型一致
2. 额外读取 CheckpointMeta
3. 返回 Neural 对象，同时返回 epoch/lr/batchSize 信息
```

## 推理接口建议

模型加载后需要单独提供推理接口：

```cpp
Tensor3D Neural::Predict(const Tensor3D& input);
std::array<int32_t, 4> Neural::PredictLabel(const Tensor3D& input);
```

其中 `Predict` 只做 forward，不做：

```text
loss
backward
update
```

`PredictLabel` 逻辑：

```text
SoftMax 输出 [1,10,4]
每一行取最大概率的数字
返回 4 个数字
```

## 第一版实现顺序

建议按这个顺序做：

```text
1. 给 Tensor3D 增加 Save/Load
2. 给 Layer 增加 Save/Load 虚函数
3. 实现 Linear Save/Load
4. 实现 Conv2D Save/Load
5. 无参数层实现空 Save/Load
6. Neural 实现 SaveModel/LoadModel
7. Neural 实现 SaveCheckpoint/LoadCheckpoint
8. 增加 Predict/PredictLabel
9. 用 100 张无噪声数据训练后保存模型
10. 重启程序，加载模型，验证同一批图像预测结果一致
```

## 正确性验证

最小验证流程：

```text
1. 训练 100 张无噪声图到 loss < 0.01
2. 保存 model.dlm
3. 程序退出
4. 重新启动
5. LoadModel("model.dlm")
6. 对同一批 100 张图执行 PredictLabel
7. 预测结果应基本全对
```

checkpoint 验证：

```text
1. 训练 20 epoch
2. 保存 checkpoint.dlckpt
3. 程序退出
4. 重新加载 checkpoint
5. 继续训练到 150 epoch
6. loss 应继续下降，而不是重新从随机水平开始
```

## 注意事项

1. 推理模型不要保存训练缓存，否则文件会膨胀，也容易引入脏状态。
2. checkpoint 第一版只保存 epoch/lr/batchSize 和参数即可。
3. 文件必须保存网络结构，不能只保存权重，否则加载时不知道怎么构建层。
4. 加载时必须做 shape 校验，否则错误模型文件会导致后续计算越界。
5. 推理时不要调用 `Backward` 和 `Update`。
6. 后续如果加入 Adam，需要额外保存一阶矩、二阶矩和 step。

