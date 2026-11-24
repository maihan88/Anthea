import json

from flask import Flask

import config
from database import Flower, db

FLOWERS = [
    {"id": 1, "code": "daisy", "name_vi": "Cúc họa mi", "name_en": "Daisy",
     "scientific_name": "Bellis perennis", "hue": 140,
     "description": "Cánh trắng mảnh, xếp một vòng quanh nhụy vàng tròn ở giữa.",
     "meaning": "Sự ngây thơ, trong sáng và khởi đầu mới.",
     "season": "Cuối thu – đầu đông"},
    {"id": 2, "code": "dandelion", "name_vi": "Bồ công anh", "name_en": "Dandelion",
     "scientific_name": "Taraxacum officinale", "hue": 60,
     "description": "Hoa vàng gồm nhiều cánh nhỏ li ti; khi già kết thành quả cầu lông trắng.",
     "meaning": "Hy vọng, ước nguyện và sự tự do.",
     "season": "Mùa xuân – hè"},
    {"id": 3, "code": "roses", "name_vi": "Hoa hồng", "name_en": "Rose",
     "scientific_name": "Rosa spp.", "hue": 10,
     "description": "Cánh hoa xếp nhiều lớp xoắn quanh tâm, thân có gai, lá kép với mép răng cưa.",
     "meaning": "Tình yêu, sự trân trọng và lòng biết ơn.",
     "season": "Quanh năm, rộ nhất vào mùa xuân"},
    {"id": 4, "code": "sunflowers", "name_vi": "Hướng dương", "name_en": "Sunflower",
     "scientific_name": "Helianthus annuus", "hue": 85,
     "description": "Đĩa hoa lớn màu nâu ở giữa, cánh vàng tỏa tròn, thân cao và cứng.",
     "meaning": "Niềm tin, sự lạc quan, luôn hướng về ánh sáng.",
     "season": "Mùa hè đến đầu thu"},
    {"id": 5, "code": "tulips", "name_vi": "Tulip", "name_en": "Tulip",
     "scientific_name": "Tulipa", "hue": 345,
     "description": "Hoa hình chén với 6 cánh, thân thẳng, lá dài hình mũi mác.",
     "meaning": "Tình yêu hoàn hảo, sự sung túc.",
     "season": "Mùa xuân"},
    {"id": 6, "code": "other", "name_vi": "Khác", "name_en": "Other",
     "scientific_name": None, "hue": 220,
     "description": "Ảnh không thuộc 5 loài hoa Anthea nhận diện: không phải hoa, hoặc là hoa loài khác.",
     "meaning": None, "season": None},
]


def check_class_order():
    path = config.BASE / "models" / "class_names.json"
    class_names = json.loads(path.read_text(encoding="utf-8"))
    if len(class_names) != len(FLOWERS):
        raise SystemExit("Số lớp trong FLOWERS khác models/class_names.json")
    # id 1, 2, 3... phải đúng thứ tự lớp của mô hình
    for i in range(len(class_names)):
        if FLOWERS[i]["id"] != i + 1 or FLOWERS[i]["code"] != class_names[i]:
            raise SystemExit("FLOWERS không đúng thứ tự trong models/class_names.json")


def is_in_flowers(flower):
    for data in FLOWERS:
        if data["id"] == flower.id and data["code"] == flower.code:
            return True
    return False


def seed():
    check_class_order()
    db.create_all()

    # Xóa loài đã bỏ khỏi FLOWERS
    for flower in db.session.scalars(db.select(Flower)).all():
        if not is_in_flowers(flower):
            db.session.delete(flower)
    db.session.commit()

    # merge: chưa có id này thì thêm, có rồi thì cập nhật
    for data in FLOWERS:
        flower = Flower(
            id=data["id"],
            code=data["code"],
            name_vi=data["name_vi"],
            name_en=data["name_en"],
            scientific_name=data["scientific_name"],
            hue=data["hue"],
            description=data["description"],
            meaning=data["meaning"],
            season=data["season"],
        )
        db.session.merge(flower)
    db.session.commit()


if __name__ == "__main__":
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    with app.app_context():
        seed()
        for flower in db.session.scalars(db.select(Flower).order_by(Flower.id)):
            print(flower.id, flower.code, flower.name_vi)
        print("Xong: đã tạo bảng và nạp", len(FLOWERS), "lớp.")
