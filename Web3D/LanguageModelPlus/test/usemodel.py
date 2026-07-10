import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
model_dir = r"D:/YueShaoPu/Web3D/LanguageModelPlus/models/DeepSeek-R1-Distill-Qwen-7B"
#从本地路径下加载模型的分词器token映射表，local_files_only:强制从本地读取
tokenizer = AutoTokenizer.from_pretrained(model_dir,local_files_only=True)
#从本地加载模型，local_files_only=True 强制离线模式，精度加载权重，显存不足时候的处理
model = AutoModelForCausalLM.from_pretrained(model_dir, local_files_only=True,
 dtype=torch.float16,device_map="auto")
#把模型设置为推理模式，而不是训练模式
model.eval()
messages = [
    {"role": "user", "content": "你好，请用中文解释一下什么是 Transformer。"}
]
#对话数据转为模型网络输入数据，不进行分词(是否序列化输入字符串为id形式)，让ai以回答用户的问题的方法来回答
prompt = tokenizer.apply_chat_template(messages,
                                       tokenize= False,add_generation_prompt=True)
#把分词转为pytorch张量，并把张量移动到模型所在的设备上,return_tensors="pt"以张量形式返回，把张量移动到模型所在的设备上
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
#推理过程不进行梯度计算，减少数据的存储开销
#最大生成512Token,do_sample 随机采样，不一定选择最高的token，temperature随机温度，越大越有创造力，
#top_p 从质量最高的累计概率达到90%的token中采样，禁止模型瞎采样,eos_token_id指定模型的结束符
with torch.no_grad():
     output_ids = model.generate(
        **inputs,
        max_new_tokens=512,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        eos_token_id=tokenizer.eos_token_id,
    )
#获取到输出的token
response_ids = output_ids[0][inputs["input_ids"].shape[-1]:] 
#解码token,在解码的时候跳过特殊的token
response = tokenizer.decode(response_ids, skip_special_tokens=True)
print(response)