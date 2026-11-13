"""Flask: gửi các trang HTML + REST API.
Người phụ trách: Nghi

Các trang trong app/pages/ là HTML tĩnh (không dùng Jinja): Flask chỉ gửi nguyên file.
Dữ liệu do JavaScript trong trang tự gọi các đường /api/... (trả về JSON) rồi điền vào.
"""
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from sqlalchemy.exc import SQLAlchemyError

import config
import model_service
import storage
from database import Flower, Prediction, PredictionScore, db

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)

PAGES_DIR = Path(__file__).parent / "pages"
SAMPLES_DIR = Path(__file__).parent / "static" / "samples"     # ảnh mẫu: samples/<mã loài>/*.jpg
MAX_IMAGE_SIZE = 5 * 1024 * 1024                                # 5 MB
ALLOWED_TYPES = {"image/jpeg": "jpg", "image/png": "png"}      # kiểu ảnh nhận -> đuôi file
OTHER_CODE = "other"                                           # lớp "Khác" của mô hình: không phải một loài hoa


# ================= CÁC TRANG HTML =================

@app.route("/")
def index_page():
    return send_from_directory(PAGES_DIR, "index.html")


@app.route("/identify")
def identify_page():
    return send_from_directory(PAGES_DIR, "identify.html")


@app.route("/flowers")
def flowers_page():
    return send_from_directory(PAGES_DIR, "flowers.html")


@app.route("/flowers/<int:flower_id>")
def flower_detail_page(flower_id):
    # Cùng một file cho mọi id: JS đọc id trên thanh địa chỉ rồi gọi /api/flowers/<id>
    return send_from_directory(PAGES_DIR, "flower_detail.html")


@app.route("/history")
def history_page():
    return send_from_directory(PAGES_DIR, "history.html")


@app.route("/history/<int:prediction_id>")
def history_detail_page(prediction_id):
    return send_from_directory(PAGES_DIR, "history_detail.html")


@app.route("/model")
def model_page():
    return send_from_directory(PAGES_DIR, "model.html")


# ================= HÀM PHỤ =================

def count_model_images(code):
    """Số ảnh của một lớp mà mô hình đang dùng đã học: train + val + test trong models/model_info.json.
    Thay mô hình (v1 -> v2) thì số này tự đổi theo."""
    num_images = model_service.get_model_info()["num_images"]
    return num_images["train"][code] + num_images["val"][code] + num_images["test"][code]


def get_sample_images(flower_code):
    """Link các ảnh mẫu trong static/samples/<mã loài>/. Chưa có thư mục thì trả về list rỗng."""
    folder = SAMPLES_DIR / flower_code
    if not folder.is_dir():
        return []
    urls = []
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() in (".jpg", ".jpeg", ".png"):
            urls.append(f"/static/samples/{flower_code}/{path.name}")
    return urls


def flower_to_json(flower):
    """Thông tin một loài + số ảnh mô hình đã học + ảnh mẫu, cho trang Thư viện hoa và Chi tiết loài."""
    data = flower.to_dict()
    data["image_count"] = count_model_images(flower.code)
    data["samples"] = get_sample_images(flower.code)
    return data


def find_flower(code):
    """Tìm loài theo mã lớp của mô hình ("roses", "tulips"…). Không có thì trả về None."""
    return db.session.scalar(db.select(Flower).where(Flower.code == code))


# ================= API: LOÀI HOA & MÔ HÌNH =================

@app.route("/api/flowers")
def api_flowers():
    # Thư viện hoa chỉ có các loài hoa, không có lớp "Khác"
    query = db.select(Flower).where(Flower.code != OTHER_CODE).order_by(Flower.id)
    flowers = db.session.scalars(query).all()
    result = []
    for flower in flowers:
        result.append(flower_to_json(flower))
    return jsonify(result)


@app.route("/api/flowers/<int:flower_id>")
def api_flower(flower_id):
    flower = db.session.get(Flower, flower_id)
    if flower is None or flower.code == OTHER_CODE:
        return jsonify(error=f"Không tìm thấy loài hoa #{flower_id}."), 404
    return jsonify(flower_to_json(flower))


@app.route("/api/model-info")
def api_model_info():
    """Nội dung models/model_info.json, thêm "flowers": thông tin các lớp (tên tiếng Việt…) theo đúng thứ tự class_names."""
    info = dict(model_service.get_model_info())        # chép ra bản mới, không sửa bản gốc
    flowers = []
    for code in info["class_names"]:
        flower = find_flower(code)
        if flower is None:
            return jsonify(error="CSDL chưa có đủ các lớp của mô hình — hãy chạy python app/seed.py."), 500
        flowers.append(flower.to_dict())
    info["flowers"] = flowers
    return jsonify(info)


# ================= API: LỊCH SỬ =================

@app.route("/api/history")
def api_history():
    """Các lần phân loại, mới nhất trước. /api/history?limit=4 thì chỉ lấy 4 mục."""
    limit = request.args.get("limit", type=int)        # không có ?limit= thì là None
    query = db.select(Prediction).order_by(Prediction.id.desc())
    if limit:
        query = query.limit(limit)
    predictions = db.session.scalars(query).all()

    items = []
    for prediction in predictions:
        items.append(prediction.to_dict())
    return jsonify(items=items)


@app.route("/api/history/<int:prediction_id>")
def api_history_item(prediction_id):
    prediction = db.session.get(Prediction, prediction_id)
    if prediction is None:
        return jsonify(error=f"Không tìm thấy mục #{prediction_id} — có thể đã bị xóa."), 404
    return jsonify(prediction.to_dict(detail=True))


@app.route("/api/history/<int:prediction_id>", methods=["DELETE"])
def api_history_delete(prediction_id):
    prediction = db.session.get(Prediction, prediction_id)
    if prediction is None:
        return jsonify(error=f"Không tìm thấy mục #{prediction_id} — có thể đã bị xóa."), 404

    image_id = prediction.image_id
    db.session.delete(prediction)              # 3 dòng prediction_scores tự xóa theo (ON DELETE CASCADE)
    db.session.commit()
    storage.delete_image(image_id)             # xóa dòng trong CSDL trước, rồi mới xóa ảnh
    return jsonify(deleted=1)


@app.route("/api/history", methods=["DELETE"])
def api_history_delete_all():
    predictions = db.session.scalars(db.select(Prediction)).all()
    image_ids = []
    for prediction in predictions:
        image_ids.append(prediction.image_id)
        db.session.delete(prediction)
    db.session.commit()

    for image_id in image_ids:
        storage.delete_image(image_id)
    return jsonify(deleted=len(image_ids))


# ================= API: PHÂN LOẠI ẢNH =================

@app.route("/api/predict", methods=["POST"])
def api_predict():
    # Bước 1: kiểm tra ảnh gửi lên
    file = request.files.get("image")
    if file is None or file.filename == "":
        return jsonify(error="Chưa có ảnh để phân loại."), 400
    if file.mimetype not in ALLOWED_TYPES:
        return jsonify(error="Định dạng chưa được hỗ trợ — vui lòng chọn ảnh JPG hoặc PNG."), 400
    image_bytes = file.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        return jsonify(error="Ảnh vượt giới hạn 5 MB."), 400

    # Bước 2: mô hình CNN phân loại -> top 3, ví dụ [{"code": "roses", "confidence": 0.91}, ...]
    try:
        top = model_service.predict(image_bytes)
    except ValueError:
        return jsonify(error="Không đọc được ảnh."), 400

    # Bước 3: tìm thông tin 3 loài trong CSDL
    flowers = []
    for item in top:
        flower = find_flower(item["code"])
        if flower is None:
            return jsonify(error="CSDL chưa có thông tin loài hoa — hãy chạy python app/seed.py."), 500
        flowers.append(flower)

    # Bước 4: lưu ảnh lên Cloudinary
    try:
        image_url, image_id = storage.save_image(image_bytes, ALLOWED_TYPES[file.mimetype])
    except Exception:
        app.logger.exception("Không lưu được ảnh")
        return jsonify(error="Không tải được ảnh lên Cloudinary — kiểm tra mạng và CLOUDINARY_URL trong .env."), 500

    # Bước 5: lưu lịch sử = 1 dòng predictions + 3 dòng prediction_scores
    info = model_service.get_model_info()
    threshold = info["uncertain_threshold"]
    prediction = Prediction(
        flower=flowers[0],                     # loài đứng đầu
        confidence=top[0]["confidence"],
        image_url=image_url,
        image_id=image_id,
        original_name=file.filename[:255],
        file_size=len(image_bytes),
        model_version=info["version"],
        threshold=threshold,
    )
    for i in range(len(top)):
        prediction.scores.append(PredictionScore(ranking=i + 1, flower=flowers[i], confidence=top[i]["confidence"]))

    try:
        db.session.add(prediction)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        storage.delete_image(image_id)         # không lưu được lịch sử thì xóa luôn ảnh vừa tải lên
        app.logger.exception("Không lưu được lịch sử")
        return jsonify(error="Không lưu được lịch sử — kiểm tra MySQL đã chạy chưa."), 500

    # Bước 6: trả kết quả cho trang Nhận diện
    results = []
    for i in range(len(top)):
        data = flowers[i].to_dict()
        data["confidence"] = top[i]["confidence"]
        data["samples"] = get_sample_images(flowers[i].code)
        results.append(data)

    return jsonify(
        top=results,
        threshold=threshold,
        uncertain=top[0]["confidence"] < threshold,    # độ tin cậy dưới ngưỡng -> "chưa chắc chắn"
        history_id=prediction.id,
    )


# ================= BẮT LỖI =================

@app.errorhandler(404)
def not_found(error):
    # Đường /api/... trả JSON để JavaScript đọc được; trang thường thì hiện trang 404
    if request.path.startswith("/api/"):
        return jsonify(error="Không tìm thấy địa chỉ API này."), 404
    return send_from_directory(PAGES_DIR, "404.html"), 404


@app.errorhandler(SQLAlchemyError)
def database_error(error):
    # MySQL chưa chạy hoặc truy vấn lỗi: báo câu tiếng Việt thay vì trang lỗi
    db.session.rollback()
    app.logger.exception("Lỗi CSDL")
    return jsonify(error="Không đọc/ghi được CSDL — kiểm tra MySQL đã chạy chưa."), 500


if __name__ == "__main__":
    app.run(debug=True)
