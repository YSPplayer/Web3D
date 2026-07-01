# 第一阶段：从零训练小型语言模型方案

> **给后续执行者的说明：** 如果以后按本文档逐步实现代码，建议使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans` 按任务推进。

**目标：** 使用 Python 和 PyTorch 从零搭建一个小型语言模型训练流程，重点学习语言模型训练的完整原理链路。

**总体架构：** 从最小可运行的因果语言模型开始。学习链路是：原始文本 -> tokenizer -> token 序列 -> 输入/目标右移 -> decoder-only Transformer -> 交叉熵损失 -> 自回归生成 -> checkpoint -> 离线推理。

**技术栈：** Python、PyTorch、Hugging Face `tokenizers` 或自定义简易 tokenizer、本地文本/代码语料、可选 TensorBoard、命令行脚本。

---

## 1. 可行性判断

这个阶段在本机上是可行的，但必须把预期定义准确。

可行的目标：

- 从随机初始化开始训练一个小模型。
- 理解 GPT 类语言模型如何通过 next-token prediction 学习。
- 使用本地编程相关文本、源码、Markdown 笔记作为语料。
- 保存 checkpoint，并进行本地离线推理。
- 做一个最小命令行生成工具。

暂时不现实的目标：

- 从零训练出一个高质量编程助手。
- 让小模型可靠回答广泛的编程问题。
- 达到 Qwen Coder、DeepSeek Coder、StarCoder 等预训练代码模型的水平。
- 把所有编程知识都压进模型权重里。

这一阶段正确的学习目标是：

```text
用小模型理解语言模型训练的完整机制。
不要用“它是否已经像强编程助手一样好用”来评价第一阶段。
```

## 2. 范围

本阶段要做：

- 在 `LanguageModel/` 下建立干净的 PyTorch 训练工程。
- 从本地笔记、源码、Markdown 文件中准备小型编程语料。
- 实现或接入 tokenizer。
- 实现 decoder-only Transformer 语言模型。
- 使用 next-token prediction 训练。
- 跟踪训练 loss、验证 loss 和生成样例。
- 保存/加载 checkpoint。
- 提供离线生成 CLI。

本阶段暂时不做：

- LoRA、QLoRA、SFT、RLHF、DPO、RAG、向量数据库。
- 训练十亿参数级别的大模型。
- Web UI 或 API 服务。
- 微调开源预训练模型。
- 分布式训练。

## 3. 语言模型到底在学什么

因果语言模型学习的是这个任务：

```text
给定前面的 token：x[0], x[1], ..., x[t-1]，
预测下一个 token：x[t] 的概率分布。
```

训练数据示例：

```text
文本：
int add(int a, int b) { return a + b; }

Token id：
[12, 48, 91, 33, 17, 18, 19, ...]

输入：
[12, 48, 91, 33, 17, 18]

目标：
[48, 91, 33, 17, 18, 19]
```

模型不是直接学习“问题答案表”。它反复学习的是：

```text
上下文 -> 下一个 token 的概率
```

推理时，文本生成只是不断重复 next-token prediction：

```text
prompt -> 预测 token -> 追加 token -> 再预测 token -> 再追加 token -> ...
```

这是第一阶段最核心的机制。

## 4. 推荐目录结构

后续开始实现时，建议创建这个结构：

```text
LanguageModel/
  Work/
    stage1_from_scratch_language_model_plan.md

  data/
    raw/
      notes/
      code/
      docs/
    processed/
      corpus.txt
      train.txt
      valid.txt
    tokenizer/
      tokenizer.json
      vocab.json

  src/
    lm/
      __init__.py
      config.py
      data.py
      tokenizer_train.py
      model.py
      train.py
      generate.py
      checkpoint.py
      utils.py

  scripts/
    prepare_corpus.py
    train_tokenizer.py
    train_tiny_gpt.py
    generate.py

  checkpoints/
    tiny-gpt/

  runs/
    logs/

  tests/
    test_data.py
    test_model_shapes.py
    test_generation.py
```

各部分职责：

- `data/raw/`：原始本地语料文件。
- `data/processed/`：清洗后用于训练的文本文件。
- `data/tokenizer/`：tokenizer 模型文件。
- `src/lm/data.py`：dataset 和 batch 构造。
- `src/lm/model.py`：Transformer 模型。
- `src/lm/train.py`：训练循环。
- `src/lm/generate.py`：离线生成。
- `checkpoints/`：模型权重和训练状态。
- `tests/`：shape、数据、生成流程的冒烟测试。

## 5. 阶段路线图

### Phase 0：环境确认

目标：确认 PyTorch 能使用 RTX 显卡。

推荐检查命令：

```powershell
python --version
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

RTX 50 系列显卡需要使用支持 CUDA 12.8 的 PyTorch 构建。具体安装命令等正式实现时再根据本机 Python 版本和显卡驱动决定。

验收条件：

```text
torch.cuda.is_available() == True
```

如果 CUDA 暂时不可用，也可以先在 CPU 上实现完整流程，但只跑非常小的冒烟测试。

### Phase 1：语料准备

目标：构建一个小而干净的本地编程语料。

推荐第一批语料：

- 你自己的 Markdown 学习笔记。
- 当前 C++ 神经网络源码：`native/src/Neural/`。
- 选定的前端/后端源码。
- 少量手写的 C++、Python、PyTorch、Transformer、训练原理问答笔记。

第一版先避免：

- `node_modules/`
- `dist/`
- 构建产物
- 二进制文件
- `native/Package/` 下的第三方库文件
- 巨大的第三方生成文件

第一版 `prepare_corpus.py` 应该完成：

- 遍历选定目录。
- 只保留有用扩展名：`.md`、`.txt`、`.py`、`.cpp`、`.h`、`.hpp`、`.ts`、`.vue`、`.java`、`.yml`、`.json`。
- 跳过超过大小限制的文件。
- 统一换行符。
- 加入文件边界标记。
- 写出合并后的 `data/processed/corpus.txt`。
- 拆分出 `train.txt` 和 `valid.txt`。

验收条件：

```text
data/processed/train.txt 和 data/processed/valid.txt 存在。
验证集文件不是空的。
没有包含二进制、vendor、generated 文件。
```

### Phase 2：Tokenizer

目标：理解原始文本如何变成 token id。

使用两个 tokenizer 里程碑：

1. 字符级 tokenizer。
2. BPE tokenizer。

字符级 tokenizer 的优点是透明：

```text
text -> chars -> char ids -> model
```

它效率低，但非常适合学习。

BPE tokenizer 更接近真实 LLM：

```text
text -> subword tokens -> token ids -> model
```

推荐 BPE 词表大小：

- `vocab_size = 512`：第一轮极小测试。
- `vocab_size = 4096`：本地代码语料第一版。
- `vocab_size = 8192`：语料规模变大后再尝试。

特殊 token：

```text
<pad>
<unk>
<bos>
<eos>
```

验收条件：

```text
输入文本可以编码成 token ids。
token ids 解码后能大致还原原始文本。
tokenizer 文件可以保存，并在离线状态下重新加载。
```

### Phase 3：Dataset 和 Batch

目标：把 token 流转换成语言模型训练 batch。

每个训练样本：

```text
tokens = [t0, t1, t2, t3, t4, ...]

x = [t0, t1, t2, t3]
y = [t1, t2, t3, t4]
```

重要参数：

```text
block_size：上下文长度
batch_size：每个 batch 的序列数量
```

推荐起始值：

```text
block_size = 128
batch_size = 16
```

然后再尝试：

```text
block_size = 256
batch_size = 16 或 32
```

验收条件：

```text
x.shape == [batch_size, block_size]
y.shape == [batch_size, block_size]
x 和 y 正好相差一个 token。
```

### Phase 4：Baseline 模型

目标：在写 Transformer 之前，先做最小 baseline。

实现一个 bigram language model：

```text
当前 token -> 下一个 token 的 logits
```

为什么这一步重要：

- 验证 dataset 是否正确。
- 验证 loss 计算是否正确。
- 验证生成流程是否正确。
- 在引入 Transformer 复杂度之前建立简单基线。

验收条件：

```text
Bigram 模型可以正常训练。
在极小语料上 loss 会下降。
生成结果虽然质量低，但能产生类似文本的输出。
```

### Phase 5：Tiny GPT 模型

目标：实现一个 decoder-only Transformer。

模型组件：

- Token embedding。
- Positional embedding。
- Causal self-attention。
- Multi-head attention。
- Feed-forward network。
- Residual connection。
- LayerNorm。
- 最后的 language-model head。

前向传播：

```text
token ids
-> token embeddings
-> position embeddings
-> Transformer blocks
-> final LayerNorm
-> LM head
-> logits [batch, time, vocab]
```

损失函数：

```text
cross_entropy(logits, target_token_ids)
```

推荐第一版配置：

```text
vocab_size = tokenizer 的词表大小
block_size = 128
n_layer = 4
n_head = 4
n_embd = 256
dropout = 0.1
```

这个规模足够小，适合学习和调试。

如果显存很轻松，再尝试：

```text
block_size = 256
n_layer = 6
n_head = 6 或 8
n_embd = 384 或 512
```

验收条件：

```text
模型 forward 返回的 logits shape 是 [B, T, vocab_size]。
训练 loss 会下降。
模型可以 overfit 一个很小的文本文件。
```

### Phase 6：训练循环

目标：构建真实、可理解的训练循环。

核心训练循环：

```text
for step in training_steps:
    采样 batch
    forward
    计算 loss
    backward
    裁剪梯度
    optimizer step
    清空梯度
    定期评估
    定期保存 checkpoint
```

推荐优化器：

```text
AdamW
```

推荐起始超参数：

```text
learning_rate = 3e-4
weight_decay = 0.1
grad_clip = 1.0
max_steps = 5000
eval_interval = 100
save_interval = 500
```

先让 FP32 版本跑通，再考虑混合精度：

```text
torch.cuda.amp.autocast
GradScaler
```

训练时跟踪：

- train loss
- valid loss
- tokens per second
- learning rate
- gradient norm
- sample generation

验收条件：

```text
训练可以从 checkpoint 停止和恢复。
loss 曲线可以在控制台或 TensorBoard 中看到。
随着训练推进，生成样例逐渐改善。
```

### Phase 7：评估

目标：判断模型是否真的在变好。

最低限度指标：

```text
train_loss
valid_loss
perplexity = exp(valid_loss)
```

手动评估 prompt：

```text
解释什么是 tensor：
写一个 C++ 函数：
什么是反向传播？
class Tensor {
```

预期现象：

- 一开始输出基本是噪声。
- overfit 极小语料后，会模仿那份语料。
- 在更大的本地代码/文本上训练后，会学到语法和重复表达。
- 它仍然不会成为可靠的编程助手。

验收条件：

```text
验证 loss 和训练 loss 分开统计。
生成测试来自保存后的 checkpoint，而不是只用内存中的模型。
```

### Phase 8：离线推理

目标：不联网加载训练好的模型，并在本地生成文本。

CLI 应支持：

```powershell
python scripts/generate.py --checkpoint checkpoints/tiny-gpt/latest.pt --prompt "解释梯度下降：" --max-new-tokens 200
```

生成参数：

```text
temperature
top_k
top_p
max_new_tokens
seed
```

验收条件：

```text
断开网络。
模型、tokenizer、checkpoint 都从本地文件加载。
输入 prompt 后能生成文本。
```

## 6. 推荐实验顺序

### 实验 1：Overfit 一个极小文件

目的：

```text
验证模型和训练循环是正确的。
```

数据：

```text
一个很小的 Markdown 或 C++ 文件。
```

预期结果：

```text
train loss 明显下降。
生成文本开始模仿这个文件。
```

如果这一步失败，不要扩大规模。先检查数据右移、mask、loss shape、优化器设置。

### 实验 2：训练当前项目笔记和源码

目的：

```text
在熟悉的编程材料上训练。
```

数据：

```text
native/Work/*.md
native/src/Neural/*.cpp
native/src/Neural/*.h
选定的 src/backend 文件
```

预期结果：

```text
模型学到项目里的专有词、C++ 语法、类名和常见注释风格。
```

### 实验 3：比较字符级 tokenizer 和 BPE

目的：

```text
理解 tokenizer 对训练的影响。
```

比较：

```text
char-level vocab
BPE vocab_size=4096
```

观察：

- token 序列长度
- 训练速度
- 生成代码的可读性
- loss 数值

### 实验 4：谨慎增大模型

目的：

```text
理解模型容量和显存压力。
```

尝试：

```text
small: n_layer=4, n_head=4, n_embd=256
medium: n_layer=6, n_head=6, n_embd=384
larger: n_layer=8, n_head=8, n_embd=512
```

出现以下情况就停止增大：

- CUDA out of memory。
- 训练太慢。
- 验证 loss 不再改善。
- 语料太小，过拟合明显。

## 7. 实现时要重点学习的概念

Tokenizer：

- 字符级 tokenization
- BPE
- vocabulary
- unknown token
- encode/decode

语言模型：

- next-token prediction
- input/target shifting
- logits
- softmax
- cross entropy
- perplexity

Transformer：

- embedding
- positional embedding
- Q/K/V
- scaled dot-product attention
- causal mask
- multi-head attention
- LayerNorm
- residual connection
- feed-forward network

训练：

- mini-batch
- AdamW
- learning rate
- gradient clipping
- train/validation split
- checkpoint
- overfitting
- underfitting

生成：

- autoregressive decoding
- temperature
- top-k sampling
- top-p sampling
- repetition
- context window

## 8. 常见失败模式

Loss 不下降：

- 输入和目标没有正确右移。
- learning rate 太高或太低。
- 模型输出 shape 错误。
- cross entropy 接收的维度错误。
- dataset 里大部分是垃圾文本或二进制内容。
- 梯度没有真正更新参数。

CUDA out of memory：

- 降低 `batch_size`。
- 降低 `block_size`。
- 降低 `n_layer`。
- 降低 `n_embd`。
- 不要用过大的验证 batch。

生成文本全是乱的：

- 训练初期这是正常的。
- 训练更久。
- 使用更干净的数据。
- 检查 tokenizer decode。
- 先验证模型能否 overfit 一个极小文件。

Train loss 下降但 valid loss 变差：

- 语料太小。
- 模型太大。
- 训练已经过拟合。
- 增加 dropout 或减小模型规模。

模型回答编程问题错误：

- 第一阶段这是预期现象。
- 模型学的是 token 统计规律，不是有依据的事实推理。
- 可靠编程问答要等后续的预训练模型微调和 RAG。

## 9. 里程碑

### M1：数据流水线可用

- `prepare_corpus.py` 能创建 `corpus.txt`、`train.txt`、`valid.txt`。
- 二进制/vendor/generated 文件被排除。
- batch shape 正确，并且输入/目标相差一个 token。

### M2：Bigram baseline 可用

- Bigram 模型可以训练。
- Loss 下降。
- 可以从保存的 checkpoint 生成文本。

### M3：Tiny GPT 可以 overfit 小文件

- Tiny GPT 可以 overfit 一个本地小文件。
- Causal mask 已验证。
- Checkpoint 保存/加载可用。

### M4：Tiny GPT 可以训练项目语料

- BPE tokenizer 已训练。
- Tiny GPT 可以在选定的本地编程语料上训练。
- 验证 loss 和生成样例有记录。

### M5：离线生成可用

- 断开网络。
- 从磁盘加载 tokenizer 和 checkpoint。
- 使用 CLI 从 prompt 生成文本。

## 10. 第一版实现计划

### Task 1：初始化 Python 工程

文件：

- 创建：`LanguageModel/requirements.txt`
- 创建：`LanguageModel/src/lm/__init__.py`
- 创建：`LanguageModel/src/lm/config.py`

步骤：

- 定义依赖：PyTorch、tokenizers、numpy、tqdm、tensorboard、pytest。
- 添加模型参数和训练参数的 config dataclass。
- 验证 Python 可以导入 `src/lm`。

### Task 2：准备本地语料

文件：

- 创建：`LanguageModel/scripts/prepare_corpus.py`
- 创建：`LanguageModel/data/raw/`
- 创建：`LanguageModel/data/processed/`

步骤：

- 遍历选定源码目录。
- 按扩展名和文件大小过滤。
- 跳过 vendor/build 文件夹。
- 写出 `corpus.txt`。
- 拆分 train/valid。
- 打印文件数量和字符数量。

### Task 3：实现 Tokenizer

文件：

- 创建：`LanguageModel/src/lm/tokenizer_train.py`
- 创建：`LanguageModel/scripts/train_tokenizer.py`
- 输出：`LanguageModel/data/tokenizer/tokenizer.json`

步骤：

- 先实现字符级 tokenizer，方便调试。
- 再从 `corpus.txt` 训练 BPE tokenizer。
- 保存 tokenizer 文件。
- 验证 encode/decode 往返。

### Task 4：实现 Dataset

文件：

- 创建：`LanguageModel/src/lm/data.py`
- 测试：`LanguageModel/tests/test_data.py`

步骤：

- 加载 token ids。
- 创建随机训练 batch。
- 返回 `x` 和 `y`。
- 验证 shape。
- 验证 `y` 是 `x` 右移一个 token。

### Task 5：实现 Bigram baseline

文件：

- 修改：`LanguageModel/src/lm/model.py`
- 创建：`LanguageModel/scripts/train_bigram.py`

步骤：

- 用 token embedding 实现 logits table。
- 使用 cross entropy 训练。
- 保存 checkpoint。
- 生成样例。

### Task 6：实现 Tiny GPT

文件：

- 修改：`LanguageModel/src/lm/model.py`
- 测试：`LanguageModel/tests/test_model_shapes.py`

步骤：

- 实现 causal self-attention。
- 实现 multi-head attention。
- 实现 feed-forward network。
- 实现 Transformer block。
- 实现最终 LM head。
- 验证输出 shape 是 `[B, T, vocab_size]`。

### Task 7：实现训练循环

文件：

- 创建：`LanguageModel/src/lm/train.py`
- 创建：`LanguageModel/src/lm/checkpoint.py`
- 创建：`LanguageModel/scripts/train_tiny_gpt.py`

步骤：

- 添加 AdamW。
- 添加 train/valid 评估。
- 添加 checkpoint 保存/加载。
- 添加 gradient clipping。
- 添加控制台日志。
- 添加可选 TensorBoard 日志。

### Task 8：实现离线生成

文件：

- 创建：`LanguageModel/src/lm/generate.py`
- 创建：`LanguageModel/scripts/generate.py`
- 测试：`LanguageModel/tests/test_generation.py`

步骤：

- 从本地文件加载 tokenizer。
- 从本地文件加载模型 checkpoint。
- 编码 prompt。
- 自回归生成。
- 解码输出。
- 添加 temperature 和 top-k。

## 11. 推荐第一版超参数

第一轮 Tiny GPT 训练建议使用：

```text
vocab_size: 来自 tokenizer
block_size: 128
batch_size: 16
n_layer: 4
n_head: 4
n_embd: 256
dropout: 0.1
learning_rate: 3e-4
weight_decay: 0.1
grad_clip: 1.0
max_steps: 5000
eval_interval: 100
save_interval: 500
```

如果训练稳定，再尝试：

```text
block_size: 256
batch_size: 16 或 32
n_layer: 6
n_head: 6
n_embd: 384
```

## 12. 学习检查点

完成本阶段后，你应该能回答：

- 为什么语言模型使用 next-token prediction。
- 为什么 `x` 和 `y` 要相差一个 token。
- tokenizer 的 vocabulary 是什么。
- 为什么需要 causal mask。
- Q/K/V 分别代表什么。
- multi-head attention 为什么有用。
- LayerNorm 和 residual connection 为什么有帮助。
- cross entropy 如何作用在 token logits 上。
- checkpoint 保存/加载如何工作。
- 为什么生成质量取决于数据、模型规模和训练时间。

## 13. 第一阶段停止标准

第一阶段完成的标准：

- 可以从零训练一个小型 GPT 风格模型。
- 它可以 overfit 一个极小文件。
- 它可以在选定的本地编程语料上训练。
- 它可以保存和重新加载 checkpoint。
- 它可以通过命令行 prompt 离线生成文本。
- 你能解释从原始文本到生成 token 的完整流程。

只有达到这些标准后，再进入：

```text
第二阶段：微调或适配开源预训练代码模型。
第三阶段：加入本地 RAG，提高编程知识可靠性。
第四阶段：封装成本地离线助手。
```

