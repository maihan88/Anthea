import io
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def read_json(filename):
    path = MODELS_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


CLASS_NAMES = read_json("class_names.json")
MODEL_INFO = read_json("model_info.json")
IMG_SIZE = MODEL_INFO["img_size"]

model = tf.keras.models.load_model(MODELS_DIR / "flower_cnn.keras")

# Chạy thử một ảnh đen lúc bật web, để lần nhận diện đầu tiên của người dùng không bị chậm
blank_image = np.zeros((1, IMG_SIZE[0], IMG_SIZE[1], 3), dtype="float32")
model.predict(blank_image, verbose=0)


def open_image(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except (UnidentifiedImageError, OSError):
        raise ValueError("Không đọc được ảnh")
    return image.convert("RGB")


def get_confidence(item):
    return item["confidence"]


def predict(image_bytes, top_k=3):
    image = open_image(image_bytes)
    pixels = np.asarray(image, dtype="float32")
    pixels = tf.image.resize(pixels, IMG_SIZE)
    batch = tf.expand_dims(pixels, axis=0)
    probs = model.predict(batch, verbose=0)[0]

    results = []
    for i in range(len(CLASS_NAMES)):
        results.append({"code": CLASS_NAMES[i], "confidence": round(float(probs[i]), 4)})
    results.sort(key=get_confidence, reverse=True)
    return results[:top_k]


def get_model_info():
    return MODEL_INFO
