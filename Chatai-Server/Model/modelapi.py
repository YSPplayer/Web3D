import litellm
import asyncio
class ModelApi:
    def get_token_count(self,model:str,message: str):
        return litellm.token_counter(
        model=model,
        text=message
    )
    def build_messages(self,user_message:str,history_messages:dict):
        model_messages = []
        for item in history_messages:
            model_messages.append({
                "role": item["role"],
                "content": item["content"]
            })
        model_messages.append({
            "role": "user",
            "content": user_message
        })
        return model_messages

    def chat(self,model: str, api_key: str, message: str):
        response = litellm.completion(
            model = model,
            messages = [{"role": "user", "content": message}],
            temperature=0.6,
            api_key = api_key
        )
        print(response.choices[0].message.content)
    
    async def chat_stream(self, model: str, api_key: str, message: list[dict]):
        response = None
        try:
            response  = await litellm.acompletion(
                model = model,
                messages = message,
                temperature=0.6,
                api_key = api_key,
                stream=True
            )
            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content #逐步返回
        except asyncio.CancelledError: #用户取消模型生成
            print("模型流式生成已取消")
            raise
        finally:
            close = getattr(response, "aclose", None)
            if close:
                await close()
modelApi = ModelApi()