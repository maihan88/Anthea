"""Tạo bảng (nếu chưa có) và chèn thông tin các loài hoa.

Chạy ở thư mục gốc dự án:  python app/seed.py
Chạy lại bao nhiêu lần cũng được: có mã loài rồi thì cập nhật, chưa có thì thêm.
Người phụ trách: Hân (Nghi duyệt)
"""
import json

from flask import Flask

import config
from database import Flower, db

# id cố định 1–5 theo đúng thứ tự models/class_names.json, nên các link /flowers/3… luôn đúng
FLOWERS = [
    {"id": 1, "code": "daisy", "name_vi": "Cúc họa mi", "name_en": "Daisy",
     "scientific_name": "Bellis perennis", "hue": 140,
     "description": "Cánh trắng mảnh, xếp một vòng quanh nhụy vàng tròn ở giữa.",
     "meaning": "Sự ngây thơ, trong sáng và khởi đầu mới.",
     "season": "Cuối thu – đầu đông", "in_model": True},
    {"id": 2, "code": "dandelion", "name_vi": "Bồ công anh", "name_en": "Dandelion",
     "scientific_name": "Taraxacum officinale", "hue": 60,
     "description": "Hoa vàng gồm nhiều cánh nhỏ li ti; khi già kết thành quả cầu lông trắng.",
     "meaning": "Hy vọng, ước nguyện và sự tự do.",
     "season": "Mùa xuân – hè", "in_model": True},
    {"id": 3, "code": "roses", "name_vi": "Hoa hồng", "name_en": "Rose",
     "scientific_name": "Rosa spp.", "hue": 10,
     "description": "Cánh hoa xếp nhiều lớp xoắn quanh tâm, thân có gai, lá kép với mép răng cưa.",
     "meaning": "Tình yêu, sự trân trọng và lòng biết ơn.",
     "season": "Quanh năm, rộ nhất vào mùa xuân", "in_model": True},
    {"id": 4, "code": "sunflowers", "name_vi": "Hướng dương", "name_en": "Sunflower",
     "scientific_name": "Helianthus annuus", "hue": 85,
     "description": "Đĩa hoa lớn màu nâu ở giữa, cánh vàng tỏa tròn, thân cao và cứng.",
     "meaning": "Niềm tin, sự lạc quan, luôn hướng về ánh sáng.",
     "season": "Mùa hè đến đầu thu", "in_model": True},
    {"id": 5, "code": "tulips", "name_vi": "Tulip", "name_en": "Tulip",
     "scientific_name": "Tulipa", "hue": 345,
     "description": "Hoa hình chén với 6 cánh, thân thẳng, lá dài hình mũi mác.",
     "meaning": "Tình yêu hoàn hảo, sự sung túc.",
     "season": "Mùa xuân", "in_model": True},
    # Mô hình chưa học hoa sen: thẻ "Sắp có". Thêm vào mô hình thì đổi in_model thành True
    {"id": 6, "code": "lotus", "name_vi": "Hoa sen", "name_en": "Lotus",
     "scientific_name": "Nelumbo nucifera", "hue": 5,
     "description": "Cánh hồng hoặc trắng xếp nhiều lớp quanh gương sen vàng; lá tròn, to, nổi trên mặt nước.",
     "meaning": "Sự thanh cao, thuần khiết.",
     "season": "Mùa hè", "in_model": False},
]


def check_class_order():
    """Các loài in_model phải trùng thứ tự class_names.json, id lần lượt 1, 2, 3…"""
    class_names = json.loads((config.BASE / "models" / "class_names.json").read_text(encoding="utf-8"))
    in_model = [(f["id"], f["code"]) for f in FLOWERS if f["in_model"]]
    expected = list(enumerate(class_names, start=1))
    assert in_model == expected, f"FLOWERS lệch class_names.json: {in_model} ≠ {expected}"


def seed():
    check_class_order()
    db.create_all()
    for data in FLOWERS:
        flower = db.session.scalar(db.select(Flower).filter_by(code=data["code"]))
        if flower is None:
            db.session.add(Flower(**data))
        else:
            for key, value in data.items():
                if key != "id":
                    setattr(flower, key, value)
    db.session.commit()


if __name__ == "__main__":
    # App Flask tối giản: chỉ cần kết nối CSDL, khỏi nạp TensorFlow như app.py
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    with app.app_context():
        seed()
        for f in db.session.scalars(db.select(Flower).order_by(Flower.id)):
            print(f"{f.id}  {f.code:11} {f.name_vi:12} {'trong mô hình' if f.in_model else 'sắp có'}")
        print(f"Xong: bảng {', '.join(sorted(db.metadata.tables))} đã sẵn sàng.")
