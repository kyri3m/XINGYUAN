"""
环境监测采样派单系统 - FastAPI
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from .models import init_db
from .api import router

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "frontend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(); yield

app = FastAPI(title="环境监测采样派单系统", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
@app.get("/login")
@app.get("/login2.html")
async def login(): return FileResponse(os.path.join(STATIC_DIR, "login2.html"))

@app.get("/register")
@app.get("/register.html")
async def register(): return FileResponse(os.path.join(STATIC_DIR, "register.html"))

@app.get("/index.html")
async def index(): return FileResponse(os.path.join(STATIC_DIR, "index.html"))
