"""Làm sạch tự động ảnh thô trong data/raw/.

Mỗi ảnh đi qua 5 trạm theo thứ tự; trượt trạm nào thì chép sang data/removed/<lý do>/<loài>/ và dừng ở đó:
  1. corrupt    không mở được (file hỏng, file bị cắt cụt)
  2. small      cạnh ngắn dưới 100 px
  3. chuẩn hóa  về RGB, xoay đúng chiều, thu nhỏ ảnh quá lớn — trạm này không loại ảnh
  4. duplicate  trùng một ảnh web đã giữ (phash lệch ≤ 5 bit)
  5. leak       trùng một ảnh val/test của TF Flowers: lọt vào train là mô hình được "xem trước đề"
Ảnh qua hết được lưu vào data/clean/<loài>/<loài>_web_0001.jpg… Mỗi ảnh, giữ hay loại, một dòng trong manifest.csv.

Chạy ở thư mục gốc dự án:  python data_tool/clean.py
Chạy lại được: ảnh thô đã có trong manifest (cột raw_file) thì bỏ qua, ảnh mới vẫn được so trùng với ảnh cũ.
Không xóa gì: data/raw/ giữ nguyên, ảnh bị loại là bản chép.
Người phụ trách: Hân
"""
import csv
import shutil
from collections import Counter

import imagehash
from PIL import Image, ImageOps

from common import (CLEAN_DIR, CRAWL_LOG, DATA, FLOWERS, RAW_DIR, REMOVED_DIR, folder_name, list_images,
                    print_table, read_manifest, write_manifest)

MIN_SIDE = 100       # theo đặc tả; nếu còn dư ảnh có thể nâng lên 150
MAX_SIDE = 800       # mô hình chỉ cần 180×180, thu nhỏ ảnh lớn cho file zip nhẹ
MAX_DISTANCE = 5     # hai phash lệch nhau ≤ 5 bit coi là cùng một ảnh
STATUSES = ["kept", "corrupt", "small", "duplicate", "leak"]


def open_image(path):
    """Mở và giải mã hết ảnh. File hỏng thì trả None."""
    try:
        with Image.open(path) as img:
            img.verify()             # kiểm tra cấu trúc file
        img = Image.open(path)       # sau verify() phải mở lại mới dùng được
        img.load()                   # giải mã thật sự: bắt được file bị cắt cụt giữa chừng
        return img
    except Exception:
        return None


def normalize(img):
    """Về ảnh RGB, đúng chiều, cạnh dài tối đa MAX_SIDE."""
    img = ImageOps.exif_transpose(img)       # ảnh điện thoại hay ghi chiều xoay trong EXIF
    if img.mode in ("RGBA", "LA", "P"):
        # PNG nền trong suốt: dán lên nền trắng, chuyển thẳng sang RGB sẽ ra nền đen
        img = img.convert("RGBA")
        white = Image.new("RGB", img.size, "white")
        white.paste(img, mask=img.getchannel("A"))
        img = white
    else:
        img = img.convert("RGB")             # CMYK, ảnh xám… -> RGB. GIF động: Pillow chỉ lấy khung đầu
    img.thumbnail((MAX_SIDE, MAX_SIDE))      # chỉ thu nhỏ, giữ tỉ lệ
    return img


def read_keyword_names():
    """Tên thư mục -> từ khóa gốc, đọc từ crawl_log.csv: ('roses', 'hoa_hong') -> 'hoa hồng'."""
    with open(CRAWL_LOG, encoding="utf-8-sig", newline="") as f:
        return {(row["flower"], folder_name(row["keyword"])): row["keyword"] for row in csv.DictReader(f)}


def is_similar(hash_value, hash_list):
    """Có hash nào trong danh sách lệch ≤ MAX_DISTANCE bit không (khoảng cách Hamming)."""
    return any((hash_value ^ other).bit_count() <= MAX_DISTANCE for other in hash_list)


def check(path, kept_hashes, test_val_hashes):
    """Cho ảnh đi qua 5 trạm. Trả (trạng thái, ảnh đã chuẩn hóa hoặc None, kích thước gốc, phash)."""
    img = open_image(path)
    if img is None:
        return "corrupt", None, ("", ""), ""
    size = img.size
    if min(size) < MIN_SIDE:
        return "small", None, size, ""

    img = normalize(img)
    phash = str(imagehash.phash(img))
    hash_value = int(phash, 16)              # đổi hex sang số nguyên để so bằng phép XOR cho nhanh
    if is_similar(hash_value, kept_hashes):
        return "duplicate", None, size, phash
    if is_similar(hash_value, test_val_hashes):
        return "leak", None, size, phash
    return "kept", img, size, phash


def clean_flower(flower, rows, keyword_names, kept_hashes, test_val_hashes):
    """Làm sạch ảnh thô mới của một loài, thêm dòng vào rows. Trả Counter số ảnh theo trạng thái."""
    done = {row["raw_file"] for row in rows if row["raw_file"]}
    keyword_folders = sorted((RAW_DIR / flower).glob("*/"))     # loài chưa tải ảnh thì danh sách rỗng
    new_files = [path for folder in keyword_folders for path in list_images(folder)
                 if path.relative_to(DATA).as_posix() not in done]
    # File lớn xử lý trước: trong một nhóm ảnh trùng, ảnh được giữ là ảnh lớn nhất
    new_files.sort(key=lambda path: path.stat().st_size, reverse=True)
    print(f"{flower}: {len(new_files)} ảnh mới…")

    # Đánh số tiếp theo các ảnh web đã có của loài này (cả ảnh bị loại), nên tên không bao giờ trùng
    number = sum(1 for row in rows if row["source"] == "web" and row["flower"] == flower)
    counts = Counter()
    for path in new_files:
        number += 1
        status, img, (width, height), phash = check(path, kept_hashes, test_val_hashes)
        name = f"{flower}_web_{number:04d}"

        if status == "kept":
            dest = CLEAN_DIR / flower / f"{name}.jpg"
            dest.parent.mkdir(parents=True, exist_ok=True)
            img.save(dest, "JPEG", quality=95)
            kept_hashes.append(int(phash, 16))
        else:
            dest = REMOVED_DIR / status / flower / f"{name}{path.suffix.lower()}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)

        counts[status] += 1
        rows.append({
            "filename": dest.relative_to(DATA).as_posix(),
            "flower": flower, "source": "web",
            "keyword": keyword_names.get((flower, path.parent.name), path.parent.name),
            "width": width, "height": height,          # kích thước gốc lúc tải về
            "phash": phash, "status": status, "split": "",
            "raw_file": path.relative_to(DATA).as_posix(),
        })
    return counts


if __name__ == "__main__":
    rows = read_manifest()
    if not any(row["source"] == "tf_flowers" for row in rows):
        raise SystemExit("manifest.csv chưa có ảnh TF Flowers: chạy python data_tool/build_tf_manifest.py trước.")

    if not CRAWL_LOG.exists():
        raise SystemExit("Chưa có data/crawl_log.csv: chạy python data_tool/crawl.py trước.")
    keyword_names = read_keyword_names()    # để manifest ghi "hoa hồng" thay vì "hoa_hong"

    kept_hashes = [int(row["phash"], 16) for row in rows if row["source"] == "web" and row["status"] == "kept"]
    test_val_hashes = [int(row["phash"], 16) for row in rows
                       if row["source"] == "tf_flowers" and row["split"] in ("val", "test")]

    run_counts = Counter()
    for flower in FLOWERS:
        counts = clean_flower(flower, rows, keyword_names, kept_hashes, test_val_hashes)
        run_counts.update({(flower, status): n for status, n in counts.items()})
        write_manifest(rows)                 # ghi sau mỗi loài: lỡ dừng giữa chừng cũng không mất phần đã làm

    print_table("Lần chạy này (tổng = số ảnh mới xử lý):", run_counts, STATUSES)
    all_counts = Counter((row["flower"], row["status"]) for row in rows if row["source"] == "web")
    print_table("Toàn bộ ảnh web trong manifest:", all_counts, STATUSES)
    print("\nMỗi loài cần ≥ 300 ảnh kept sau khi duyệt tay. Tiếp theo: chạy screen.py để CLIP sàng lọc trước.")
