"""app/model_service.py – cầu nối giữa mô hình CNN và web. Người phụ trách: Hân."""
import io, json, os, random
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent.parent
MODELS = BASE / "models"
load_dotenv(BASE / ".env")                        # đọc .env ngay tại đây cho chắc
USE_FAKE = os.getenv("USE_FAKE_MODEL", "0") == "1"

CLASS_NAMES = json.loads((MODELS / "class_names.json").read_text(encoding="utf-8"))
MODEL_INFO = json.loads((MODELS / "model_info.json").read_text(encoding="utf-8"))
IMG_SIZE = tuple(MODEL_INFO["img_size"])

_model = None
if not USE_FAKE:                                   # nạp mô hình MỘT lần khi server khởi động
    import numpy as np
    import tensorflow as tf
    _model = tf.keras.models.load_model(MODELS / "flower_cnn.keras")

def _load_image(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
    except (UnidentifiedImageError, OSError):
        raise ValueError("Không đọc được ảnh")
    return img.convert("RGB")                      # PNG trong suốt / ảnh xám -> 3 kênh

def predict(image_bytes, top_k=3):
    img = _load_image(image_bytes)
    if USE_FAKE:
        rnd = random.Random(len(image_bytes))      # cùng ảnh -> cùng kết quả
        probs = [rnd.random() for _ in CLASS_NAMES]
        total = sum(probs)
        probs = [p / total for p in probs]
    else:
        x = tf.image.resize(np.asarray(img, dtype="float32"), IMG_SIZE).numpy()[None, ...]  # resize giống hệt lúc train
        probs = _model.predict(x, verbose=0)[0].tolist()   # KHÔNG chia 255
    ranked = sorted(zip(CLASS_NAMES, probs), key=lambda t: t[1], reverse=True)
    return [{"code": c, "confidence": round(float(p), 4)} for c, p in ranked[:top_k]]

def get_model_info():
    return MODEL_INFO