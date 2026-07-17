import litellm
class ModelApi:
    def chat(self,model,api_key,message):
        response = litellm.completion(
            model = model,
            messages = [{"role": "user", "content": message}],
            temperature=0.6,
            api_key = api_key
        )
        print(response.choices[0].message.content)

modelApi = ModelApi()