# from zai import ZhipuAiClient
# # 初始化客户端
# client = ZhipuAiClient(api_key="5a42c59072ee4983b9da2456c3b35343.MOiVpKzHuitSmd2T")
# response = client.chat.completions.create(
#      model="glm-5.2",
#       messages=[
#         {
#             "role": "system",
#             "content": "你是一个有用的AI助手。"
#         },
#         {
#             "role": "user",
#             "content": "你好，请介绍一下自己。"
#         }
#     ],
#     temperature=0.6
# )
# # 获取回复
# print(response.choices[0].message.content)
import Server.server as server
if __name__ == "__main__":
    server.run()