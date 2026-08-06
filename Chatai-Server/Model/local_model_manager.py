import gc
import threading
import torch
from Config.config import config
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
class LocalModelManager:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.status = "stopped"  # stopped / starting / ready / error
        self.error = ""
        self.lock = threading.RLock()
        self.model_path = config.local_model_path / "DeepSeek-R1-Distill-Qwen-7B"

    def get_status(self): #获取到模型状态
        return {
            "status": self.status,
            "error": self.error
        }
    
    def start(self):
        with self.lock:
            if self.status == "ready":
                return {"code": 200, "message": "模型已经启动"}
            if self.status == "starting":
                return {"code": 200, "message": "模型正在启动"}
            
            self.status = "starting"
            self.error = "" 
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                local_files_only=True
                )
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    local_files_only=True,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
                model.eval()
                with self.lock:
                    self.tokenizer = tokenizer
                    self.model = model
                    self.status = "ready"
                return {"code": 200, "message": "模型启动成功"}
            except Exception as exc:
                with self.lock:
                    self.status = "error"
                    self.error = str(exc)
                return {
                    "code": 500,
                    "message": f"模型启动失败: {exc}"
                }
            
    def stop(self):
        with self.lock:
            self.model = None
            self.tokenizer = None
            self.status = "stopped"
            self.error = ""
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
            return {"code": 200, "message": "模型已关闭"}
    
    def chat_stream(self, messages: list[dict]):
        with self.lock:
            if self.status != "ready" or self.model is None or self.tokenizer is None:
                raise RuntimeError("本地模型未启动")
            model = self.model
            tokenizer = self.tokenizer

        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        streamer = TextIteratorStreamer(
            tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )

        generation_kwargs = {
            **inputs,
            "streamer": streamer,
            "max_new_tokens": 1024,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9,
            "eos_token_id": tokenizer.eos_token_id
        }

        thread = threading.Thread(
            target=model.generate,
            kwargs=generation_kwargs
        )
        thread.start()

        for text in streamer:
            if text:
                yield text

local_model_manager = LocalModelManager()