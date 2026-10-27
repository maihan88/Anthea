"""Nạp data_tool/manifest.csv vào bảng dataset_images.

Cần chạy python app/seed.py trước (tạo bảng và 6 loài hoa).
Chạy ở thư mục gốc dự án:  python data_tool/import_manifest.py
Chạy lại bao nhiêu lần cũng được: bảng được xóa sạch rồi nạp lại từ manifest, nên luôn giống hệt file.
Không bảng nào trỏ tới dataset_images.id, nên id đổi sau mỗi lần nạp cũng không sao.
Người phụ trách: Hân
"""
import sys

from flask import Flask

from common import BASE, print_table, read_manifest

sys.path.insert(0, str(BASE / "app"))   # để import được config.py, database.py của web
import config
from database import DatasetImage, Flower, db


def to_int(text):
    return int(text) if text else None   # ảnh hỏng không có kích thước


def import_rows(rows):
    flower_ids = {f.code: f.id for f in db.session.scalars(db.select(Flower))}
    if not flower_ids:
        raise SystemExit("Bảng flowers đang trống: chạy python app/seed.py trước.")

    records = [{
        "filename": row["filename"],
        "flower_id": flower_ids[row["flower"]],
        "source": row["source"],
        "keyword": row["keyword"] or None,
        "width": to_int(row["width"]),
        "height": to_int(row["height"]),
        "phash": row["phash"] or None,
        "status": row["status"],
        "split": row["split"] or None,
    } for row in rows]

    # Xóa và thêm trong cùng một lần commit: lỗi giữa chừng thì bảng vẫn còn dữ liệu cũ
    db.session.execute(db.delete(DatasetImage))
    db.session.execute(db.insert(DatasetImage), records)
    db.session.commit()


def print_summary():
    """Đếm lại ngay trong CSDL — cùng kiểu truy vấn mà các API sẽ dùng."""
    kept = (db.select(Flower.code, DatasetImage.source, db.func.count())
            .join(DatasetImage.flower).where(DatasetImage.status == "kept")
            .group_by(Flower.code, DatasetImage.source))
    counts = {(code, source): n for code, source, n in db.session.execute(kept)}
    print_table("Ảnh đang dùng (status = kept) theo nguồn:", counts, ["tf_flowers", "web"])

    removed = (db.select(DatasetImage.status, db.func.count())
               .where(DatasetImage.status != "kept").group_by(DatasetImage.status))
    for status, n in db.session.execute(removed):
        print(f"  bị loại vì {status}: {n}")


if __name__ == "__main__":
    rows = read_manifest()
    if not rows:
        raise SystemExit("Chưa có data_tool/manifest.csv: chạy python data_tool/build_tf_manifest.py trước.")

    # App Flask tối giản: chỉ cần kết nối CSDL, giống seed.py
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    with app.app_context():
        import_rows(rows)
        total = db.session.scalar(db.select(db.func.count()).select_from(DatasetImage))
        print(f"Đã nạp {total} dòng vào dataset_images.")
        print_summary()
