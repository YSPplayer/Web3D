from __future__ import annotations

import json
from pathlib import Path

from generate_stage1_zh_qa_3000 import TOPICS as TECH_TOPICS


LANGUAGE_MODEL_ROOT = Path(__file__).resolve().parents[1]
QA_DIR = LANGUAGE_MODEL_ROOT / "data" / "raw" / "synthetic_qa"
OUTPUT_PATH = QA_DIR / "zh_dialogue_qa_generated_6000.json"
TARGET_GENERATED_QA = 6000


DIALOGUE_CASES = [
    {
        "tag": "greeting",
        "questions": [
            "你好",
            "你好啊",
            "在吗？",
            "您好",
            "嗨",
            "哈喽",
            "早上好",
            "晚上好",
            "我来了",
            "开始吧",
            "可以聊天吗？",
            "先打个招呼",
        ],
        "answers": [
            "你好，我在。你可以直接问我编程、AI、训练流程或代码解释相关的问题。",
            "你好。现在可以继续提问，如果问题比较短，我会先确认你的意图再回答。",
            "在的。你可以问一个具体问题，比如 AI 是什么、代码为什么报错，或者模型训练怎么调整。",
            "你好，我会尽量用中文回答，并且避免无关代码片段。",
            "你好。为了回答更准确，你可以把问题、报错或代码片段一起发出来。",
            "你好，我们可以继续。你想先聊模型训练、推理结果，还是编程概念？",
            "你好。你问得越具体，我越容易给出有针对性的解释。",
            "你好，我会优先给出直接答案，再补充必要原因。",
            "你好。如果我理解错了，你可以说“重新回答”或“不要输出代码”。",
            "你好。请告诉我你想解决的问题，我会按步骤分析。",
            "你好。当前目标如果是学习原理，我会尽量解释输入、输出和中间过程。",
            "你好。我们可以从一个小问题开始，然后逐步展开。",
        ],
    },
    {
        "tag": "wrong_answer",
        "questions": [
            "你答非所问",
            "你真的答非所问",
            "你没回答我的问题",
            "这不是我要的答案",
            "你理解错了",
            "你跑题了",
            "你在说什么？",
            "别乱回答",
            "你这个回答不对",
            "你没有懂我的意思",
            "你又开始胡说了",
            "这个答案和问题没关系",
        ],
        "answers": [
            "你说得对，这种情况应该先回到你的原问题。我需要根据问题本身重新组织答案，而不是继续套用训练语料里的其他模板。",
            "是的，这属于答非所问。更好的做法是先判断问题类型，再给对应回答；如果信息不足，就应该追问，而不是生成无关内容。",
            "我需要重新对齐你的问题。请把你真正想问的点再说一遍，我会先给结论，再解释原因。",
            "这个反馈说明模型没有正确匹配问题和答案。可以通过增加纠错对话、自然问答和反模板数据来改善。",
            "我理解错了。正确处理方式是承认偏差，并请求你补充上下文或让我重新回答。",
            "确实跑题了。回答应该围绕你的问题，不应该突然切换到无关概念、代码或模板句式。",
            "这种回答质量不好。对于小模型来说，常见原因是训练数据模板重复、问答对不够自然、模型容量较小。",
            "收到，我应该停止无关续写，重新根据你的问题作答。",
            "你指出的问题是有效的。下一步应该检查数据集中是否有足够的“用户纠错 -> 模型修正回答”的样本。",
            "我没有理解你的意思时，应该先澄清，而不是装作已经理解。",
            "如果回答明显不相关，应该降低采样随机性，并继续补充更自然的中文问答数据。",
            "这个答案不合格。一个合格回答应当直接回应问题，并保持中文解释风格稳定。",
        ],
    },
    {
        "tag": "continue",
        "questions": [
            "然后呢",
            "继续",
            "接着说",
            "再说详细一点",
            "继续往下讲",
            "后面怎么做？",
            "下一步是什么？",
            "再展开讲讲",
            "还需要做什么？",
            "能继续分析吗？",
            "讲完了吗？",
            "请继续解释",
        ],
        "answers": [
            "下一步要先明确你当前问题的上下文。如果是在训练模型，就看 loss、数据比例和推理效果；如果是在问代码，就看输入、输出和错误位置。",
            "可以继续。一般我会先总结前面的结论，再给出后续操作，而不是突然切换到无关主题。",
            "接着说，重点是把问题拆成几个可验证的小点，逐个确认，而不是一次性猜很多原因。",
            "如果你问的是模型效果，后面要看数据质量、采样参数、checkpoint 选择和训练是否过拟合。",
            "下一步取决于目标：想提升中文问答，就补自然对话数据；想提升编程能力，就补代码解释和错误诊断数据。",
            "继续分析时，要先看当前现象，再判断它是数据问题、模型问题、训练问题还是推理参数问题。",
            "后续可以先做一个小实验，固定问题输入，比较不同 checkpoint 和 temperature 下的输出。",
            "还需要检查模型是不是加载了正确的 best.pt，而不是旧 tokenizer 对应的 checkpoint。",
            "如果前面的回答不清楚，我可以换一种更直白的方式重新讲。",
            "继续时不要急着扩大模型，先确认数据格式和问答样本是否真的符合目标行为。",
            "还没讲完的话，应该沿着当前主题继续，不应该生成无关代码。",
            "可以，我会继续围绕你的问题展开。",
        ],
    },
    {
        "tag": "no_code",
        "questions": [
            "不要输出代码",
            "别给我代码",
            "先别写代码",
            "只用中文解释",
            "不要贴源码",
            "先讲原理",
            "别生成代码块",
            "用自然语言说明",
            "不要用 markdown 代码块",
            "我只想听分析",
            "先回答概念",
            "不要跑去写程序",
        ],
        "answers": [
            "可以，我先不用代码，只用中文解释概念和原因。",
            "收到。我会先讲清楚思路，不贴源码。",
            "好的，先分析原理：我们关注输入是什么、输出是什么、为什么会出现这个现象。",
            "可以。对于当前问题，我会避免代码块，直接给出中文说明。",
            "明白。你现在需要的是分析，不是实现。",
            "我会先说结论，再解释理由，不生成无关代码。",
            "可以先不写代码。等你确认方案后，再进入实现。",
            "我会用自然语言说明，并尽量把关键概念讲清楚。",
            "收到，不使用 markdown 代码块，只给分析。",
            "好的，我会围绕问题本身解释，不跳到源码续写。",
            "先讲概念是合理的，尤其是在学习模型原理时。",
            "我不会直接写程序，会先把判断依据说明白。",
        ],
    },
    {
        "tag": "reanswer",
        "questions": [
            "重新回答",
            "换个说法",
            "说简单点",
            "讲人话",
            "你再解释一遍",
            "用更直白的话说",
            "别绕弯子",
            "重新组织一下",
            "给我一个简短版本",
            "详细版也说一下",
            "我没听懂",
            "能不能更清楚一点？",
        ],
        "answers": [
            "可以。简单说，就是先看问题属于哪一类，再给对应回答；不要把无关训练样本里的句子拼进来。",
            "换句话说，模型现在需要学会匹配问题和答案，而不仅仅是学会中文句式。",
            "直白讲，就是数据要更像真实用户提问，答案要更像真实助手回复。",
            "简单版：你的问题是什么，我就应该围绕那个问题回答，不应该突然说别的概念。",
            "更清楚地说，当前目标是让模型先学会中文对话的基本秩序。",
            "可以重新解释：如果问题短，我应该先确认；如果问题明确，我应该直接回答。",
            "不绕弯子：答非所问通常是数据和训练目标没有对齐。",
            "重新组织后，结论是：补自然对话、纠错样本和高质量问答比继续堆源码更重要。",
            "简短版本：先让模型学会正常中文对话，再谈复杂编程推理。",
            "详细版：需要覆盖问候、追问、纠错、拒绝无关输出、概念解释和代码解释等场景。",
            "你没听懂时，我应该降低抽象程度，用更小的例子说明。",
            "可以更清楚：我会把答案拆成结论、原因和下一步。",
        ],
    },
    {
        "tag": "unknown",
        "questions": [
            "你不知道就说不知道",
            "不确定可以直说",
            "别瞎编",
            "如果没把握怎么办？",
            "你能保证吗？",
            "这个你确定吗？",
            "不要强行回答",
            "信息不够怎么办？",
            "如果问题不完整呢？",
            "你应该追问吗？",
            "你不知道答案怎么办？",
            "别装懂",
        ],
        "answers": [
            "如果信息不足，正确做法是说明不确定，并指出需要补充哪些上下文。",
            "可以，不确定时应该直说，而不是编造看似完整的答案。",
            "我不应该瞎编。对于缺少上下文的问题，应先追问或给出条件化分析。",
            "没把握时，可以说“根据当前信息，我只能推测”，再列出需要验证的点。",
            "不能保证时就不应该说得过满。技术分析要区分事实、推测和建议。",
            "如果不确定，我应该说明依据不足，并给出检查方法。",
            "不应该强行回答。强行生成会让用户误以为模型真的理解了。",
            "信息不够时，应该问清楚输入、输出、报错、环境和目标。",
            "问题不完整时，先澄清比乱答更可靠。",
            "是的，必要时应该追问，而不是直接生成无关内容。",
            "不知道答案时可以坦率说明，然后给出可验证的排查路径。",
            "不能装懂。对学习型模型来说，承认不确定比胡乱续写更好。",
        ],
    },
]


TOPIC_QUESTION_STYLES = [
    "我想问一下，{name}到底是什么意思？",
    "{name}能不能用普通话解释？",
    "请不要套模板，直接解释{name}。",
    "如果我是初学者，应该怎么理解{name}？",
    "请用两三句话说明{name}。",
    "{name}和我现在的项目有什么关系？",
    "为什么学习语言模型时会遇到{name}？",
    "{name}容易和什么概念混淆？",
    "能不能先讲{name}的作用，再讲注意点？",
    "如果{name}相关结果不对，可能是什么原因？",
    "请从输入和输出角度解释{name}。",
    "请用一个实际开发场景说明{name}。",
    "如果我要调试{name}相关问题，应该先看哪里？",
    "{name}对中文问答模型有什么影响？",
    "用一句比较自然的话解释{name}。",
    "请像老师一样讲{name}。",
    "请像代码审查一样分析{name}。",
    "请给{name}一个清晰定义。",
    "为什么不能只背{name}这个词？",
    "怎么判断自己是否理解了{name}？",
    "{name}在训练阶段有什么意义？",
    "{name}在推理阶段有什么意义？",
    "如果用户问{name}，助手应该怎么答？",
    "请纠正我对{name}的误解。",
    "请用中文回答：{name}是什么？",
]


def topic_answer(name: str, definition: str, detail: str, tag: str, style_index: int) -> str:
    variants = [
        f"{name}可以理解为{definition}。{detail}。如果只记名字，不看它解决的问题，就很容易在实际项目里用错。",
        f"直白地说，{name}就是{definition}。它的重要点在于：{detail}。学习时建议结合一个小例子观察输入和输出。",
        f"先给结论：{name}是{definition}。在你的语言模型项目里，它和{tag}相关，核心是帮助你判断模型为什么这样训练或生成。",
        f"不要把{name}当成孤立术语。它本质上是{definition}，实际作用是让我们更好地处理{tag}中的具体问题。",
        f"如果从工程角度看，{name}关注的是：{definition}。{detail}。排查问题时可以先确认数据、参数和运行阶段。",
        f"可以这样记：{name}不是玄学，它指{definition}。理解它以后，再看训练日志、推理输出或代码结构会更清楚。",
        f"初学时先抓一句话：{name}是{definition}。然后再看它为什么有用：{detail}。",
        f"在问答模型里，解释{name}时应该先定义，再举用途，最后说限制。定义是：{definition}。用途是：{detail}。",
        f"如果{name}相关结果不对，通常要检查上下文是否完整、数据是否匹配、参数是否合理。因为{name}本身涉及{definition}。",
        f"更自然地说，{name}就是帮助我们理解或处理{tag}问题的一种概念。它的核心含义是{definition}。",
    ]
    return variants[style_index % len(variants)]


def append_item(items: list[dict[str, object]], question: str, answer: str, tag: str) -> None:
    serial = len(items) + 1
    items.append(
        {
            "source": f"synthetic_dialogue_zh_qa_6000/{serial:04d}",
            "language": "zh+en",
            "kind": "synthetic_learning_qa",
            "question": question,
            "answer": answer,
            "tags": [tag, "dialogue_or_natural_qa", "zh_qa", "generated_stage1"],
        }
    )


def generate_dialogue_items(items: list[dict[str, object]]) -> None:
    for case in DIALOGUE_CASES:
        tag = str(case["tag"])
        for question in case["questions"]:
            for answer in case["answers"]:
                append_item(items, str(question), str(answer), tag)
                if len(items) >= TARGET_GENERATED_QA:
                    return


def generate_topic_items(items: list[dict[str, object]]) -> None:
    style_index = 0
    while len(items) < TARGET_GENERATED_QA:
        for name, definition, detail, tag in TECH_TOPICS:
            for question_style in TOPIC_QUESTION_STYLES:
                question = question_style.format(name=name)
                answer = topic_answer(name, definition, detail, tag, style_index)
                append_item(items, question, answer, str(tag))
                style_index += 1
                if len(items) >= TARGET_GENERATED_QA:
                    return


def generate_items() -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    generate_dialogue_items(items)
    generate_topic_items(items)
    if len(items) != TARGET_GENERATED_QA:
        raise RuntimeError(f"generated {len(items)}, expected {TARGET_GENERATED_QA}")
    return items


def main() -> int:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    items = generate_items()
    OUTPUT_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"generated_qa_count": len(items), "output": str(OUTPUT_PATH)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
