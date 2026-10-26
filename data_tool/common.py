"""Đường dẫn và hàm dùng chung cho các script trong data_tool/.

Người phụ trách: Hân
"""
import csv
import json
import re
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
TF_DIR = DATA / "tf_flowers_split"          # bản chia TF Flowers giải nén từ Drive, chỉ đọc
RAW_DIR = DATA / "raw"                       # crawl.py ghi
CRAWL_LOG = DATA / "crawl_log.csv"           # crawl.py ghi: mỗi từ khóa / loài một dòng
CLEAN_DIR = DATA / "clean"                   # clean.py ghi
REMOVED_DIR = DATA / "removed"               # clean.py và người duyệt tay ghi
MANIFEST = BASE / "data_tool" / "manifest.csv"

SPLITS = ["train", "val", "test"]
FLOWERS = json.loads((BASE / "models" / "class_names.json").read_text(encoding="utf-8"))
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

# Cột 1–9 trùng tên cột bảng dataset_images (flower là mã loài, import_manifest.py đổi sang flower_id).
# raw_file: ảnh web lấy từ file nào trong data/raw/, để clean.py chạy lại không xử lý lại ảnh cũ.
COLUMNS = ["filename", "flower", "source", "keyword", "width", "height", "phash", "status", "split", "raw_file"]


def read_manifest():
    """Đọc manifest.csv thành danh sách dict; chưa có file thì trả danh sách rỗng."""
    if not MANIFEST.exists():
        return []
    # utf-8-sig: mở bằng Excel vẫn đúng tiếng Việt
    with open(MANIFEST, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_manifest(rows):
    with open(MANIFEST, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def folder_name(keyword):
    """'hoa hồng trắng' -> 'hoa_hong_trang'. Đường dẫn có dấu làm OpenCV đọc ảnh lỗi trên Windows."""
    text = keyword.lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)                               # tách dấu ra khỏi chữ: "ồ" -> "o" + 2 dấu
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")      # bỏ các dấu
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def list_images(folder):
    """Các file ảnh trong một thư mục (không đi vào thư mục con), sắp theo tên."""
    return sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in IMAGE_EXTS)


def print_table(title, counts, columns):
    """In bảng số ảnh: mỗi loài một dòng. counts[(loài, cột)] = số ảnh."""
    print(f"\n{title}")
    print(f"{'loài':12}" + "".join(f"{c:>11}" for c in columns) + f"{'tổng':>8}")
    for flower in FLOWERS:
        values = [counts.get((flower, c), 0) for c in columns]
        print(f"{flower:12}" + "".join(f"{v:>11}" for v in values) + f"{sum(values):>8}")
    totals = [sum(counts.get((f, c), 0) for f in FLOWERS) for c in columns]
    print(f"{'tổng':12}" + "".join(f"{v:>11}" for v in totals) + f"{sum(totals):>8}")
