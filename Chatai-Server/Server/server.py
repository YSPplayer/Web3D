from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import json
from Config.config import config
import uvicorn
import mimetypes
from Data.db_manager import db_manager
from Model.key import key
from Model.modelapi import modelApi
from datetime import datetime
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 服务启动,初始化数据库
    db_manager.init_db()
    try:
        yield
    finally:
        # 服务关闭，例如 Ctrl+C、正常停止 Uvicorn
        db_manager.close_db()
app = FastAPI(title="Chat API",lifespan=lifespan)
# 重要：允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # 开发环境允许所有，生产环境要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run():
    uvicorn.run("Server.server:app", host=config.server_ip, port=config.server_port, reload=False)
# ---- API 接口 ----
#请求体模型
class UserRegister(BaseModel):
    username:str
    password:str
class ModelConfig(BaseModel):
    userid:int
    modeltype:str
    modelname:str
    apikey:str
    isonline:int

class Conversation(BaseModel):
    userid: int
    modelconfigid: int
    title: str

class ChatMessage(BaseModel):
    userid: int
    modelconfigid: int
    conversationid:int
    message:str   

def success(message:str = "成功",data:any = None) ->dict:
    return {
        "code": 200,
        "message": message,
        "data": data or {}
    }
def error(message: str = "操作失败", code: int = 400) ->dict:
    return {
         "code": code,
         "detail": message
    }
def check_result(result:dict):
    if "code" in result:
        if result["code"] == 409:
            raise HTTPException(
                status_code=409,
                detail="账号已经存在"
            )
        elif result["code"] == 401:
             raise HTTPException(
                status_code=409,
                detail="账号或密码不正确"
            )
        elif result["code"] == 500:
            raise HTTPException(
                status_code=500,
                detail="数据库写入失败"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="数据库操作失败"
            )
def image_to_data_url(logo_path: str)-> str:
    # 数据库中是 /logo/glm.svg，去掉开头的斜杠
    relative_path = logo_path.lstrip("/\\")
    logo_root = (config.db_path / "images").resolve() 
    image_path = (logo_root / relative_path).resolve()
    if not image_path.is_relative_to(logo_root):
        return ""
    if not image_path.is_file():
        print(f"模型Logo不存在：{image_path}")
        return ""
    mime_type, _ = mimetypes.guess_type(image_path.name)
    mime_type = mime_type or "application/octet-stream"
    image_bytes = image_path.read_bytes()
    encoded = key.img_bytes_to_base64(image_bytes)
    return f"data:{mime_type};base64,{encoded}"
##get
@app.get("/chatai/health")
async def health():
    return success("服务器访问正常")

@app.get("/chatai/models") #获取到当前后端存储的所有类别的模型
async def models():
    models = db_manager.get_models()
    check_result(models)
    logo_cache = {}
    for model in models:
        logo_path = model.get("logo_path")
        if not logo_path:
            model["logo_path"] = ""
            continue
        if logo_path not in logo_cache:
            logo_cache[logo_path] = image_to_data_url(logo_path)
        model["logo_path"] = logo_cache[logo_path]
    return success("模型数据查询成功！",models)

@app.get("/chatai/user/chatMessages") #获取当前模型的会话记录
async def get_model_chat_message(conversationid:int):
    messages = db_manager.get_messages(conversationid)
    check_result(messages)
    if not messages:
        return success("当前会话中的消息不存在！")
    else:
         return  success("当前会话消息查询成功！",messages)
    
    
@app.get("/chatai/user/modelConfgState") #获取到模型配置
async def get_model_config_state(userid:int,
            modeltype:str,modelname:str):
    config_state = db_manager.get_model_config_state_by_user_par(userid,
                    modeltype,modelname)
    check_result(config_state)
    if not config_state:
        return success("当前用户模型配置数据不存在！")
    else:
        return  success("当前用户模型配置查询成功！",{
            "apikey":key.string_to_base64(key.decrypt_api_key(config_state["api_key"])),
            "isonline":config_state["is_online"],
            "logo":image_to_data_url(config_state["logo_path"])
        })

@app.get("/chatai/user/modelConfg") #获取到当前用户的模型配置
async def get_user_model_config(userid:int):
    config = db_manager.get_model_config_by_userid(userid)
    check_result(config)
    if not config:
        return success("当前用户模型配置数据不存在！")
    else:
        return success("当前用户模型配置查询成功！",{
            "apikey":key.string_to_base64(key.decrypt_api_key(config["api_key"])),
            "isonline":config["is_online"],
            "modeltype":config["model_type"],
            "modelname": config["model_name"],
            "modelconfigid":config["id"],
            "logo":image_to_data_url(config["logo_path"])
        })

@app.get("/chatai/user/getConversation")
async def get_conversation(userid:int,modelconfigid:int):
    result = db_manager.get_conversation(userid,modelconfigid)
    check_result(result)
    if not result:
        return success("当前用户会话记录不存在！")
    else:
        return success("当前用户会话记录查询成功！",result)
##put
@app.put("/chatai/saveModelConfig")
async def save_model_config(config:ModelConfig):
    encrypted_api_key = key.encrypt_api_key(
       key.base64_to_string(config.apikey)
    )
    result = db_manager.create_model_config(
        config.userid,config.modeltype,
        config.modelname,encrypted_api_key,
        config.isonline
    )
    check_result(result)
    return success("配置保存成功",{
        "userid": result["user_id"]
    })

##post
@app.post("/chatai/user/conversation")
async def create_conversation(conversation:Conversation):
    result = db_manager.create_conversation(conversation.userid,conversation.modelconfigid,conversation.title)
    check_result(result)
    return success("会话新建成功！",{
        "conversationid": result["conversation_id"]
    })

@app.post("/chatai/user/chat")
async def create_chat_message(chatMessage:ChatMessage):
    user_message = chatMessage.message.strip()
    # 必须在流开始前完成参数校验
    if not user_message:
        raise HTTPException(
            status_code=400,
            detail="消息不能为空"
        )
    model_name = "zai/glm-5.2"
    api_key = "5a42c59072ee4983b9da2456c3b35343.MOiVpKzHuitSmd2T"
    user_tokens_used = modelApi.get_token_count(model_name,
    user_message)
    # 先保存用户消息
    user_result = db_manager.create_messages(
        chatMessage.conversationid,"user",
        user_message,user_tokens_used)
    check_result(user_result)
    user_created_at = user_result["created_at"]
    async def generate():
        full_content: list[str] = []
        try:
            async for content in modelApi.chat_stream(
                model_name,
                api_key,
                user_message
            ):
                full_content.append(content)
                yield json.dumps(
                    {
                        "type": "delta",
                        "content": content
                    },
                    ensure_ascii=False
                ) + "\n"
            ai_message = "".join(full_content)
            # 把完整 AI 消息存入数据库
            user_tokens_used = modelApi.get_token_count(model_name,
            ai_message)
            # 先保存用户消息
            ai_result = db_manager.create_messages(
                chatMessage.conversationid,"assistant",
                ai_message,user_tokens_used)
            check_result(ai_result)
            yield json.dumps(
                {
                    "type": "done",
                    "user_created_at":user_created_at,
                    "ai_created_at":ai_result["created_at"]
                },
                ensure_ascii=False
            ) + "\n"
        except asyncio.CancelledError:
            # 前端断开或用户点击“停止生成”
            raise
        except Exception as exc:
            print(f"模型流式调用失败: {exc}")
            yield json.dumps(
                {
                    "type": "error",
                    "message": "模型生成失败"
                },
                ensure_ascii=False
            ) + "\n"
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/chatai/register")
async def register(user:UserRegister):
    #获取前端传输数据
    username = user.username.strip()
    password = user.password
    if not username:
        raise HTTPException(
            status_code=400,
            detail="账号不能为空"
        )
    # 1. 后端用 bcrypt 再加盐哈希（安全存储）
    result = db_manager.create_user(username, key.string_to_bcrypt_hash(password))
    check_result(result)
    return success("注册成功",{
                "username": result["username"]
    })

@app.post("/chatai/login")
async def login(user:UserRegister):
    #获取前端传输数据
    username = user.username.strip()
    password = user.password
    db_user = db_manager.get_user_by_username(username)
    check_result(db_user)
    if key.checkpw_bcrypt(password.encode(), db_user["password_hash"]):
            return success("登录成功",{
                "id": db_user["id"],
                "username": db_user["username"]
            })
    return error("登录失败，账号或密码不正确！",401)

