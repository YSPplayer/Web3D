from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from Config.config import config
import uvicorn
import mimetypes
from Data.db_manager import db_manager
from Model.key import key
from Model.modelapi import modelApi
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
   # modelApi.chat("zai/glm-5.2","5a42c59072ee4983b9da2456c3b35343.MOiVpKzHuitSmd2T","你好，请问数学中的函数指代什么？")
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
            "modelconfigid":config["model_config_id"],
            "logo":image_to_data_url(config["logo_path"])
        })
    
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

