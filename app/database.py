"""4 bảng: flowers, predictions, prediction_scores, dataset_images.

Schema là điểm giao chung: sửa file này chỉ qua Pull Request có người kia duyệt.
db.create_all() chỉ tạo bảng chưa có, KHÔNG sửa bảng đã có — đổi cột thì xóa bảng rồi chạy lại seed.py.
Người phụ trách: Hân
"""
from datetime import datetime

from flask import url_for
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Flower(db.Model):
    """Một loài hoa. id cố định 1–5 theo thứ tự class_names.json, hoa sen là 6."""
    __tablename__ = "flowers"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)       # đúng tên lớp của mô hình: roses, tulips…
    name_vi = db.Column(db.String(50), nullable=False)
    name_en = db.Column(db.String(50), nullable=False)
    scientific_name = db.Column(db.String(80))
    hue = db.Column(db.SmallInteger, nullable=False)                    # màu chấm tròn trên giao diện (0–360)
    description = db.Column(db.Text)
    meaning = db.Column(db.Text)
    season = db.Column(db.String(100))
    in_model = db.Column(db.Boolean, nullable=False, default=True)      # False: thẻ "Sắp có" (hoa sen)

    def to_dict(self):
        # Giữ đúng tên trường mà frontend đang đọc (scientific, không phải scientific_name)
        return {
            "id": self.id, "code": self.code, "name_vi": self.name_vi, "name_en": self.name_en,
            "scientific": self.scientific_name, "hue": self.hue, "description": self.description,
            "meaning": self.meaning, "season": self.season, "in_model": self.in_model,
        }


class Prediction(db.Model):
    """Một lần phân loại. Lưu phiên bản mô hình và ngưỡng TẠI THỜI ĐIỂM phân loại."""
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    flower_id = db.Column(db.Integer, db.ForeignKey("flowers.id"), nullable=False)   # loài đứng đầu
    confidence = db.Column(db.Float, nullable=False)
    image_path = db.Column(db.String(255), nullable=False)       # trong static/, ví dụ uploads/3f9c….jpg
    original_name = db.Column(db.String(255), nullable=False)    # tên file người dùng đặt, chỉ để hiển thị
    file_size = db.Column(db.Integer, nullable=False)            # byte
    model_version = db.Column(db.String(20), nullable=False)     # "v1", "v2"
    threshold = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)  # trang Lịch sử sắp theo cột này

    flower = db.relationship("Flower")
    # Xóa lần phân loại thì 3 dòng điểm xóa theo
    scores = db.relationship("PredictionScore", back_populates="prediction", order_by="PredictionScore.ranking",
                             cascade="all, delete-orphan", passive_deletes=True)

    def to_dict(self, detail=False):
        """Một mục lịch sử cho /api/history. detail=True: thêm phần trang Chi tiết lịch sử cần.
        uncertain tính bằng ngưỡng lưu cùng dòng này, không phải ngưỡng hiện tại của mô hình."""
        data = {
            "id": self.id,
            "flower": {"id": self.flower.id, "name_vi": self.flower.name_vi, "hue": self.flower.hue},
            "confidence": self.confidence, "threshold": self.threshold,
            "uncertain": self.confidence < self.threshold,
            "image_url": url_for("static", filename=self.image_path),
            "original_name": self.original_name,
            "created_at": self.created_at.isoformat(timespec="seconds"),
        }
        if detail:
            data.update(
                flower=self.flower.to_dict(), file_size=self.file_size, model_version=self.model_version,
                # Cùng dạng top của /api/predict (thông tin loài + confidence), để hai trang dùng chung hàm vẽ
                top=[{**s.flower.to_dict(), "confidence": s.confidence} for s in self.scores],
            )
        return data


class PredictionScore(db.Model):
    """Top 3 của một lần phân loại: mỗi lần đúng 3 dòng, ranking 1–3."""
    __tablename__ = "prediction_scores"
    __table_args__ = (db.UniqueConstraint("prediction_id", "ranking"),)

    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False)
    ranking = db.Column(db.SmallInteger, nullable=False)         # không đặt tên "rank": từ khóa của MySQL 8
    flower_id = db.Column(db.Integer, db.ForeignKey("flowers.id"), nullable=False)
    confidence = db.Column(db.Float, nullable=False)

    prediction = db.relationship("Prediction", back_populates="scores")
    flower = db.relationship("Flower")


class DatasetImage(db.Model):
    """Mỗi ảnh của bộ dữ liệu (TF Flowers và tự thu thập) một dòng. Nạp từ manifest.csv bằng import_manifest.py."""
    __tablename__ = "dataset_images"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), unique=True, nullable=False)
    flower_id = db.Column(db.Integer, db.ForeignKey("flowers.id"), nullable=False)
    source = db.Column(db.String(20), nullable=False)            # tf_flowers | web
    keyword = db.Column(db.String(100))                          # từ khóa tìm ảnh (chỉ ảnh web)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    phash = db.Column(db.String(16))                             # perceptual hash, dạng hex
    status = db.Column(db.String(20), nullable=False, default="kept")  # kept | corrupt | small | duplicate | leak | manual
    split = db.Column(db.String(10))                             # train | val | test; ảnh bị loại để trống

    flower = db.relationship("Flower")
