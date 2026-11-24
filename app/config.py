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

# quote_plus: mật khẩu có ký tự đặc biệt như @ hay : vẫn ghép vào đường link được
SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}/{DB_NAME}?charset=utf8mb4"
)
# Kiểm tra kết nối trước khi dùng, vì MySQL tự ngắt kết nối bị bỏ không quá lâu
SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 3600}

CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "")
