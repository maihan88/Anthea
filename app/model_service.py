"""app/model_service.py – cầu nối giữa mô hình CNN và web. Người phụ trách: Hân.

Web chỉ dùng 2 hàm:
    predict(image_bytes)  -> top 3 loài hoa kèm độ tin cậy
    get_model_info()      -> thông tin mô hình (độ chính xác, kiến trúc, số ảnh…)

Đặt USE_FAKE_MODEL=1 trong .env để chạy web không cần TensorFlow
(kết quả là số ngẫu nhiên, chỉ để làm giao diện).
"""
import io
import json
import os
import random
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, UnidentifiedImageError

# ---------------- Đường dẫn & cấu hình ----------------
ROOT_DIR = Path(__file__).resolve().parent.parent      # thư mục anthea/
MODELS_DIR = ROOT_DIR / "models"

load_dotenv(ROOT_DIR / ".env")                         # đọc .env ngay tại đây cho chắc
USE_FAKE = os.getenv("USE_FAKE_MODEL", "0") == "1"


def _read_json(filename):
    path = MODELS_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


CLASS_NAMES = _read_json("class_names.json")           # ["daisy", "dandelion", "roses", ...]
MODEL_INFO = _read_json("model_info.json")
IMG_SIZE = tuple(MODEL_INFO["img_size"])               # (180, 180)

# ---------------- Nạp mô hình MỘT lần khi server khởi động ----------------
model = None
if not USE_FAKE:
    import numpy as np
    import tensorflow as tf
    model = tf.keras.models.load_model(MODELS_DIR / "flower_cnn.keras")


# ---------------- Các bước xử lý ----------------
def _open_image(image_bytes):
    """bytes -> ảnh PIL 3 kênh RGB. File không phải ảnh thì báo ValueError."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()                                   # đọc hết file để phát hiện ảnh hỏng
    except (UnidentifiedImageError, OSError):
        raise ValueError("Không đọc được ảnh")
    return image.convert("RGB")                        # PNG trong suốt / ảnh xám -> 3 kênh


def _real_probabilities(image):
    """Chạy CNN thật. Trả về list 5 xác suất, theo đúng thứ tự CLASS_NAMES."""
    pixels = np.asarray(image, dtype="float32")        # (cao, rộng, 3), giá trị 0..255
    pixels = tf.image.resize(pixels, IMG_SIZE)         # (180, 180, 3) – resize giống hệt lúc train
    batch = tf.expand_dims(pixels, axis=0)             # (1, 180, 180, 3) – mô hình nhận một lô ảnh
    # KHÔNG chia 255 ở đây: mô hình đã có sẵn lớp Rescaling(1/255) bên trong
    output = model.predict(batch, verbose=0)           # (1, 5)
    return output[0].tolist()


def _fake_probabilities(image_bytes):
    """Xác suất ngẫu nhiên cho chế độ USE_FAKE_MODEL=1."""
    rnd = random.Random(len(image_bytes))              # cùng ảnh -> cùng kết quả
    scores = [rnd.random() for _ in CLASS_NAMES]
    total = sum(scores)
    return [score / total for score in scores]


# ---------------- Hàm cho web gọi ----------------
def predict(image_bytes, top_k=3):
    """Trả về top_k loài, ví dụ [{"code": "roses", "confidence": 0.91}, ...]."""
    image = _open_image(image_bytes)                   # chế độ giả cũng kiểm tra ảnh hợp lệ
    if USE_FAKE:
        probs = _fake_probabilities(image_bytes)
    else:
        probs = _real_probabilities(image)

    pairs = list(zip(CLASS_NAMES, probs))              # [("daisy", 0.02), ("dandelion", 0.01), ...]
    pairs.sort(key=lambda pair: pair[1], reverse=True) # xác suất cao nhất lên đầu

    results = []
    for code, prob in pairs[:top_k]:
        results.append({"code": code, "confidence": round(float(prob), 4)})
    return results


def get_model_info():
    return MODEL_INFO
