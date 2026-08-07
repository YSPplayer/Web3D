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
from Model.local_model_manager import local_model_manager
from System.system_monitor import system_monitor
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 服务启动,初始化数据库
    db_manager.init_db()
    await system_monitor.start()
    try:
        yield
    finally:
        await system_monitor.stop()
        # 服务关闭，例如 Ctrl+C、正常停止 Uvicorn
        db_manager.close_db()
        local_model_manager.stop()
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
    imgurl:str
class UserLogin(BaseModel):
    username:str
    password:str
class ModelConfig(BaseModel):
    userid:int
    modeltype:str
    modelname:str
    apikey:str
    proxyhost:str
    proxyport:int
    proxyactive:int

class Conversation(BaseModel):
    userid: int
    modelconfigid: int
    title: str

class ChatMessage(BaseModel):
    userid: int
    modelconfigid: int
    conversationid:int
    message:str
    istiTle:bool 

def success(message:str = "成功",data:any = None) ->dict:
    return {
        "code": 200,
        "message": message,
        "data": data if data is not None else {}
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
        elif result["code"] == 200:
            return
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
@app.get("/chatai/user/defaultUserImage")
async def get_default_user_image():
    imageurl = image_to_data_url('/user/userdefault.jpg')
    return success("默认用户图像获取成功！", {"imageurl": imageurl})

@app.get("/chatai/health")
async def health():
    return success("服务器访问正常")

@app.get("/chatai/system/metrics")
async def get_system_metrics():
    return success("系统状态查询成功", system_monitor.get_snapshot())

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
        return success("当前会话中的消息不存在！",[])
    else:
         return  success("当前会话消息查询成功！",messages)
@app.get("/chatai/user/tokensCountByUserId")
async def get_tokens_count_by_user_id(userid: int, date: str):
    result = db_manager.get_tokens_count_by_user_id(userid, date)
    check_result(result)
    return success("Token 使用量查询成功", result)

@app.get("/chatai/user/tokensCount")
async def get_tokens_count(conversationid: int, date: str):
    result = db_manager.get_tokens_count(conversationid, date)
    check_result(result)
    return success("Token 使用量查询成功", result)

@app.get("/chatai/user/chatPageMessages") 
async def get_model_chat_message_page(conversationid:int,limit: int,beforeid:int):#获取当前模型的会话记录，分页查询
    messages = db_manager.get_messages_page(conversationid,limit,beforeid)
    check_result(messages)
    return success("当前会话消息查询成功！",messages)

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
    proxy_config = db_manager.get_proxy_config_by_user_id(userid)
    check_result(proxy_config)
    if not config or not proxy_config:
        return success("当前用户模型配置数据不存在！")
    else:
        return success("当前用户模型配置查询成功！",{
            "apikey":key.string_to_base64(key.decrypt_api_key(config["api_key"])),
            "isonline":config["is_online"],
            "modeltype":config["model_type"],
            "modelname": config["model_name"],
            "modelconfigid":config["id"],
            "modelid":config["model_id"],
            "logo":image_to_data_url(config["logo_path"]),
            "proxyhost":proxy_config["proxy_host"],
            "proxyport":proxy_config["proxy_port"],
            "proxyactive":proxy_config["is_active"],
        })
    
@app.get("/chatai/user/getConversationByUserId")
async def get_conversation_by_user_id(userid:int):
    result = db_manager.get_conversation_by_user_id(userid)
    check_result(result)
    if not result:
        return success("当前用户会话记录不存在！", [])
    else:
        return success("当前用户会话记录查询成功！",result)

@app.get("/chatai/user/getConversation")
async def get_conversation(userid:int,modelconfigid:int):
    result = db_manager.get_conversation(userid,modelconfigid)
    check_result(result)
    if not result:
        return success("当前用户会话记录不存在！", [])
    else:
        return success("当前用户会话记录查询成功！",result)
##put
@app.put("/chatai/saveModelConfig")
async def save_model_config(config:ModelConfig):
    encrypted_api_key = key.encrypt_api_key(
       key.base64_to_string(config.apikey)
    )
    is_online = 0 if config.modeltype == "local" else 1
    result = db_manager.create_model_config(
        config.userid,config.modeltype,
        config.modelname,encrypted_api_key,
        is_online
    )
    check_result(result)
    #设置代理
    proxyresult = db_manager.create_proxy_config(config.userid,
        config.proxyhost,config.proxyport,config.proxyactive
    )
    check_result(proxyresult)
    return success("配置保存成功",{
        "userid": result["user_id"],
        "modelconfigid": result["id"],
        "modelid":result["model_id"],
        "modelname": result["model_name"]
    })

##delete
@app.delete("/chatai/user/conversation")
async def delete_conversation(conversationid:int):
    result = db_manager.delete_conversation(conversationid)
    check_result(result)
    return success('会话删除操作成功')

##post
@app.post("/chatai/localModel/start")
async def start_local_model(userid:int, modelconfigid:int):
    model_config = db_manager.get_active_local_model_config(userid, modelconfigid)
    check_result(model_config)
    if not model_config:
        raise HTTPException(
            status_code=400,
            detail="当前本地模型配置不存在或未启用"
        )
    result = await asyncio.to_thread(
        local_model_manager.start,
        model_config["model_name"]
    )
    check_result(result)
    return success(result["message"], {
        "modelname": model_config["model_name"],
        "modelconfigid": model_config["id"]
    })

@app.get("/chatai/localModel/status")
async def get_local_model_status():
    return success("本地模型状态查询成功", local_model_manager.get_status())

@app.post("/chatai/localModel/stop")
async def stop_local_model():
    result = await asyncio.to_thread(local_model_manager.stop)
    check_result(result)
    return success(result["message"])

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
    # 查询历史上下文
    history_messages = db_manager.get_recent_messages_for_context(
        chatMessage.conversationid,
        limit=20
    )
    check_result(history_messages)
    model_config = db_manager.get_model_config_by_userid(chatMessage.userid)
    check_result(model_config)

    is_local_model = (
        model_config.get("provider_type") == "local"
        or model_config.get("model_type") == "local"
    )
    model_messages = modelApi.build_messages(user_message,history_messages)

    if is_local_model:
        local_status = local_model_manager.get_status()
        if local_status.get("status") != "ready":
            raise HTTPException(
                status_code=409,
                detail="本地模型未启动"
            )
        model_name = model_config["model_name"]
        user_tokens_used = 0
        proxy_config = None
        api_key = None
    else:
        #查询当前的VPN配置
        proxy_config = db_manager.get_proxy_config_by_user_id(chatMessage.userid)
        check_result(proxy_config)
        model_name = f"{model_config['provider_type']}/{model_config['model_name']}"
        api_key = key.decrypt_api_key(model_config['api_key'])
        # model_name = "zai/glm-5.2"
        # api_key = "5a42c59072ee4983b9da2456c3b35343.MOiVpKzHuitSmd2T"
        #算上下文的token量
        user_tokens_used = modelApi.get_token_count(model_name,
        model_messages)

    # 先保存用户消息
    if not chatMessage.istiTle:
        user_result = db_manager.create_messages(
            model_config["model_id"],
            chatMessage.conversationid,"user",
            user_message,user_tokens_used)
        check_result(user_result)
        user_created_at = user_result["created_at"]
    async def generate():
        full_content: list[str] = []
        try:
            if is_local_model:
                for content in local_model_manager.chat_stream(model_messages):
                    full_content.append(content)
                    yield json.dumps(
                        {
                            "type": "delta",
                            "content": content
                        },
                        ensure_ascii=False
                    ) + "\n"
                    await asyncio.sleep(0)
            else:
                async for content in modelApi.chat_stream(
                    model_name,
                    api_key,
                    model_messages,
                    proxy_config["proxy_host"],
                    proxy_config["proxy_port"],
                    proxy_config["is_active"]
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
            ai_tokens_used = 0 if is_local_model else modelApi.get_token_count(model_name,
            ai_message)
            if not chatMessage.istiTle:
                # 先保存用户消息
                ai_result = db_manager.create_messages(
                    model_config["model_id"],
                    chatMessage.conversationid,"assistant",
                    ai_message,ai_tokens_used)
                check_result(ai_result)
                yield json.dumps(
                    {
                        "type": "done",
                        "user_created_at":user_created_at,
                        "ai_created_at":ai_result["created_at"]
                    },
                    ensure_ascii=False
                ) + "\n"
            else:
                #替换会话
                title_result = db_manager.update_conversation_title(chatMessage.conversationid,
                                          ai_message)
                check_result(title_result)
                yield json.dumps(
                   {
                        "type": "done",
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
    imgurl = user.imgurl.strip() if user.imgurl else ""
    if not username:
        raise HTTPException(
            status_code=400,
            detail="账号不能为空"
        )
    avatar_mime = "image/png"
    avatar_base64 = ""
    if imgurl:
          if imgurl.startswith("data:") and ";base64," in imgurl:
            header, avatar_base64 = imgurl.split(";base64,", 1)
            avatar_mime = header.replace("data:", "").strip() or "image/png"
          else:
            avatar_base64 = imgurl
    
    # 1. 后端用 bcrypt 再加盐哈希（安全存储）
    result = db_manager.create_user(username, key.string_to_bcrypt_hash(password),
                                    avatar_base64, avatar_mime)
    check_result(result)
    return success("注册成功",{
                "id": result["id"],
                "username": result["username"],
                "imgurl": f'data:{result["avatar_mime"]};base64,{result["avatar_base64"]}'
                if result.get("avatar_base64") else ""
    })

@app.post("/chatai/login")
async def login(user:UserLogin):
    #获取前端传输数据
    username = user.username.strip()
    password = user.password
    db_user = db_manager.get_user_by_username(username)
    check_result(db_user)
    if key.checkpw_bcrypt(password.encode(), db_user["password_hash"]):
            avatar_base64 = db_user.get("avatar_base64") or ""
            avatar_mime = db_user.get("avatar_mime") or "image/png"
            imgurl = ""
            if avatar_base64:
                imgurl = f"data:{avatar_mime};base64,{avatar_base64}"
            return success("登录成功",{
                "id": db_user["id"],
                "username": db_user["username"],
                "imgurl": imgurl
            })
    return error("登录失败，账号或密码不正确！",401)

