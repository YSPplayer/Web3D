from __future__ import annotations

import json
from pathlib import Path


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
QA_DIR = LANGUAGE_MODEL_ROOT / "data" / "raw" / "synthetic_qa"
OUTPUT_PATH = QA_DIR / "zh_qa_generated_3000.json"
TARGET_TOTAL_QA = 3000


TOPICS = [
    ("AI", "让计算机表现出类似人类智能能力的技术方向", "常见能力包括识别、预测、生成、规划和问答", "ai"),
    ("人工智能", "研究如何让机器完成智能任务的领域", "它包括机器学习、深度学习、自然语言处理和计算机视觉", "ai"),
    ("机器学习", "让模型从数据中学习规律的方法", "它通过训练样本调整参数，而不是完全依赖手写规则", "ml"),
    ("深度学习", "使用多层神经网络学习数据表示的方法", "它适合处理图像、语音、文本和复杂模式识别任务", "deep_learning"),
    ("神经网络", "由可训练参数、线性变换和非线性激活组成的模型", "训练过程会根据 loss 调整权重", "deep_learning"),
    ("语言模型", "根据上下文预测和生成文本的模型", "GPT 类模型通常通过预测下一个 token 来训练", "llm"),
    ("大语言模型", "在大量文本上训练的大规模语言模型", "它能进行文本生成、总结、问答和代码辅助", "llm"),
    ("Transformer", "基于 self-attention 的神经网络结构", "现代语言模型大量使用 Transformer block", "llm"),
    ("self-attention", "让每个 token 根据上下文聚合信息的机制", "它能建立词语、代码符号和长距离依赖之间的关系", "llm"),
    ("causal mask", "限制模型只能看当前位置和之前 token 的掩码", "它防止训练时偷看未来答案", "llm"),
    ("multi-head attention", "并行使用多个注意力头观察上下文的机制", "不同 head 可以关注不同关系", "llm"),
    ("LayerNorm", "稳定每层激活分布的归一化方法", "它能让深层 Transformer 更容易训练", "llm"),
    ("残差连接", "把子层输出和输入相加的结构", "它帮助梯度传播并减少深层网络训练困难", "llm"),
    ("FeedForward 网络", "Transformer block 中逐位置处理隐藏向量的 MLP", "它通常由 Linear、GELU 和 Linear 组成", "llm"),
    ("embedding", "把 token id 映射成向量的查表层", "模型后续所有计算都在向量表示上进行", "llm"),
    ("position embedding", "表示 token 在上下文中位置的向量", "没有位置信息时 attention 难以区分顺序", "llm"),
    ("tokenizer", "把文本转换为 token id 的组件", "它也负责把生成的 token id 解码回文本", "tokenizer"),
    ("字符级 tokenizer", "把每个普通字符当成一个 token 的 tokenizer", "它简单透明，但序列较长，学习效率较低", "tokenizer"),
    ("BPE tokenizer", "把高频文本片段合并为 token 的 tokenizer", "它通常比字符级 tokenizer 更高效", "tokenizer"),
    ("特殊 token", "用于表示结构边界或控制语义的 token", "例如 <|qa_start|> 和 <|qa_end|> 可以标记问答边界", "tokenizer"),
    ("unknown token", "表示词表中不存在字符或片段的 token", "大量 <unk> 会降低模型学习文本的能力", "tokenizer"),
    ("next-token prediction", "根据前文预测下一个 token 的训练任务", "自回归语言模型的训练核心就是这个目标", "training"),
    ("logits", "模型对词表中每个 token 给出的未归一化分数", "softmax 会把 logits 转成概率分布", "training"),
    ("softmax", "把一组分数转换成概率分布的函数", "概率越高表示模型越倾向选择对应 token", "training"),
    ("cross entropy", "衡量预测概率和真实目标差距的损失函数", "语言模型常用它训练下一个 token 预测", "training"),
    ("loss", "模型预测错误程度的数值指标", "训练目标是让 loss 逐步下降", "training"),
    ("反向传播", "根据 loss 计算每个参数梯度的过程", "优化器根据梯度更新模型权重", "training"),
    ("梯度", "loss 对参数变化的方向和大小", "梯度告诉优化器参数应该如何调整", "training"),
    ("AdamW", "训练 Transformer 常用的优化器", "它使用动量估计并解耦 weight decay", "training"),
    ("学习率", "控制每次参数更新步长的超参数", "太大会震荡，太小会训练很慢", "training"),
    ("batch_size", "每一步训练并行处理的样本数量", "它影响显存占用和梯度稳定性", "training"),
    ("block_size", "模型一次能看到的上下文 token 长度", "上下文越长，注意力计算开销越大", "training"),
    ("训练集", "用于更新模型参数的数据", "模型通过训练集学习文本规律", "dataset"),
    ("验证集", "训练过程中用于观察泛化的数据", "它不参与反向传播，常用于保存 best.pt", "dataset"),
    ("测试集", "训练完成后用于最终评估的数据", "它不应该频繁参与调参", "dataset"),
    ("过拟合", "模型在训练集很好但在新数据上变差的现象", "表现为 train_loss 下降而 valid_loss 不再改善", "training"),
    ("欠拟合", "模型连训练集规律都没学好的现象", "表现为 train_loss 和 valid_loss 都较高", "training"),
    ("checkpoint", "训练过程中的保存点", "它通常包含模型参数、优化器状态、step 和配置", "training"),
    ("best.pt", "验证集 loss 最好时保存的模型文件", "推理时通常优先使用它", "training"),
    ("latest.pt", "最近一次训练状态的模型文件", "它适合继续训练或恢复中断", "training"),
    ("auto-resume", "自动从 latest.pt 继续训练的机制", "它能避免每次重新随机初始化模型", "training"),
    ("early stopping", "验证集长期不改善时停止训练的策略", "它可以减少过拟合和无效训练时间", "training"),
    ("梯度裁剪", "限制梯度范数的训练稳定方法", "它能减少偶发梯度爆炸", "training"),
    ("推理", "使用训练好的模型生成结果的过程", "推理阶段不更新参数", "inference"),
    ("自回归生成", "每次生成一个 token 并追加到上下文的生成方式", "后续 token 会依赖前面已经生成的内容", "inference"),
    ("temperature", "控制采样随机性的参数", "低温更稳定，高温更多样但更容易乱", "inference"),
    ("top-k sampling", "只在概率最高的 k 个 token 中采样的方法", "它能减少低概率 token 带来的混乱输出", "inference"),
    ("中文问答数据", "以问题和回答形式组织的中文训练样本", "它能让模型学习用中文解释而不是只续写代码", "dataset"),
    ("代码解释数据", "让模型根据代码片段给出中文说明的数据", "它能训练模型用自然语言解释程序逻辑", "dataset"),
    ("错误诊断数据", "围绕报错信息和排查步骤构造的问答数据", "它能让模型学习调试思路", "dataset"),
    ("数据清洗", "删除低质量、乱码、重复和无关文本的过程", "干净数据通常比盲目增加训练步数更重要", "dataset"),
    ("UTF-8", "常用的 Unicode 文本编码", "统一编码可以减少中文乱码问题", "dataset"),
    ("JSON", "常见的数据交换格式", "它由对象、数组、字符串、数字和布尔值组成", "programming"),
    ("JSONL", "一行一个 JSON 对象的文本格式", "它适合存储大量训练样本", "programming"),
    ("Python", "常用的高级编程语言", "它在数据处理、AI 训练和脚本自动化中很常见", "python"),
    ("PyTorch", "深度学习框架", "它提供 tensor、自动求导、神经网络模块和 GPU 加速", "pytorch"),
    ("tensor", "多维数组对象", "模型输入、权重和激活值通常都是 tensor", "pytorch"),
    ("torch.no_grad", "关闭梯度记录的 PyTorch 上下文", "推理和验证时使用它可以节省显存", "pytorch"),
    ("model.train", "让模型进入训练模式的方法", "dropout 等层会启用训练行为", "pytorch"),
    ("model.eval", "让模型进入评估模式的方法", "推理和验证时应关闭训练随机性", "pytorch"),
    ("CUDA", "NVIDIA GPU 并行计算平台", "PyTorch 可以通过 CUDA 使用显卡加速训练", "cuda"),
    ("显存不足", "GPU 内存不够导致训练或推理失败的问题", "可以减小 batch_size、block_size 或模型规模", "cuda"),
    ("C++", "常用于系统、图形和高性能计算的编程语言", "它强调类型、内存和性能控制", "cpp"),
    ("std::vector", "C++ 标准库中的动态数组容器", "它可以运行时扩容并管理连续内存", "cpp"),
    ("指针", "保存内存地址的变量", "它可以为空，也可以指向不同对象", "cpp"),
    ("引用", "对象的别名", "它通常必须初始化并绑定到有效对象", "cpp"),
    ("RAII", "把资源生命周期绑定到对象生命周期的 C++ 思想", "构造获取资源，析构释放资源", "cpp"),
    ("智能指针", "自动管理动态对象生命周期的 C++ 工具", "unique_ptr 表示独占，shared_ptr 表示共享", "cpp"),
    ("CMake", "跨平台构建系统生成工具", "它根据 CMakeLists.txt 生成实际构建配置", "cpp"),
    ("Git", "分布式版本控制系统", "它用于跟踪代码历史和协作开发", "programming"),
    ("单元测试", "验证小范围代码行为的自动化测试", "它能防止改动破坏已有逻辑", "programming"),
    ("TDD", "先写失败测试再实现功能的开发方法", "它让需求和边界更清楚", "programming"),
    ("REST API", "基于 HTTP 资源和方法组织接口的风格", "常见方法包括 GET、POST、PUT 和 DELETE", "backend"),
    ("前端组件", "封装界面和交互逻辑的可复用单元", "组件通常包含 props、state 和事件", "frontend"),
    ("TypeScript", "带静态类型的 JavaScript 超集", "大型前端项目常用它提升可维护性", "frontend"),
    ("Vue", "用于构建前端界面的 JavaScript 框架", "它通过组件、响应式状态和模板组织应用", "frontend"),
    ("WebGL", "浏览器中的 GPU 图形 API", "它可以绘制 2D 和 3D 图形", "web3d"),
    ("Three.js", "封装 WebGL 的 3D 图形库", "它提供场景、相机、材质、几何体和渲染器", "web3d"),
    ("mesh", "由顶点、边和面组成的几何网格", "3D 渲染中模型通常以 mesh 表示", "web3d"),
    ("shader", "运行在 GPU 上的着色程序", "它控制顶点变换和像素颜色", "web3d"),
    ("法线", "垂直于表面的方向向量", "光照计算常用法线判断表面朝向", "web3d"),
    ("矩阵变换", "用矩阵表达平移、旋转、缩放和投影", "3D 图形中会组合多个矩阵完成坐标转换", "math"),
    ("点乘", "衡量两个向量方向相似度的运算", "它常用于投影和光照夹角计算", "math"),
    ("叉乘", "得到垂直于两个向量的新向量的运算", "它常用于计算法线和坐标轴", "math"),
    ("时间复杂度", "描述算法运行时间随输入规模增长的趋势", "常见表示有 O(1)、O(n) 和 O(n log n)", "algorithm"),
    ("递归", "函数直接或间接调用自身的方法", "递归必须有明确终止条件", "algorithm"),
    ("哈希表", "通过哈希函数快速定位 key 的数据结构", "它通常能接近 O(1) 查找", "algorithm"),
    ("栈", "后进先出的数据结构", "函数调用和撤销操作常用栈思想", "algorithm"),
    ("队列", "先进先出的数据结构", "任务调度和广度优先搜索常用队列", "algorithm"),
    ("二叉树", "每个节点最多有两个子节点的树结构", "它常用于搜索、排序和层级表达", "algorithm"),
    ("动态规划", "保存子问题结果以避免重复计算的方法", "它适合重叠子问题和最优子结构", "algorithm"),
]

QUESTION_PATTERNS = [
    ("definition", "什么是{name}？"),
    ("definition", "请解释一下{name}。"),
    ("definition", "{name}是什么意思？"),
    ("definition", "能不能用中文说明{name}？"),
    ("definition", "我想知道{name}是什么。"),
    ("purpose", "{name}有什么作用？"),
    ("purpose", "为什么要学习{name}？"),
    ("purpose", "{name}在编程里有什么用？"),
    ("purpose", "{name}解决什么问题？"),
    ("purpose", "{name}适合用在什么场景？"),
    ("example", "能举例说明{name}吗？"),
    ("example", "请给一个{name}的简单例子。"),
    ("example", "{name}在实际项目中怎么体现？"),
    ("compare", "{name}和普通写代码有什么关系？"),
    ("compare", "{name}和模型训练有什么关系？"),
    ("debug", "如果{name}相关结果不对，应该怎么排查？"),
    ("debug", "{name}常见问题是什么？"),
    ("debug", "使用{name}时容易犯什么错误？"),
    ("learn", "初学者应该怎么理解{name}？"),
    ("learn", "学习{name}应该先抓住哪一点？"),
    ("learn", "能用更直白的话解释{name}吗？"),
    ("qa", "用户问到{name}时，模型应该怎么回答？"),
    ("qa", "如何用问答形式解释{name}？"),
    ("qa", "请用一段中文回答{name}相关问题。"),
    ("short", "用一句话解释{name}。"),
    ("short", "简单说说{name}。"),
    ("detail", "请稍微详细地解释{name}。"),
    ("detail", "{name}的核心思想是什么？"),
    ("detail", "{name}背后的原理是什么？"),
    ("warning", "{name}有什么需要注意的地方？"),
    ("warning", "为什么{name}不能只看表面？"),
    ("training", "{name}对训练语言模型有什么帮助？"),
    ("training", "训练小语言模型时，{name}为什么重要？"),
    ("inference", "推理阶段如何看待{name}？"),
    ("dialogue", "如果我说不懂{name}，你应该怎么解释？"),
    ("dialogue", "请像老师一样解释{name}。"),
]


def count_existing_items() -> int:
    total = 0
    for path in QA_DIR.glob("*.json"):
        if path.resolve() == OUTPUT_PATH.resolve():
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError(f"QA JSON must be a list: {path}")
        total += len(raw)
    return total


def build_answer(name: str, definition: str, detail: str, tag: str, mode: str) -> str:
    if mode == "definition":
        return f"{name}是{definition}。{detail}。理解它时先抓住概念本身，再看它在训练、推理或工程中的具体作用。"
    if mode == "purpose":
        return f"{name}的作用是帮助我们处理或理解{tag}相关问题。{detail}。在学习阶段，不要只背术语，要把它和输入、输出、数据流联系起来。"
    if mode == "example":
        return f"举例来说，讨论{name}时可以先问它的输入是什么、输出是什么、解决什么问题。{detail}。这样比只记名字更容易真正理解。"
    if mode == "compare":
        return f"{name}和编程实践是相关的。编程强调明确规则和流程，而{name}强调从数据、结构或上下文中抽象规律。两者结合后才能构建可运行的 AI 系统。"
    if mode == "debug":
        return f"排查{name}相关问题时，先确认输入数据是否正确，再确认格式、参数和运行环境。{detail}。不要直接猜结论，要用最小样例逐步定位。"
    if mode == "learn":
        return f"初学{name}时，可以把它理解成：{definition}。先掌握它解决什么问题，再看代码实现和训练日志。这样学习路径更清晰。"
    if mode == "qa":
        return f"用户问到{name}时，模型应该先给出中文定义，再解释用途和注意点。例如：{name}是{definition}，{detail}。"
    if mode == "short":
        return f"{name}可以简单理解为{definition}，核心作用是帮助处理{tag}相关任务。"
    if mode == "detail":
        return f"{name}的核心思想是{definition}。{detail}。如果放在语言模型项目里，还要关注它如何影响数据、训练、loss 或推理结果。"
    if mode == "warning":
        return f"学习{name}时要避免只记术语。{detail}。更好的做法是结合一个小例子，观察输入、输出和中间状态。"
    if mode == "training":
        return f"训练小语言模型时，{name}能帮助我们理解{tag}相关现象。{detail}。它会影响模型学到什么、怎么收敛以及最终回答是否稳定。"
    if mode == "inference":
        return f"推理阶段看待{name}时，要关注它如何影响模型生成。{detail}。如果输出不稳定，应同时检查训练数据、采样参数和 checkpoint。"
    if mode == "dialogue":
        return f"如果你不懂{name}，我会先用中文解释：它是{definition}。然后再补一句用途：{detail}。最后可以给一个小例子帮助理解。"
    raise ValueError(f"Unknown answer mode: {mode}")


def generate_items(target_count: int) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    serial = 1
    for topic_index, (name, definition, detail, tag) in enumerate(TOPICS):
        for pattern_index, (mode, question_pattern) in enumerate(QUESTION_PATTERNS):
            if len(items) >= target_count:
                return items
            question = question_pattern.format(name=name)
            answer = build_answer(name, definition, detail, tag, mode)
            items.append(
                {
                    "source": f"synthetic_zh_qa_3000/{serial:04d}",
                    "language": "zh+en",
                    "kind": "synthetic_learning_qa",
                    "question": question,
                    "answer": answer,
                    "tags": [tag, mode, "zh_qa", "generated_stage1"],
                    "topic_index": topic_index,
                    "pattern_index": pattern_index,
                }
            )
            serial += 1
    if len(items) < target_count:
        raise RuntimeError(f"Not enough topic/pattern combinations: generated {len(items)}, need {target_count}")
    return items


def main() -> int:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    existing_count = count_existing_items()
    target_generated_count = max(TARGET_TOTAL_QA - existing_count, 0)
    items = generate_items(target_generated_count)
    OUTPUT_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(
        {
            "existing_qa_count_excluding_generated": existing_count,
            "generated_qa_count": len(items),
            "target_total_qa": TARGET_TOTAL_QA,
            "output": str(OUTPUT_PATH),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
