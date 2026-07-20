import litellm
class ModelApi:
    def chat(self,model: str, api_key: str, message: str):
        response = litellm.completion(
            model = model,
            messages = [{"role": "user", "content": message}],
            temperature=0.6,
            api_key = api_key
        )
        print(response.choices[0].message.content)
    async def chat_stream(self, model: str, api_key: str, message: str):
        response  = await litellm.acompletion(
            model = model,
            messages = [{"role": "user", "content": message}],
            temperature=0.6,
            api_key = api_key,
            stream=True
        )
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content #逐步返回
modelApi = ModelApi()