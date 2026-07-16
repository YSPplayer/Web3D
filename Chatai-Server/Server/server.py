from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from Config.config import config
import uvicorn
import bcrypt
import sqlite3
from Data.db_manager import db_manager
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

def success(message:str = "成功",data:any = None) ->dict:
    return {
        "code": 200,
        "message": message,
        "data": data or {}
    }
def error(message: str = "操作失败", code: int = 400) ->dict:
    return {
         "code": code,
         "message": message
    }

@app.get("/chatai/health")
async def health():
    return success("服务器访问正常")
@app.get("/chatai/models") #获取到当前后端存储的所有类别的模型
async def models():
    models = db_manager.get_models()
    return success("模型数据查询成功！",models)
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
    salt = bcrypt.gensalt()
    final_hash = bcrypt.hashpw(password.encode(), salt)
    try:
        result = db_manager.create_user(username,final_hash)
    except sqlite3.IntegrityError as exc:
        if "UNIQUE constraint failed: users.username" in str(exc):
            raise HTTPException(
                status_code=409,
                detail="账号已经存在"
            )

        raise HTTPException(
            status_code=500,
            detail="数据库写入失败"
        )
    return success("注册成功",{
                "username": result.username
    })

@app.post("/chatai/login")
async def login(user:UserRegister):
    #获取前端传输数据
    username = user.username.strip()
    password = user.password
    db_user = db_manager.get_user_by_username(user.username)
    if db_user is not None:
        if bcrypt.checkpw(password.encode(), db_user["password_hash"]):
            return success("登录成功",{
                "username": username
            })
    return error("登录失败，账号或密码不正确！",401)

