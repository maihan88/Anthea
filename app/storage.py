from urllib.parse import urlparse

import cloudinary
import cloudinary.uploader

import config

CLOUDINARY_FOLDER = "anthea/uploads"

# CLOUDINARY_URL có dạng cloudinary://<api_key>:<api_secret>@<cloud_name>
url = urlparse(config.CLOUDINARY_URL)
cloudinary.config(cloud_name=url.hostname, api_key=url.username, api_secret=url.password, secure=True)


def save_image(image_bytes):
    result = cloudinary.uploader.upload(image_bytes, folder=CLOUDINARY_FOLDER)
    return result["secure_url"], result["public_id"]


def delete_image(image_id):
    try:
        cloudinary.uploader.destroy(image_id)
    except Exception as error:
        print("Không xóa được ảnh", image_id, ":", error)
