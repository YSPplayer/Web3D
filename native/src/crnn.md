# CRNN OCR 手搓实现计划

## 1. 任务定义

当前 CNN 任务：

```text
input:  1 x 128 x 128
output: 4 x 10
label:  固定 4 位数字
```

CRNN OCR 任务：

```text
input:  1 x H x W 图像
output: 不定长字符串
label:  中文 / 英文 / 数字 / 符号
```

第一版先固定输入尺寸，降低实现难度：

```text
input:  1 x 32 x 160
output: T x classCount
```

其中：

```text
T = CNN 输出特征图的宽度方向时间步
classCount = 字符表数量 + blank
```

尺寸约定：

```text
本文中图像/特征图统一写成 C x H x W。
C = 通道数，H = 高度，W = 宽度。
代码里的 Tensor3D 构造函数是 Tensor3D(c, w, h)，实现时注意传参顺序和本文展示顺序不同。
```

## 2. 第一版字符表

先不要直接上中文，第一版建议只做数字和英文：

```text
0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
```

再加一个 CTC 专用类别：

```text
blank
```

类别数：

```text
10 + 26 + 26 + 1 = 63
```

建议：

```text
blankId = classCount - 1
```

中文等 CRNN 主链路跑通后再扩展。

## 3. 推荐主方案：CNN + BiLSTM + CTC

输入固定：

```text
1 x 32 x 160
```

CRNN 主网络：

| 层 | 配置 | 输出尺寸（C x H x W） | 参数量 |
| --- | --- | --- | ---: |
| Input | 灰度图 | `1 x 32 x 160` | 0 |
| Conv2D | `3x3, pad=1, out=32` | `32 x 32 x 160` | `32x1x3x3+32 = 320` |
| ReLU | - | `32 x 32 x 160` | 0 |
| MaxPool2D | `2x2` | `32 x 16 x 80` | 0 |
| Conv2D | `3x3, pad=1, out=64` | `64 x 16 x 80` | `64x32x3x3+64 = 18496` |
| ReLU | - | `64 x 16 x 80` | 0 |
| MaxPool2D | `2x2` | `64 x 8 x 40` | 0 |
| Conv2D | `3x3, pad=1, out=128` | `128 x 8 x 40` | `128x64x3x3+128 = 73856` |
| ReLU | - | `128 x 8 x 40` | 0 |
| MaxPool2D | `poolH=2, poolW=1` | `128 x 4 x 40` | 0 |
| Conv2D | `3x3, pad=1, out=256` | `256 x 4 x 40` | `256x128x3x3+256 = 295168` |
| ReLU | - | `256 x 4 x 40` | 0 |
| HeightPool | 沿高度做池化/聚合到 1 | `256 x 1 x 40` | 0 |
| FeatureToSequence | 沿宽度展开 | `T=40, F=256` | 0 |
| BiLSTM | `input=256, hidden=128` | `T=40, F=256` | `394240` |
| BiLSTM | `input=256, hidden=128` | `T=40, F=256` | `394240` |
| SequenceLinear | `256 -> 63` | `T=40, C=63` | `256x63+63 = 16191` |
| TimeSoftmax | 每个时间步 softmax | `40 x 63` | 0 |
| CTCLoss | 可变长度标签 | `loss` | 0 |

参数量约：

```text
320 + 18496 + 73856 + 295168 + 394240 + 394240 + 16191
= 1,192,511
```

## 4. 最小工程版：CNN + CTC

为了先跑通 OCR 链路，可以先不实现 BiLSTM：

| 层 | 配置 | 输出尺寸（C x H x W） |
| --- | --- | --- |
| Input | 灰度图 | `1 x 32 x 160` |
| CNN | 同上 | `256 x 1 x 40` |
| FeatureToSequence | 沿宽度展开 | `T=40, F=256` |
| SequenceLinear | `256 -> classCount` | `40 x 63` |
| TimeSoftmax | 每个时间步 softmax | `40 x 63` |
| CTCLoss | 可变长度标签 | `loss` |

这个版本不是完整 CRNN，但实现顺序更稳：

```text
先跑通可变长度 OCR
再加入 BiLSTM
```

## 5. 当前 data.h 需要扩展的层类型

当前：

```cpp
enum NeuralType {
    Null,
    Conv2D,
    RelU,
    MaxPool,
    Flatten,
    Linear,
    SoftMax
};
```

CRNN 建议新增：

| 类型 | 用途 |
| --- | --- |
| `MaxPool2D` | 支持 `poolH/poolW`，保留宽度时间步 |
| `HeightPool` | 沿高度做池化/聚合到 1，不把高度展平进通道 |
| `FeatureToSequence` | `C x 1 x W -> T x F` |
| `SequenceLinear` | 对每个时间步做 Linear |
| `TimeSoftMax` | 对每个时间步做 Softmax |
| `LSTM` | 单向序列建模 |
| `BiLSTM` | 双向序列建模 |

第一版最少需要：

```text
MaxPool2D
HeightPool
FeatureToSequence
SequenceLinear
TimeSoftMax
```

如果先做 CNN + CTC，可以暂时不实现：

```text
LSTM
BiLSTM
```

## 6. 新增核心类

建议新增目录：

```text
native/src/OCR
```

文件：

| 文件 | 作用 |
| --- | --- |
| `charset.h/.cpp` | 字符和 id 映射 |
| `ocr_sample.h/.cpp` | OCR 样本，支持可变长度标签 |
| `ctc_loss.h/.cpp` | CTC loss 前向和反向 |
| `ctc_decoder.h/.cpp` | CTC greedy decode |
| `crnn.h/.cpp` | OCR 网络训练、验证、推理入口 |
| `lstm.h/.cpp` | LSTM 层，第二阶段实现 |
| `bilstm.h/.cpp` | BiLSTM 层，第二阶段实现 |

## 7. Charset 设计

```cpp
class Charset {
public:
    bool Load(const std::string& path);
    bool Save(const std::string& path);
    int32_t CharToId(const std::string& ch) const;
    std::string IdToChar(int32_t id) const;
    int32_t BlankId() const;
    int32_t ClassCount() const;
};
```

字符表文件示例：

```text
0
1
2
...
A
B
...
blank
```

中文字符要按 UTF-8 字符切分，不能按 `char` 字节切。

## 8. OCR 样本格式

不要再用文件名当标签，中文和符号不适合放文件名。

建议使用：

```text
dataset.txt
```

格式：

```text
D:/data/ocr/000001.png	Hello123
D:/data/ocr/000002.png	中国ABC9
```

样本类：

```cpp
class OcrSample {
public:
    Tensor3D input;
    std::vector<int32_t> targetIds;
    std::string labelText;
};
```

加载器：

```cpp
class OcrSampleLoader {
public:
    static std::vector<std::string> LoadList(const std::string& datasetPath);
    static std::vector<std::shared_ptr<OcrSample>> LoadBatch(
        const std::vector<std::string>& lines,
        const Charset& charset
    );
};
```

## 9. FeatureToSequence

输入：

```text
Tensor3D: C x 1 x W
```

输出：

```text
Sequence: T x F
T = W
F = C
```

转换逻辑：

```text
for t in [0, W):
    feature[t] = tensor[:, 0, t]
```

建议新增序列张量：

```cpp
class TensorSeq {
public:
    int32_t T;
    int32_t F;
    std::vector<float> data;
};
```

内存布局：

```text
index = t * F + f
```

## 10. SequenceLinear

输入：

```text
T x F
```

输出：

```text
T x classCount
```

每个时间步共享同一组权重：

```text
y[t] = W * x[t] + b
```

参数：

```text
W: classCount x F
b: classCount
```

反向传播：

```text
dW += dy[t] * x[t]
db += dy[t]
dx[t] = W^T * dy[t]
```

## 11. TimeSoftmax

对每个时间步单独 softmax：

```text
for t in T:
    prob[t] = softmax(logits[t])
```

输出：

```text
T x classCount
```

## 12. CTC Decode

第一版只做 greedy decode。

输入：

```text
prob: T x classCount
```

步骤：

```text
1. 每个时间步取最大概率 classId
2. 合并连续重复 classId
3. 删除 blankId
4. id 转字符串
```

示例：

```text
blank, A, A, blank, B, B, 1
-> A, B, 1
-> "AB1"
```

接口：

```cpp
class CTCDecoder {
public:
    static std::string GreedyDecode(
        const TensorSeq& prob,
        const Charset& charset
    );
};
```

## 13. CTC Loss

输入：

```text
prob:      T x classCount
targetIds: L
blankId
```

输出：

```text
loss
dLogits: T x classCount
```

CTC 内部会把标签插入 blank：

```text
target: A B C
ext:    blank A blank B blank C blank
```

核心算法：

```text
alpha 前向动态规划
beta  反向动态规划
posterior 计算每个时间步每个字符的占用概率
dLogits = prob - posterior
```

数值实现建议：

```text
使用 log space
使用 logSumExp
避免直接连乘概率
```

## 14. CRNN 训练流程

```cpp
void CRNN::Train(
    const std::string& modelPath,
    const std::string& charsetPath,
    std::vector<std::string>& lines,
    int32_t maxEpoch,
    int32_t batch,
    float lr
);
```

训练逻辑：

```text
1. 固定划分 train / validate / test
2. 每个 epoch shuffle train
3. batch 动态加载图片
4. Forward
5. CTCLoss Forward
6. CTCLoss Backward
7. 网络 Backward
8. Update
9. Validate
10. 保存验证集 textAcc 最好的模型
```

## 15. CRNN 验证指标

```cpp
struct OcrValidateResult {
    float loss;
    float charAcc;
    float textAcc;
    float editDistanceMean;
    int32_t sampleCount;
};
```

指标含义：

| 指标 | 含义 |
| --- | --- |
| `loss` | CTC 平均 loss |
| `charAcc` | 字符级准确率 |
| `textAcc` | 整行文本完全正确率 |
| `editDistanceMean` | 平均编辑距离 |

保存模型优先级：

```text
textAcc 优先
textAcc 相同再看 editDistanceMean
最后看 loss
```

## 16. CRNN 推理接口

```cpp
bool CRNN::Predict(const Tensor3D& input, std::string& text);
```

流程：

```text
input
-> CNN
-> FeatureToSequence
-> BiLSTM
-> SequenceLinear
-> TimeSoftmax
-> CTCDecoder::GreedyDecode
-> text
```

第一版 CNN + CTC 流程：

```text
input
-> CNN
-> FeatureToSequence
-> SequenceLinear
-> TimeSoftmax
-> CTCDecoder::GreedyDecode
-> text
```

## 17. 模型保存需要增加的数据

当前分类模型保存：

```text
inputShape
NeuralBuild[]
Conv2D kernels/bias
Linear w/b
```

CRNN 还需要保存：

```text
modelTaskType = OCR
charset
blankId
classCount
inputH / inputW
sequenceLength T
SequenceLinear w/b
LSTM/BiLSTM weights
```

CTC Loss 和 CTC Decoder 没有训练参数，不需要保存权重。

## 18. 实现顺序

按这个顺序写：

1. `Charset`
2. `OcrSample` / `OcrSampleLoader`
3. `TensorSeq`
4. `FeatureToSequence`
5. `SequenceLinear`
6. `TimeSoftmax`
7. `CTCDecoder::GreedyDecode`
8. `CTCLoss Forward`
9. `CTCLoss Backward`
10. `CRNN` 训练、验证、推理入口
11. 模型保存/加载扩展
12. `LSTM`
13. `BiLSTM`
14. 中文字符集扩展

第一阶段验收：

```text
CNN + CTC 能 overfit 100 张英文数字短文本图片
```

第二阶段验收：

```text
加入 BiLSTM 后，验证集 textAcc 高于 CNN + CTC
```

第三阶段验收：

```text
扩展中文字符集后，能识别中文/英文/数字混合文本
```
