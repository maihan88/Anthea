"""Flask: các trang + REST API.
Người phụ trách: Nghi
"""
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import HTTPException

import config
import model_service
from database import DatasetImage, Flower, Prediction, PredictionScore, db

app = Flask(__name__)
app.config.from_object(config)
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024    # chặn request quá lớn (ảnh 5 MB + phần đầu multipart)
db.init_app(app)

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png"}   # kiểu ảnh → đuôi file khi lưu
SAMPLE_DIR = Path(app.static_folder) / "samples"               # ảnh mẫu: samples/<mã loài>/*.jpg
SAMPLE_TYPES = {".jpg", ".jpeg", ".png", ".webp"}
# Câu báo lỗi cho các lỗi HTTP mà route không tự báo (đường /api/ sai, sai phương thức…)
HTTP_ERRORS = {
    400: "Yêu cầu không hợp lệ.",
    404: "Không tìm thấy địa chỉ API này.",
    405: "Địa chỉ này không hỗ trợ phương thức đó.",
    500: "Máy chủ gặp lỗi, vui lòng thử lại.",
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
    flower = db.get_or_404(Flower, flower_id)                  # id sai thì trả trang 404 ngay, không đợi JS
    return render_template("flower_detail.html", flower=flower)


@app.route("/history")
def history():
    return render_template("history.html")


@app.route("/history/<int:prediction_id>")
def history_detail(prediction_id):
    # Không trả 404 ở đây: mục vừa bị xóa thì trang tự báo "đã bị xóa" (JS gọi API nhận 404)
    return render_template("history_detail.html", prediction_id=prediction_id)


@app.route("/model")
def model():
    return render_template("model.html")


# ---------------- REST API ----------------
def is_api():
    return request.path.startswith("/api/")


def api_error(message, status):
    return jsonify(error=message), status


def image_counts(flowers):
    """Số ảnh kept của mỗi loài theo nguồn: {flower_id: {"tf_flowers": n, "web": n}}.
    dataset_images chưa nạp thì tạm lấy num_images trong model_info.json (chỉ có phần TF Flowers)."""
    counts = {f.id: {"tf_flowers": 0, "web": 0} for f in flowers}
    if db.session.scalar(db.select(DatasetImage.id).limit(1)) is None:
        num_images = model_service.get_model_info()["num_images"]   # {"train": {"daisy": 445, …}, "val": …}
        for f in flowers:
            counts[f.id]["tf_flowers"] = sum(split.get(f.code, 0) for split in num_images.values())
        return counts
    rows = db.session.execute(
        db.select(DatasetImage.flower_id, DatasetImage.source, db.func.count())
        .where(DatasetImage.status == "kept")
        .group_by(DatasetImage.flower_id, DatasetImage.source)
    )
    for flower_id, source, n in rows:
        if flower_id in counts:
            counts[flower_id][source] = n
    return counts


def sample_urls(flower):
    """URL các ảnh mẫu trong static/samples/<mã loài>/, sắp theo tên file. Chưa có thư mục thì rỗng."""
    folder = SAMPLE_DIR / flower.code
    if not folder.is_dir():
        return []
    return [url_for("static", filename=f"samples/{flower.code}/{p.name}")
            for p in sorted(folder.iterdir()) if p.suffix.lower() in SAMPLE_TYPES]


def flower_json(flower, counts, samples):
    return {**flower.to_dict(), "image_counts": counts[flower.id], "cover": samples[0] if samples else None}


def remove_upload(image_path):
    """Xóa ảnh đã tải lên. Chỉ lấy tên file, nên dòng CSDL bị sửa tay cũng không xóa được ra ngoài uploads/."""
    (config.UPLOAD_DIR / Path(image_path).name).unlink(missing_ok=True)


@app.route("/api/flowers")
def api_flowers():
    flowers = db.session.scalars(db.select(Flower).order_by(Flower.id)).all()
    counts = image_counts(flowers)
    return jsonify([flower_json(f, counts, sample_urls(f)) for f in flowers])


@app.route("/api/flowers/<int:flower_id>")
def api_flower(flower_id):
    flower = db.session.get(Flower, flower_id)
    if flower is None:
        return api_error(f"Không tìm thấy loài hoa #{flower_id}.", 404)
    samples = sample_urls(flower)
    return jsonify({**flower_json(flower, image_counts([flower]), samples), "samples": samples})


@app.route("/api/model-info")
def api_model_info():
    """Nguyên nội dung model_info.json, thêm flowers: tên và số ảnh từng loài theo đúng thứ tự class_names
    (trang Mô hình dùng làm nhãn ma trận nhầm lẫn và bảng số ảnh)."""
    info = model_service.get_model_info()
    by_code = {f.code: f for f in db.session.scalars(db.select(Flower).where(Flower.code.in_(info["class_names"])))}
    flowers = [by_code[code] for code in info["class_names"] if code in by_code]
    counts = image_counts(flowers)
    return jsonify({**info, "flowers": [
        {"id": f.id, "code": f.code, "name_vi": f.name_vi, "hue": f.hue, "image_counts": counts[f.id]}
        for f in flowers
    ]})


@app.route("/api/history")
def api_history():
    limit = request.args.get("limit")
    if limit is not None and not (limit.isdecimal() and int(limit) > 0):
        return api_error("Tham số limit phải là số nguyên dương.", 400)
    # Mới nhất trước; cùng giây thì id lớn hơn là mới hơn
    query = (db.select(Prediction).options(joinedload(Prediction.flower))
             .order_by(Prediction.created_at.desc(), Prediction.id.desc()))
    if limit:
        query = query.limit(int(limit))
    items = db.session.scalars(query).all()
    total = db.session.scalar(db.select(db.func.count(Prediction.id)))
    return jsonify(items=[p.to_dict() for p in items], total=total)


@app.route("/api/history/<int:prediction_id>")
def api_history_item(prediction_id):
    prediction = db.session.get(Prediction, prediction_id)
    if prediction is None:
        return api_error(f"Không tìm thấy mục #{prediction_id} — có thể đã bị xóa.", 404)
    return jsonify(prediction.to_dict(detail=True))


@app.route("/api/history/<int:prediction_id>", methods=["DELETE"])
def api_history_delete(prediction_id):
    prediction = db.session.get(Prediction, prediction_id)
    if prediction is None:
        return api_error(f"Không tìm thấy mục #{prediction_id} — có thể đã bị xóa.", 404)
    image_path = prediction.image_path
    db.session.delete(prediction)              # 3 dòng prediction_scores tự xóa theo (ON DELETE CASCADE)
    db.session.commit()
    remove_upload(image_path)                  # xóa dòng trước, file sau: file thiếu thì bỏ qua
    return jsonify(deleted=1)


@app.route("/api/history", methods=["DELETE"])
def api_history_delete_all():
    rows = db.session.execute(db.select(Prediction.id, Prediction.image_path)).all()
    if rows:
        db.session.execute(db.delete(Prediction).where(Prediction.id.in_([r.id for r in rows])))
        db.session.commit()
    for row in rows:
        remove_upload(row.image_path)
    return jsonify(deleted=len(rows))


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


# ---------------- Bắt lỗi ----------------
def too_large_error(size):
    return jsonify(error=f"Ảnh nặng {size / 1024 / 1024:.1f} MB — vượt giới hạn 5 MB."), 413


@app.errorhandler(413)
def too_large(e):
    return too_large_error(request.content_length or 0)


@app.errorhandler(HTTPException)
def http_error(e):
    """Đường /api/... luôn trả JSON {"error": …} để frontend đọc được; trang thường thì 404 có trang riêng.
    Lỗi chưa bắt (ví dụ ghi file thất bại) cũng đi qua đây dưới dạng 500, trừ khi chạy debug=True."""
    if is_api():
        return api_error(HTTP_ERRORS.get(e.code) or HTTP_ERRORS[500 if e.code >= 500 else 400], e.code)
    if e.code == 404:
        return render_template("404.html"), 404
    return e


@app.errorhandler(SQLAlchemyError)
def db_error(e):
    """MySQL tắt hoặc truy vấn lỗi: /api/... báo câu tiếng Việt thay vì trang lỗi HTML (kể cả khi debug)."""
    db.session.rollback()
    if not is_api():
        raise e
    app.logger.exception("Lỗi CSDL")
    return api_error("Không đọc/ghi được CSDL — kiểm tra MySQL đã chạy chưa.", 500)


if __name__ == "__main__":
    app.run(debug=True)
