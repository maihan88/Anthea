"""Tạo bảng (nếu chưa có) và chèn thông tin các lớp của mô hình: 5 loài hoa + lớp "Khác".

Chạy ở thư mục gốc dự án:  python app/seed.py
Chạy lại bao nhiêu lần cũng được: chưa có thì thêm, có rồi thì cập nhật, mục không còn trong FLOWERS thì xóa.
Người phụ trách: Hân (Nghi duyệt)
"""
import json

from flask import Flask

import config
from database import Flower, db

# id cố định 1–6 theo đúng thứ tự models/class_names.json, nên các link /flowers/3… luôn đúng
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
    # Lớp "Khác" của mô hình: ảnh không phải hoa, hoặc hoa ngoài 5 loài.
    # Không phải một loài hoa nên không hiện trong Thư viện hoa
    {"id": 6, "code": "other", "name_vi": "Khác", "name_en": "Other",
     "scientific_name": None, "hue": 220,
     "description": "Ảnh không thuộc 5 loài hoa Anthea nhận diện: không phải hoa, hoặc là hoa loài khác.",
     "meaning": None, "season": None},
]


def check_class_order():
    """FLOWERS phải trùng class_names.json: đúng thứ tự, id lần lượt 1, 2, 3…"""
    class_names = json.loads((config.BASE / "models" / "class_names.json").read_text(encoding="utf-8"))
    codes = [(f["id"], f["code"]) for f in FLOWERS]
    expected = list(enumerate(class_names, start=1))
    assert codes == expected, f"FLOWERS lệch class_names.json: {codes} ≠ {expected}"


def seed():
    check_class_order()
    db.create_all()

    # Xóa mục cũ không còn trong FLOWERS (ví dụ hoa sen của bản trước), hoặc có id khác với FLOWERS.
    # Mục đã có lịch sử phân loại thì MySQL không cho xóa và sẽ báo lỗi.
    wanted_ids = {f["code"]: f["id"] for f in FLOWERS}
    for flower in db.session.scalars(db.select(Flower)).all():
        if wanted_ids.get(flower.code) != flower.id:
            db.session.delete(flower)
    db.session.commit()

    # merge: id chưa có thì thêm dòng mới, có rồi thì cập nhật cho giống FLOWERS
    for data in FLOWERS:
        db.session.merge(Flower(**data))
    db.session.commit()


if __name__ == "__main__":
    # App Flask tối giản: chỉ cần kết nối CSDL, khỏi nạp TensorFlow như app.py
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    with app.app_context():
        seed()
        for f in db.session.scalars(db.select(Flower).order_by(Flower.id)):
            print(f"{f.id}  {f.code:11} {f.name_vi}")
        print(f"Xong: bảng {', '.join(sorted(db.metadata.tables))} đã sẵn sàng.")
