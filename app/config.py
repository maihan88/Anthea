"""Đọc cấu hình từ file .env.

Người phụ trách: Hân
"""
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE / ".env")

DB_USER = os.getenv("DB_USER", "anthea")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "flower_db")

# quote_plus: mật khẩu có ký tự như @ : / vẫn ghép đúng vào chuỗi kết nối
SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}/{DB_NAME}?charset=utf8mb4"
)
# MySQL tự ngắt kết nối để lâu không dùng; kiểm tra trước khi dùng lại cho khỏi lỗi "server has gone away"
SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 3600}

# Cloudinary (lưu ảnh người dùng tải lên). Dạng cloudinary://<api_key>:<api_secret>@<cloud_name>,
# chép ở trang Dashboard của Cloudinary. Để trống thì ảnh tạm lưu vào UPLOAD_DIR (xem storage.py).
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "")
UPLOAD_DIR = BASE / "app" / "static" / "uploads"
