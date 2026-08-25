"""
Converts admin-uploaded portfolio images into Base64 data URIs for storage
directly in the projects table, keeping with the project's no-external /
no-loose-static-file-dependency approach for imagery.
"""
import base64

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_IMAGE_MB = 5


class AssetError(Exception):
    pass


def file_to_data_uri(file_storage) -> str:
    if not file_storage or file_storage.filename == "":
        raise AssetError("No image file provided.")
    if file_storage.mimetype not in ALLOWED_IMAGE_TYPES:
        raise AssetError("Image must be PNG, JPEG, WEBP, or GIF.")

    file_storage.stream.seek(0, 2)
    size_mb = file_storage.stream.tell() / (1024 * 1024)
    file_storage.stream.seek(0)
    if size_mb > MAX_IMAGE_MB:
        raise AssetError(f"Image must be smaller than {MAX_IMAGE_MB}MB.")

    raw = file_storage.read()
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{file_storage.mimetype};base64,{encoded}"
