from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from Config.config import config
import uvicorn
from Data.db_manager import db_manager
app = FastAPI(title="Chat API")
# 重要：允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # 开发环境允许所有，生产环境要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run():
    db_manager.init_db()  # 初始化数据库
    uvicorn.run("Server.server:app", host=config.server_ip, port=config.server_port, reload=False)
# ---- API 接口 ----
