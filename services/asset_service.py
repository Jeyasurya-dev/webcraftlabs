"""
Project image upload handling.

Admin-uploaded portfolio images are validated and stored in the
private Supabase Storage bucket.

Only the Supabase storage path is returned and stored in PostgreSQL.

Storage structure:

webcraft-assets/
└── projects/
    └── <safe-uuid>.<extension>

The bucket must remain PRIVATE.
"""

import os
import uuid
import mimetypes

from supabase import create_client, Client


# ============================================================
# Configuration
# ============================================================

ALLOWED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
}

MAX_IMAGE_MB = 5

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL"
)

SUPABASE_SECRET_KEY = os.environ.get(
    "SUPABASE_SECRET_KEY"
)

SUPABASE_BUCKET = "webcraft-assets"

PROJECT_FOLDER = "projects"


# ============================================================
# Errors
# ============================================================

class AssetError(Exception):
    pass


# ============================================================
# Supabase
# ============================================================

def get_supabase() -> Client:
    """
    Creates a server-side Supabase client.

    The secret key must never be exposed to the frontend.
    """

    if not SUPABASE_URL:
        raise AssetError(
            "SUPABASE_URL environment variable is not configured."
        )

    if not SUPABASE_SECRET_KEY:
        raise AssetError(
            "SUPABASE_SECRET_KEY environment variable is not configured."
        )

    return create_client(
        SUPABASE_URL,
        SUPABASE_SECRET_KEY,
    )


# ============================================================
# Validation
# ============================================================

def _extension(filename: str) -> str:
    """
    Returns the lowercase extension of the filename.
    """

    if not filename or "." not in filename:
        return ""

    return filename.rsplit(
        ".",
        1
    )[-1].lower()


def validate_image(file_storage) -> str:
    """
    Validates an uploaded project image.

    Checks:
    - File exists
    - MIME type
    - Maximum file size

    Returns:
        str: validated file extension
    """

    if not file_storage or not file_storage.filename:
        raise AssetError(
            "No image file provided."
        )

    filename = file_storage.filename.strip()

    # Browser-provided MIME type.
    uploaded_mime = (
        file_storage.mimetype
        or ""
    ).lower()

    # Filename-based MIME type as a secondary check.
    guessed_mime, _ = mimetypes.guess_type(
        filename
    )

    if (
        uploaded_mime not in ALLOWED_IMAGE_TYPES
        and guessed_mime not in ALLOWED_IMAGE_TYPES
    ):
        raise AssetError(
            "Image must be PNG, JPEG, WEBP, or GIF."
        )

    # Determine size without loading the entire
    # image into memory.
    try:
        file_storage.stream.seek(
            0,
            os.SEEK_END
        )

        size_bytes = file_storage.stream.tell()

        file_storage.stream.seek(
            0
        )

    except Exception as exc:
        raise AssetError(
            "Unable to determine image file size."
        ) from exc

    max_size_bytes = (
        MAX_IMAGE_MB
        * 1024
        * 1024
    )

    if size_bytes > max_size_bytes:
        raise AssetError(
            f"Image must be smaller than "
            f"{MAX_IMAGE_MB}MB."
        )

    return _extension(filename)


# ============================================================
# Upload
# ============================================================

def file_to_data_uri(file_storage) -> str:
    """
    Uploads a project image to Supabase Storage.

    The function name is intentionally kept as
    file_to_data_uri() so existing admin.py call sites
    do not need to change immediately.

    Despite the legacy function name, this function now
    returns a Supabase storage path instead of a Base64
    data URI.

    Example return value:

        projects/8c5d3e...a91.webp
    """

    ext = validate_image(
        file_storage
    )

    original_filename = (
        file_storage.filename
    )

    safe_filename = (
        f"{uuid.uuid4().hex}.{ext}"
    )

    storage_path = (
        f"{PROJECT_FOLDER}/{safe_filename}"
    )

    try:
        supabase = get_supabase()

        file_storage.stream.seek(0)

        file_bytes = file_storage.read()

        content_type = (
            file_storage.mimetype
            or mimetypes.guess_type(
                original_filename
            )[0]
            or "application/octet-stream"
        )

        supabase.storage \
            .from_(SUPABASE_BUCKET) \
            .upload(
                storage_path,
                file_bytes,
                {
                    "content-type": content_type,
                    "upsert": False,
                },
            )

    except AssetError:
        raise

    except Exception as exc:
        raise AssetError(
            "Unable to upload the project image. "
            "Please try again."
        ) from exc

    # IMPORTANT:
    # PostgreSQL stores this path, not the image itself.
    return storage_path


# ============================================================
# Delete
# ============================================================

def delete_project_image(storage_path: str) -> bool:
    """
    Deletes a project image from Supabase Storage.

    Only paths inside the projects/ folder are allowed.
    """

    if not storage_path:
        return False

    # Backward compatibility:
    # Old projects may still contain Base64 data.
    if storage_path.startswith("data:"):
        return False

    # Security check.
    if not storage_path.startswith(
        f"{PROJECT_FOLDER}/"
    ):
        raise AssetError(
            "Invalid project image storage path."
        )

    try:
        supabase = get_supabase()

        supabase.storage \
            .from_(SUPABASE_BUCKET) \
            .remove([
                storage_path
            ])

        return True

    except Exception as exc:
        raise AssetError(
            "Unable to delete the project image."
        ) from exc


# ============================================================
# Signed URL
# ============================================================

def create_project_image_signed_url(
    storage_path: str,
    expires_in: int = 3600,
):
    """
    Creates a temporary signed URL for a private
    project image.

    Default expiry:
        3600 seconds = 1 hour
    """

    if not storage_path:
        return None

    # Old Base64 images can still be returned directly.
    if storage_path.startswith("data:"):
        return storage_path

    if not storage_path.startswith(
        f"{PROJECT_FOLDER}/"
    ):
        raise AssetError(
            "Invalid project image storage path."
        )

    try:
        supabase = get_supabase()

        result = (
            supabase.storage
            .from_(SUPABASE_BUCKET)
            .create_signed_url(
                storage_path,
                expires_in,
            )
        )

        if isinstance(result, dict):
            return (
                result.get("signedURL")
                or result.get("signedUrl")
            )

        return None

    except Exception as exc:
        raise AssetError(
            "Unable to create project image URL."
        ) from exc