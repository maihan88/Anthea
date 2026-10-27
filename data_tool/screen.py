"""Sàng lọc ảnh web bằng CLIP: ảnh không giống "ảnh chụp hoa X" chuyển sang data/removed/clip/<loài>/ để duyệt lại.

CLIP (của OpenAI) đã học hàng trăm triệu cặp ảnh – câu mô tả, nên cho biết một ảnh khớp với câu nào nhất.
Mỗi ảnh được so với các câu trong PROMPTS: ảnh của từng loài trong 5 loài, và vài kiểu ảnh không dùng được
(bãi cỏ, luống vườn nhiều loài, nhà cửa, tranh vẽ…). Điểm của ảnh = xác suất CLIP chọn câu đúng loài của ảnh.
Điểm dưới THRESHOLD thì chuyển ảnh đi.

CLIP chỉ là máy đoán, nên đây là bước giảm việc chứ không thay người duyệt:
  - Xem data/removed/clip/<loài>/: ảnh dùng được thì kéo về data/clean/<loài>/, còn lại để nguyên.
  - Lướt nhanh data/clean/<loài>/: ảnh hỏng còn sót thì kéo vào data/removed/manual/<loài>/.
split.py xem file đang nằm ở đâu để ghi trạng thái (kept / clip / manual), nên không cần ghi chép gì.

Chạy sau clean.py:  python data_tool/screen.py
Chạy lại được: ảnh đã chấm (có trong data/clip_scores.csv) thì bỏ qua, nên ảnh đã kéo về không bị chuyển đi lần nữa.
Lần chạy đầu tải mô hình CLIP (khoảng 600 MB) về máy.
Người phụ trách: Hân
"""
import csv
import shutil
from collections import Counter

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from common import CLEAN_DIR, DATA, FLOWERS, REMOVED_DIR, list_images, print_table

MODEL_NAME = "openai/clip-vit-base-patch32"
SCORES_FILE = DATA / "clip_scores.csv"
THRESHOLD = 0.5
BATCH_SIZE = 32

# (loài, câu mô tả). Loài None = kiểu ảnh không dùng được. CLIP học chủ yếu bằng tiếng Anh nên câu viết tiếng Anh.
PROMPTS = [
    ("daisy", "a photo of a daisy flower"),
    ("dandelion", "a photo of a yellow dandelion flower"),
    ("dandelion", "a photo of a dandelion seed head"),     # bộ gốc có cả quả cầu lông trắng
    ("roses", "a photo of a rose flower"),
    ("sunflowers", "a photo of a sunflower"),
    ("sunflowers", "a photo of a field of sunflowers"),
    ("tulips", "a photo of a tulip flower"),
    ("tulips", "a photo of a field of tulips"),          # thiếu câu này, CLIP coi luống tulip là "luống vườn nhiều loài"
    (None, "a photo of a lawn or a grass field"),
    (None, "a photo of a garden bed with many different flowers"),
    (None, "a photo of a building, a street or a landscape"),
    (None, "a photo of green leaves without flowers"),
    (None, "a drawing or painting of flowers"),
    (None, "an image with text or a watermark"),
    (None, "a photo of a person"),
]


def score_images(model, processor, paths):
    """Chấm từng ảnh. Trả danh sách (điểm của đúng loài, câu CLIP chọn nhiều nhất)."""
    texts = [text for _, text in PROMPTS]
    results = []
    for start in range(0, len(paths), BATCH_SIZE):
        batch = paths[start:start + BATCH_SIZE]
        images = [Image.open(path).convert("RGB") for path in batch]
        inputs = processor(text=texts, images=images, return_tensors="pt", padding=True)
        with torch.no_grad():
            probs = model(**inputs).logits_per_image.softmax(dim=1)   # mỗi ảnh: xác suất của từng câu, tổng = 1

        for path, p in zip(batch, probs.tolist()):
            flower = path.parent.name
            score = sum(prob for (label, _), prob in zip(PROMPTS, p) if label == flower)
            best_text = texts[p.index(max(p))]
            results.append((score, best_text))
    return results


def read_scored_names():
    if not SCORES_FILE.exists():
        return set()
    with open(SCORES_FILE, encoding="utf-8-sig", newline="") as f:
        return {row["name"] for row in csv.DictReader(f)}


def save_scores(rows):
    is_new = not SCORES_FILE.exists()
    with open(SCORES_FILE, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        if is_new:
            writer.writerow(["name", "flower", "score", "flagged", "best_prompt"])
        writer.writerows(rows)


if __name__ == "__main__":
    scored = read_scored_names()
    paths = [path for flower in FLOWERS if (CLEAN_DIR / flower).exists()
             for path in list_images(CLEAN_DIR / flower) if path.name not in scored]
    if not paths:
        raise SystemExit("Không có ảnh mới trong data/clean/ cần chấm.")

    print(f"Đang nạp CLIP và chấm {len(paths)} ảnh…")
    model = CLIPModel.from_pretrained(MODEL_NAME)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    results = score_images(model, processor, paths)

    counts = Counter()
    rows = []
    for path, (score, best_text) in zip(paths, results):
        flower = path.parent.name
        flagged = score < THRESHOLD
        if flagged:
            dest = REMOVED_DIR / "clip" / flower / path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(path, dest)
        counts[(flower, "gắn cờ" if flagged else "giữ")] += 1
        rows.append([path.name, flower, f"{score:.3f}", int(flagged), best_text])
    save_scores(rows)

    print_table(f"Kết quả sàng lọc (ngưỡng {THRESHOLD}):", counts, ["giữ", "gắn cờ"])
    print("\nTiếp theo: xem data/removed/clip/<loài>/, ảnh dùng được thì kéo về data/clean/<loài>/.")
