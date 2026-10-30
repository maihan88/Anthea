"""Lưu và xóa ảnh người dùng tải lên.

Có CLOUDINARY_URL trong .env  -> ảnh lưu trên Cloudinary (dịch vụ lưu trữ đám mây), CSDL chỉ giữ đường link.
Chưa có CLOUDINARY_URL        -> tạm lưu vào app/static/uploads/ để vẫn chạy thử được web.

app.py chỉ dùng 2 hàm:
    save_image(image_bytes, extension) -> (image_url, image_id)
    delete_image(image_id)
Người phụ trách: Hân
"""
import uuid
from urllib.parse import urlparse

import cloudinary
import cloudinary.uploader

import config

USE_CLOUDINARY = config.CLOUDINARY_URL != ""
CLOUDINARY_FOLDER = "anthea/uploads"                   # thư mục chứa ảnh trên Cloudinary

if USE_CLOUDINARY:
    # CLOUDINARY_URL có dạng cloudinary://<api_key>:<api_secret>@<cloud_name>, tách ra 3 phần
    url = urlparse(config.CLOUDINARY_URL)
    cloudinary.config(cloud_name=url.hostname, api_key=url.username, api_secret=url.password, secure=True)


def save_image(image_bytes, extension):
    """Lưu ảnh. Trả về (link để hiện ảnh, mã ảnh để sau này xóa)."""
    if USE_CLOUDINARY:
        result = cloudinary.uploader.upload(image_bytes, folder=CLOUDINARY_FOLDER)
        # secure_url: link https tới ảnh;  public_id: mã ảnh, ví dụ "anthea/uploads/abc123"
        return result["secure_url"], result["public_id"]

    # Không có Cloudinary: lưu vào máy. Tên file ngẫu nhiên (uuid4) để không bao giờ trùng.
    filename = uuid.uuid4().hex + "." + extension
    (config.UPLOAD_DIR / filename).write_bytes(image_bytes)
    return "/static/uploads/" + filename, filename


def delete_image(image_id):
    """Xóa ảnh. Lỗi thì chỉ in ra rồi bỏ qua: dòng trong CSDL đã xóa rồi, không cần báo người dùng."""
    try:
        if USE_CLOUDINARY:
            cloudinary.uploader.destroy(image_id)
        else:
            (config.UPLOAD_DIR / image_id).unlink(missing_ok=True)
    except Exception as error:
        print("Không xóa được ảnh", image_id, ":", error)
