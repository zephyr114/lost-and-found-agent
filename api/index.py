"""Vercel Python 入口：把 FastAPI 应用挂到 serverless function 上。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402,F401
