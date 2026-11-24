from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Flower(db.Model):
    __tablename__ = "flowers"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name_vi = db.Column(db.String(50), nullable=False)
    name_en = db.Column(db.String(50), nullable=False)
    scientific_name = db.Column(db.String(80))
    hue = db.Column(db.SmallInteger, nullable=False)
    description = db.Column(db.Text)
    meaning = db.Column(db.Text)
    season = db.Column(db.String(100))

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name_vi": self.name_vi,
            "name_en": self.name_en,
            "scientific": self.scientific_name,
            "hue": self.hue,
            "description": self.description,
            "meaning": self.meaning,
            "season": self.season,
        }


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    flower_id = db.Column(db.Integer, db.ForeignKey("flowers.id"), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    image_id = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    model_version = db.Column(db.String(20), nullable=False)
    threshold = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)

    flower = db.relationship("Flower")
    # 3 dòng top 3 của lần phân loại này, xếp theo hạng; xóa lần phân loại thì 3 dòng này tự xóa theo
    scores = db.relationship(
        "PredictionScore",
        back_populates="prediction",
        order_by="PredictionScore.ranking",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_dict(self, detail=False):
        data = {
            "id": self.id,
            "flower": {"id": self.flower.id, "name_vi": self.flower.name_vi, "hue": self.flower.hue},
            "confidence": self.confidence,
            "threshold": self.threshold,
            "uncertain": self.confidence < self.threshold,
            "image_url": self.image_url,
            "original_name": self.original_name,
            "created_at": self.created_at.isoformat(timespec="seconds"),
        }
        if detail:
            data["flower"] = self.flower.to_dict()
            data["file_size"] = self.file_size
            data["model_version"] = self.model_version
            top = []
            for score in self.scores:
                item = score.flower.to_dict()
                item["confidence"] = score.confidence
                top.append(item)
            data["top"] = top
        return data


class PredictionScore(db.Model):
    __tablename__ = "prediction_scores"
    __table_args__ = (db.UniqueConstraint("prediction_id", "ranking"),)

    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False)
    ranking = db.Column(db.SmallInteger, nullable=False)
    flower_id = db.Column(db.Integer, db.ForeignKey("flowers.id"), nullable=False)
    confidence = db.Column(db.Float, nullable=False)

    prediction = db.relationship("Prediction", back_populates="scores")
    flower = db.relationship("Flower")
