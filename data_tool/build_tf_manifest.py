"""Lập manifest cho bản chia TF Flowers: mỗi ảnh một dòng trong data_tool/manifest.csv.

Cần có data/tf_flowers_split/{train,val,test}/<loài>/ (giải nén tf_flowers_split.zip từ Drive).
Chạy ở thư mục gốc dự án:  python data_tool/build_tf_manifest.py
Chạy lại được: chỉ viết lại các dòng tf_flowers, các dòng ảnh web (nếu đã có) giữ nguyên.
Người phụ trách: Hân
"""
import json
from collections import Counter

import imagehash
from PIL import Image

from common import BASE, DATA, FLOWERS, SPLITS, TF_DIR, list_images, print_table, read_manifest, write_manifest


def build_rows():
    rows = []
    for split in SPLITS:
        for flower in FLOWERS:
            for path in list_images(TF_DIR / split / flower):
                with Image.open(path) as img:
                    width, height = img.size
                    phash = str(imagehash.phash(img))   # clean.py dùng hash ảnh test/val để bắt ảnh web bị rò rỉ
                rows.append({
                    "filename": path.relative_to(DATA).as_posix(),   # tf_flowers_split/train/roses/xxx.jpg
                    "flower": flower, "source": "tf_flowers", "keyword": "",
                    "width": width, "height": height, "phash": phash,
                    "status": "kept", "split": split, "raw_file": "",
                })
            print(f"  {split}/{flower}: xong")
    return rows


def check_with_model_info(rows):
    """Số ảnh theo tập và loài phải khớp num_images trong models/model_info.json (số notebook 01 đã train)."""
    counts = Counter((row["split"], row["flower"]) for row in rows)
    actual = {split: {flower: counts[(split, flower)] for flower in FLOWERS} for split in SPLITS}
    model_info = json.loads((BASE / "models" / "model_info.json").read_text(encoding="utf-8"))
    if actual == model_info["num_images"]:
        print("\nKhớp num_images trong model_info.json.")
    else:
        print("\nLỆCH num_images trong model_info.json — kiểm tra lại thư mục data/tf_flowers_split/!")


if __name__ == "__main__":
    if not TF_DIR.exists():
        raise SystemExit(f"Chưa có {TF_DIR}: tải tf_flowers_split.zip từ Drive và giải nén vào đó.")

    print("Đang tính kích thước và phash cho ảnh TF Flowers…")
    tf_rows = build_rows()
    web_rows = [row for row in read_manifest() if row["source"] != "tf_flowers"]
    write_manifest(tf_rows + web_rows)

    print_table("Số ảnh TF Flowers:", Counter((row["flower"], row["split"]) for row in tf_rows), SPLITS)
    check_with_model_info(tf_rows)
    print(f"Đã ghi {len(tf_rows)} dòng tf_flowers (giữ {len(web_rows)} dòng web) vào data_tool/manifest.csv")
