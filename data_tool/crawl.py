"""Tải ảnh hoa từ iNaturalist theo các loài trong keywords.json.

iNaturalist là trang ghi nhận thiên nhiên: mỗi quan sát có ảnh chụp và tên loài do cộng đồng xác nhận.
API công khai, không cần tài khoản: https://api.inaturalist.org/v1/docs/
  - Chỉ lấy ảnh có giấy phép Creative Commons, mỗi quan sát một ảnh, cỡ medium (cạnh dài 500 px).
  - Mặc định chỉ lấy quan sát được chú thích "đang ra hoa", để ảnh có bông hoa chứ không chỉ có lá.
  - "params" trong keywords.json thêm điều kiện riêng cho từng loài:
      bồ công anh  term_value_id = 13,14  lấy cả hoa vàng lẫn quả cầu lông trắng, như bộ gốc
      hoa hồng     captive = true         hồng trồng trong vườn, bỏ hồng dại 5 cánh

Ảnh lưu vào data/raw/<loài>/inaturalist_<tên loài>/<mã ảnh>.jpg.
Mỗi loài ghi một dòng vào data/crawl_log.csv; nguồn và giấy phép từng ảnh ghi vào data/inat_sources.csv (để ghi nguồn trong báo cáo).

Chạy ở thư mục gốc dự án:
    python data_tool/crawl.py                     # tất cả các loài, số ảnh theo "max" trong keywords.json
    python data_tool/crawl.py roses tulips        # chỉ vài loài
    python data_tool/crawl.py daisy --max 20      # chạy thử: 20 ảnh mỗi loài

Chạy lại được: ảnh đã có (cùng mã ảnh) thì bỏ qua, chỉ tải phần còn thiếu cho đủ "max".
Ảnh tải từ Bing trước đó (các thư mục khác trong data/raw/) giữ nguyên, clean.py làm sạch chung.
Người phụ trách: Hân
"""
import argparse
import csv
import json
import time
from datetime import date

import requests

from common import BASE, CRAWL_LOG, DATA, FLOWERS, RAW_DIR, folder_name, list_images

KEYWORDS_FILE = BASE / "data_tool" / "keywords.json"
SOURCES_FILE = DATA / "inat_sources.csv"
API_URL = "https://api.inaturalist.org/v1/observations"
session = requests.Session()                    # dùng chung một kết nối: tải nhanh hơn nhiều so với mở mới mỗi ảnh
session.headers["User-Agent"] = "Anthea (do an sinh vien: phan loai 5 loai hoa)"


def fetch_observations(taxon, page):
    """Một trang (200 quan sát) của loài này, mới nhất trước."""
    params = {
        "taxon_id": taxon["taxon_id"],
        "photos": "true",
        "photo_licensed": "true",               # chỉ ảnh có giấy phép Creative Commons
        "term_id": 12, "term_value_id": 13,     # chú thích "Hoa và quả" = "Đang ra hoa"
        "per_page": 200, "page": page,
    }
    params.update(taxon.get("params", {}))
    time.sleep(1)                               # iNaturalist đề nghị tối đa khoảng 1 lần gọi API mỗi giây
    response = session.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()["results"]


def download(url, path):
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"  bỏ qua {url}: {error}")
        return False
    path.write_bytes(response.content)
    return True


def write_csv_row(file, header, row):
    """Ghi nối một dòng vào file CSV, file mới thì ghi thêm dòng tiêu đề."""
    is_new = not file.exists()
    with open(file, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        if is_new:
            writer.writerow(header)
        writer.writerow(row)


def crawl_taxon(flower, taxon, max_num):
    """Tải cho đủ max_num ảnh của một loài trên iNaturalist. Trả số ảnh đang có trong thư mục."""
    keyword = f"iNaturalist: {taxon['name']}"
    folder = RAW_DIR / flower / folder_name(keyword)        # inaturalist_bellis_perennis
    folder.mkdir(parents=True, exist_ok=True)
    count = len(list_images(folder))

    page = 1
    while count < max_num:
        observations = fetch_observations(taxon, page)
        if not observations:
            break                                           # iNaturalist hết ảnh thỏa điều kiện
        for obs in observations:
            photo = obs["photos"][0]                        # các ảnh sau thường chụp lại cùng một cây
            path = folder / f"{photo['id']}.jpg"
            if path.exists():
                continue
            if download(photo["url"].replace("square", "medium"), path):
                write_csv_row(SOURCES_FILE, ["flower", "file", "observation", "license", "attribution"], [
                    flower, path.relative_to(DATA).as_posix(),
                    f"https://www.inaturalist.org/observations/{obs['id']}",
                    photo["license_code"], photo["attribution"],
                ])
                count += 1
            if count >= max_num:
                break
        page += 1

    write_csv_row(CRAWL_LOG, ["date", "flower", "keyword", "requested", "downloaded"],
                  [date.today().isoformat(), flower, keyword, max_num, count])
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tải ảnh hoa từ iNaturalist")
    parser.add_argument("flowers", nargs="*", default=FLOWERS, help="mã loài, bỏ trống = tất cả")
    parser.add_argument("--max", type=int, help="số ảnh mỗi loài trên iNaturalist, bỏ trống = theo keywords.json")
    args = parser.parse_args()

    keywords = json.loads(KEYWORDS_FILE.read_text(encoding="utf-8"))
    for flower in args.flowers:
        if flower not in FLOWERS:
            raise SystemExit(f"Không có loài '{flower}'. Các mã loài: {', '.join(FLOWERS)}")

        for taxon in keywords[flower]:
            max_num = args.max or taxon["max"]
            count = crawl_taxon(flower, taxon, max_num)
            print(f"{flower:11} {taxon['name']:22} có {count}/{max_num} ảnh")

    print(f"\nXong. Số ảnh từng loài: {CRAWL_LOG.relative_to(BASE)}; nguồn từng ảnh: {SOURCES_FILE.relative_to(BASE)}")
