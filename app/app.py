"""Flask: các trang + REST API.
Người phụ trách: Nghi
"""
from flask import Flask, jsonify, render_template, request

import model_service

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024    # chặn request quá lớn (ảnh 5 MB + phần đầu multipart)

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png"}

# Thông tin 5 loài (lấy đúng chữ trong bản thiết kế) – TẠM để ở đây, thay bằng bảng flowers khi có database
FLOWERS = {
    "daisy": {
        "id": 1, "name_vi": "Cúc họa mi", "name_en": "Daisy", "scientific": "Bellis perennis", "hue": 140,
        "description": "Cánh trắng mảnh, xếp một vòng quanh nhụy vàng tròn ở giữa.",
        "meaning": "Sự ngây thơ, trong sáng và khởi đầu mới.",
        "season": "Cuối thu – đầu đông",
    },
    "dandelion": {
        "id": 2, "name_vi": "Bồ công anh", "name_en": "Dandelion", "scientific": "Taraxacum officinale", "hue": 60,
        "description": "Hoa vàng gồm nhiều cánh nhỏ li ti; khi già kết thành quả cầu lông trắng.",
        "meaning": "Hy vọng, ước nguyện và sự tự do.",
        "season": "Mùa xuân – hè",
    },
    "roses": {
        "id": 3, "name_vi": "Hoa hồng", "name_en": "Rose", "scientific": "Rosa spp.", "hue": 10,
        "description": "Cánh hoa xếp nhiều lớp xoắn quanh tâm, thân có gai, lá kép với mép răng cưa.",
        "meaning": "Tình yêu, sự trân trọng và lòng biết ơn.",
        "season": "Quanh năm, rộ nhất vào mùa xuân",
    },
    "sunflowers": {
        "id": 4, "name_vi": "Hướng dương", "name_en": "Sunflower", "scientific": "Helianthus annuus", "hue": 85,
        "description": "Đĩa hoa lớn màu nâu ở giữa, cánh vàng tỏa tròn, thân cao và cứng.",
        "meaning": "Niềm tin, sự lạc quan, luôn hướng về ánh sáng.",
        "season": "Mùa hè đến đầu thu",
    },
    "tulips": {
        "id": 5, "name_vi": "Tulip", "name_en": "Tulip", "scientific": "Tulipa", "hue": 345,
        "description": "Hoa hình chén với 6 cánh, thân thẳng, lá dài hình mũi mác.",
        "meaning": "Tình yêu hoàn hảo, sự sung túc.",
        "season": "Mùa xuân",
    },
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/identify")
def identify():
    return render_template("identify.html")


@app.route("/flowers")
def flowers():
    return render_template("flowers.html")


@app.route("/flowers/<int:flower_id>")
def flower_detail(flower_id):
    return render_template("flower_detail.html")


@app.route("/history")
def history():
    return render_template("history.html")


@app.route("/history/<int:prediction_id>")
def history_detail(prediction_id):
    return render_template("history_detail.html")


@app.route("/model")
def model():
    return render_template("model.html")


# ---------------- REST API ----------------
@app.route("/api/predict", methods=["POST"])
def api_predict():
    file = request.files.get("image")
    if file is None or file.filename == "":
        return jsonify(error="Chưa có ảnh để phân loại."), 400
    if file.mimetype not in ALLOWED_TYPES:
        return jsonify(error="Định dạng chưa được hỗ trợ — vui lòng chọn ảnh JPG hoặc PNG."), 400
    image_bytes = file.read()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        return too_large_error(len(image_bytes))
    try:
        top = model_service.predict(image_bytes)
    except ValueError as e:
        return jsonify(error=f"{e}."), 400

    threshold = model_service.get_model_info()["uncertain_threshold"]
    return jsonify(
        top=[{**FLOWERS[p["code"]], **p} for p in top],
        threshold=threshold,
        uncertain=top[0]["confidence"] < threshold,
        history_id=None,                              # chưa có bảng predictions nên chưa lưu lịch sử
    )


def too_large_error(size):
    return jsonify(error=f"Ảnh nặng {size / 1024 / 1024:.1f} MB — vượt giới hạn 5 MB."), 413


@app.errorhandler(413)
def too_large(e):
    return too_large_error(request.content_length or 0)


if __name__ == "__main__":
    app.run(debug=True)
