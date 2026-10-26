"""Chia ảnh web đã làm sạch thành train/val/test và gộp với TF Flowers để huấn luyện lại.

Làm 5 việc theo thứ tự:
  1. Ghi trạng thái ảnh web theo chỗ file đang nằm: data/clean/ -> kept, data/removed/clip/ -> clip,
     data/removed/manual/ -> manual. Duyệt tay chỉ là kéo file giữa các thư mục, không cần ghi chép gì thêm.
  2. Chia ảnh web mỗi loài 70/15/15 vào data/web_split/{train,val,test}/, seed cố định 42 như notebook 01.
  3. data/combined/train = TF train + web train, data/combined/val = TF val + web val.
     Không gộp test: giữ riêng TF test (so v1 với v2 công bằng) và web test ("ảnh thực tế").
  4. Nén data/combined.zip và data/web_test.zip để đưa lên Drive.
  5. Ghi cột split vào manifest.csv. Sau đó chạy import_manifest.py để nạp vào CSDL.

Chạy ở thư mục gốc dự án:  python data_tool/split.py
Chạy lại được: data/web_split/ và data/combined/ do script này tạo ra, nên mỗi lần chạy được xóa và tạo lại từ đầu.
Người phụ trách: Hân
"""
import random
import shutil
from collections import Counter
from pathlib import Path

from common import CLEAN_DIR, DATA, FLOWERS, REMOVED_DIR, SPLITS, print_table, read_manifest, write_manifest

SEED = 42
WEB_SPLIT_DIR = DATA / "web_split"
COMBINED_DIR = DATA / "combined"
MIN_WEB_IMAGES = 300     # mục tiêu tối thiểu mỗi loài


def sync_with_folders(rows):
    """Bước 1: trạng thái ảnh web theo thư mục đang chứa file. Ảnh CLIP gắn cờ mà được kéo về clean/ thì lại là kept."""
    places = {"kept": CLEAN_DIR, "clip": REMOVED_DIR / "clip", "manual": REMOVED_DIR / "manual"}
    for row in rows:
        if row["source"] != "web" or row["status"] not in places:
            continue                                   # ảnh TF Flowers và ảnh clean.py đã loại: giữ nguyên
        name = Path(row["filename"]).name
        row["status"] = "manual"                        # không tìm thấy ở đâu (lỡ xóa) thì coi như bỏ tay
        row["filename"] = f"removed/manual/{row['flower']}/{name}"
        for status, folder in places.items():
            if (folder / row["flower"] / name).exists():
                row["status"] = status
                row["filename"] = (folder / row["flower"] / name).relative_to(DATA).as_posix()
                break
    return Counter(row["status"] for row in rows if row["source"] == "web")


def assign_splits(rows):
    """Bước 2: chia ảnh web kept của từng loài theo tỉ lệ 70/15/15."""
    for flower in FLOWERS:
        kept = [row for row in rows if row["source"] == "web" and row["flower"] == flower and row["status"] == "kept"]
        kept.sort(key=lambda row: row["filename"])   # cùng danh sách ảnh -> cùng kết quả chia
        random.Random(SEED).shuffle(kept)            # mỗi loài một bộ sinh số riêng: loài này đổi không ảnh hưởng loài khác
        n_train = round(len(kept) * 0.70)
        n_val = round(len(kept) * 0.15)
        for i, row in enumerate(kept):
            row["split"] = "train" if i < n_train else "val" if i < n_train + n_val else "test"

    for row in rows:
        if row["status"] != "kept":
            row["split"] = ""                        # ảnh bị loại không thuộc tập nào


def copy_files(rows):
    """Bước 3: chép ảnh vào web_split/ và combined/."""
    for folder in (WEB_SPLIT_DIR, COMBINED_DIR):
        if folder.exists():
            shutil.rmtree(folder)

    for row in rows:
        if row["status"] != "kept":
            continue
        targets = []
        if row["source"] == "web":
            targets.append(WEB_SPLIT_DIR / row["split"] / row["flower"])
        if row["split"] in ("train", "val"):         # cả TF lẫn web; test không gộp
            targets.append(COMBINED_DIR / row["split"] / row["flower"])

        source = DATA / row["filename"]
        for folder in targets:
            folder.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, folder / source.name)


def make_zips():
    """Bước 4: nén để đưa lên Drive, cạnh tf_flowers_split.zip."""
    shutil.make_archive(str(DATA / "combined"), "zip", root_dir=DATA, base_dir="combined")
    shutil.make_archive(str(DATA / "web_test"), "zip", root_dir=DATA, base_dir="web_split/test")


if __name__ == "__main__":
    rows = read_manifest()
    web_kept = [row for row in rows if row["source"] == "web" and row["status"] == "kept"]
    if not web_kept:
        raise SystemExit("manifest.csv chưa có ảnh web: chạy crawl.py rồi clean.py trước.")

    status_counts = sync_with_folders(rows)
    print(f"Ảnh web: giữ {status_counts['kept']}, CLIP loại {status_counts['clip']}, bỏ tay {status_counts['manual']}")
    assign_splits(rows)
    print("Đang chép ảnh vào data/web_split/ và data/combined/…")
    copy_files(rows)
    print("Đang nén data/combined.zip và data/web_test.zip…")
    make_zips()
    write_manifest(rows)                             # bước 5

    web = Counter((row["flower"], row["split"]) for row in rows if row["source"] == "web" and row["status"] == "kept")
    print_table("Ảnh web đã chia (data/web_split):", web, SPLITS)
    combined = Counter((row["flower"], row["split"]) for row in rows
                       if row["status"] == "kept" and row["split"] in ("train", "val"))
    print_table("TF Flowers + web (data/combined):", combined, ["train", "val"])

    for flower in FLOWERS:
        total = sum(web[(flower, split)] for split in SPLITS)
        if total < MIN_WEB_IMAGES:
            print(f"Cảnh báo: {flower} mới có {total} ảnh web, dưới {MIN_WEB_IMAGES}. Thêm từ khóa rồi chạy lại crawl.py, clean.py.")

    print("\nTiếp theo: đưa data/combined.zip và data/web_test.zip lên Drive, rồi chạy python data_tool/import_manifest.py")
