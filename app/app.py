"""Flask: các trang + REST API.
Người phụ trách: Nghi
"""
import uuid

from flask import Flask, jsonify, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError

import config
import model_service
from database import Flower, Prediction, PredictionScore, db

app = Flask(__name__)
app.config.from_object(config)
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024    # chặn request quá lớn (ảnh 5 MB + phần đầu multipart)
db.init_app(app)

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png"}   # kiểu ảnh → đuôi file khi lưu


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

    info = model_service.get_model_info()
    threshold = info["uncertain_threshold"]
    # Tên file ngẫu nhiên (uuid4): không trùng, không có ký tự lạ hay "../"; tên gốc chỉ lưu vào CSDL
    image_file = config.UPLOAD_DIR / (uuid.uuid4().hex + ALLOWED_TYPES[file.mimetype])
    try:
        codes = [p["code"] for p in top]
        flowers = {f.code: f for f in db.session.scalars(db.select(Flower).where(Flower.code.in_(codes)))}
        if len(flowers) < len(codes):
            return jsonify(error="CSDL chưa có đủ thông tin loài hoa — chạy python app/seed.py."), 500
        image_file.write_bytes(image_bytes)
        # 1 dòng predictions + 3 dòng prediction_scores trong cùng một lần commit: lỗi thì không dòng nào được ghi
        prediction = Prediction(
            flower=flowers[top[0]["code"]], confidence=top[0]["confidence"],
            image_path=f"uploads/{image_file.name}", original_name=file.filename[:255],
            file_size=len(image_bytes), model_version=info["version"], threshold=threshold,
            scores=[PredictionScore(ranking=i, flower=flowers[p["code"]], confidence=p["confidence"])
                    for i, p in enumerate(top, start=1)],
        )
        db.session.add(prediction)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        image_file.unlink(missing_ok=True)
        app.logger.exception("Không lưu được lịch sử phân loại")
        return jsonify(error="Không lưu được lịch sử — kiểm tra MySQL đã chạy chưa."), 500

    return jsonify(
        top=[{**flowers[p["code"]].to_dict(), **p} for p in top],
        threshold=threshold,
        uncertain=top[0]["confidence"] < threshold,
        history_id=prediction.id,
        image_url=url_for("static", filename=prediction.image_path),
        created_at=prediction.created_at.isoformat(timespec="seconds"),
    )


def too_large_error(size):
    return jsonify(error=f"Ảnh nặng {size / 1024 / 1024:.1f} MB — vượt giới hạn 5 MB."), 413


@app.errorhandler(413)
def too_large(e):
    return too_large_error(request.content_length or 0)


if __name__ == "__main__":
    app.run(debug=True)
