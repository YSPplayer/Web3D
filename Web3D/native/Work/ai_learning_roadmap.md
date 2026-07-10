# AI 学习路线：从手搓 CNN/CRNN 到现代深度学习

## 1. 当前阶段判断

当前项目已经完成或正在完成的能力：

- 用 C++ 自己实现基础张量结构。
- 自己实现矩阵乘法、前向传播、反向传播。
- 手写 CNN 分类网络，包括 Conv2D、ReLU、MaxPool、Flatten、Linear、SoftMax、Loss。
- 正在推进 CRNN OCR，包括 HeightPool、FeatureToSequence、BiLSTM、CTC Loss。

这说明当前学习重点已经不再是“神经网络是什么”，而是进入了更底层的阶段：

- 计算图如何组织。
- 梯度如何通过网络传播。
- 参数如何更新。
- CNN 如何提取空间特征。
- RNN/LSTM/CTC 如何处理序列任务。

下一步不要只追求继续堆更多层，应该开始学习“如何稳定训练模型”和“现代 AI 主干结构”。

## 2. 推荐总路线

建议学习顺序：

```text
当前 CRNN 收尾
-> 训练系统能力
-> 手搓 mini autograd
-> Attention / Transformer
-> PyTorch 对照复现
-> LLM / RAG / LoRA / 多模态 / Diffusion
```

如果只选一个最重要的下一步模块，优先学习：

```text
Attention + Transformer
```

如果想把基础打得更扎实，优先学习：

```text
Autograd + 优化器 + 梯度检查
```

## 3. 第一阶段：把 CRNN 训练链路收尾

目标不是做大模型，而是把当前手搓深度学习链路跑完整。

需要补齐的模块：

- `MaxPool2D` 支持 `poolH / poolW`。
- `HeightPool` 和 `FeatureToSequence` 完整接入网络构建。
- `BiLSTM` 补齐 `ClearGrad` 和 `AccumulateGrad`。
- 实现 `SequenceLinear`，每个时间步共享同一组权重。
- 实现 `TimeSoftmax`，每个时间步单独 softmax。
- 实现 `CTCLoss Backward`，输出 `dLogits`。
- 实现 CTC greedy decoder。
- 建立 OCR 样本格式和字符表。

阶段验收目标：

```text
CNN + CTC 能 overfit 100 张英文数字短文本图片。
加入 BiLSTM 后，验证集 textAcc 高于 CNN + CTC。
```

这个阶段的学习价值：

- 理解 OCR 为什么需要序列建模。
- 理解 CTC 如何处理输入长度和标签长度不一致的问题。
- 理解 LSTM 的梯度如何跨时间传播。

## 4. 第二阶段：训练系统能力

当前项目已经能写层，但真正训练好模型还需要训练系统能力。

重点学习：

- 梯度检查：numerical gradient check。
- 初始化：Xavier、He initialization。
- 优化器：SGD、Momentum、RMSProp、Adam。
- 正则化：L2 weight decay、Dropout。
- 归一化：BatchNorm、LayerNorm。
- 学习率策略：step decay、cosine decay、warmup。
- 梯度裁剪：gradient clipping。
- 训练诊断：过拟合、欠拟合、梯度爆炸、梯度消失。

建议在当前项目中实践：

- 给每一层写一个小型梯度检查工具。
- 给 `Linear`、`Conv2D`、`BiLSTM` 做 numerical gradient check。
- 加入 Adam 优化器。
- 给 LSTM/CTC 训练加 gradient clipping。
- 打印 loss、grad norm、weight norm。

阶段验收目标：

```text
能判断一次训练失败是模型问题、数据问题、初始化问题、学习率问题，还是梯度实现问题。
```

## 5. 第三阶段：手搓 mini autograd

你现在每一层都手写 `Backward`，这是非常好的基础。下一步应该理解 PyTorch 这类框架为什么能自动反传。

建议实现一个极简 autograd 引擎。

核心结构：

```cpp
struct Tensor {
    std::vector<float> data;
    std::vector<float> grad;
    std::vector<Tensor*> parents;
    std::function<void()> backward;
};
```

先支持这些算子：

- `add`
- `mul`
- `matmul`
- `relu`
- `sigmoid`
- `tanh`
- `softmax`
- `cross_entropy`

重点学习：

- 计算图。
- 拓扑排序。
- 梯度累积。
- leaf tensor 和 intermediate tensor。
- backward function 闭包。

阶段验收目标：

```text
用 mini autograd 写一个两层 MLP，并自动完成反向传播。
```

这个阶段非常关键。学完以后，再看 PyTorch 的 `autograd`、`nn.Module`、`optimizer` 会清楚很多。

## 6. 第四阶段：Attention 和 Transformer

做完 CNN + LSTM/CTC 后，最自然的下一站是 Attention 和 Transformer。

原因：

- CRNN 是老一代 OCR 和序列建模方案。
- Transformer 是现代 NLP、OCR、视觉、多模态模型的主干。
- 你已经理解 LSTM，再学 Attention 会更容易明白它解决了什么问题。

学习顺序：

```text
Seq2Seq
-> Bahdanau Attention / Luong Attention
-> Self-Attention
-> Multi-Head Attention
-> Position Encoding
-> Transformer Encoder
-> Transformer Decoder
-> Masked Attention
-> LayerNorm + Residual
```

建议手搓模块：

- Scaled dot-product attention。
- Multi-head attention。
- Transformer encoder block。
- Transformer decoder block。
- 小型字符级语言模型。

阶段验收目标：

```text
能手写一个小型 Transformer Encoder，并解释 Q/K/V、mask、position encoding、LayerNorm、residual 的作用。
```

## 7. 第五阶段：开始用 PyTorch 做对照实验

手搓底层可以建立理解，但学习 AI 不能长期只停留在纯 C++ 低层实现。

建议方式：

- 同一个 CNN，用 C++ 手搓一版，用 PyTorch 复现一版。
- 同一个 CRNN + CTC，用 PyTorch 复现一版。
- 对比 loss、梯度、准确率、收敛速度。
- 用 PyTorch 验证自己 C++ 实现的梯度是否正确。

重点学习：

- `torch.Tensor`
- `autograd`
- `nn.Module`
- `DataLoader`
- `optimizer`
- GPU 训练
- 模型保存和加载

阶段验收目标：

```text
能用 PyTorch 快速复现自己的 C++ CNN/CRNN，并用它反查 C++ 实现里的问题。
```

## 8. 第六阶段：进入现代 AI 主线

当 Transformer 掌握之后，再进入现代 AI 模块。

推荐顺序：

```text
Tokenizer
-> Embedding
-> Causal Language Model
-> Pretraining / Fine-tuning
-> RAG
-> LoRA / QLoRA
-> Vision Transformer
-> CLIP
-> Diffusion
-> Multimodal Models
```

重点模块：

- LLM 基础：tokenizer、embedding、causal mask、next token prediction。
- RAG：embedding 检索、向量数据库、rerank、上下文构造。
- 微调：SFT、LoRA、QLoRA。
- 多模态：图像编码器、文本编码器、对比学习。
- Diffusion：噪声预测、U-Net、scheduler、采样过程。

阶段验收目标：

```text
能理解一个小型 GPT 的训练流程，并能使用 LoRA 微调一个开源模型完成具体任务。
```

## 9. 推荐学习资料

### 深度学习基础和训练系统

- Dive into Deep Learning: https://d2l.ai/
- Stanford CS231n: https://cs231n.github.io/

### NLP、Attention、Transformer

- Stanford CS224N: https://web.stanford.edu/class/cs224n/
- Hugging Face LLM Course: https://huggingface.co/learn/llm-course/en/chapter1/1

### 实践方向

- 用 PyTorch 复现当前 C++ CNN。
- 用 PyTorch 复现当前 C++ CRNN + CTC。
- 用 Hugging Face Transformers 跑通 tokenizer、模型推理、微调。

## 10. 对当前项目的短期建议

短期不要同时开太多方向，建议按这个顺序推进：

1. 把 CRNN 文档第 3 节的主链路跑通。
2. 补 `CTCLoss Backward`。
3. 补 `SequenceLinear` 和 `TimeSoftmax`。
4. 给核心层做梯度检查。
5. 给训练加入 Adam 和 gradient clipping。
6. 用 PyTorch 复现一版 CRNN 作为对照。
7. 开始手搓 Attention。
8. 再进入 Transformer。

最重要的判断标准：

```text
不是代码写得越底层越好，而是你能否解释每个模块为什么存在、梯度怎么流、训练失败时怎么定位。
```

