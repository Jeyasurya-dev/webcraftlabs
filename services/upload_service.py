"""
Resume upload handling.

Resumes are validated and uploaded to the private Supabase Storage bucket.

PostgreSQL stores only the Supabase Storage path.

Storage structure:

webcraft-assets/
└── resumes/
    └── <safe-uuid>.<extension>

The bucket must remain PRIVATE.

Resume downloads happen through an authenticated admin route
using a short-lived signed URL.
"""

import os
import uuid
import mimetypes

from supabase import create_client, Client


# ============================================================
# Configuration
# ============================================================

ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

MAX_UPLOAD_MB = int(
    os.environ.get("UPLOAD_MAX_MB", 5)
)

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL"
)

SUPABASE_SECRET_KEY = os.environ.get(
    "SUPABASE_SECRET_KEY"
)

SUPABASE_BUCKET = "webcraft-assets"

RESUME_FOLDER = "resumes"


# ============================================================
# Errors
# ============================================================

class UploadError(Exception):
    """Raised when resume validation or storage fails."""
    pass


# ============================================================
# Supabase
# ============================================================

def get_supabase() -> Client:
    """
    Creates a server-side Supabase client.

    SUPABASE_SECRET_KEY must NEVER be exposed
    to frontend/browser JavaScript.
    """

    if not SUPABASE_URL:
        raise UploadError(
            "SUPABASE_URL environment variable is not configured."
        )

    if not SUPABASE_SECRET_KEY:
        raise UploadError(
            "SUPABASE_SECRET_KEY environment variable is not configured."
        )

    return create_client(
        SUPABASE_URL,
        SUPABASE_SECRET_KEY,
    )


# ============================================================
# Validation helpers
# ============================================================

def _extension(filename: str) -> str:
    """
    Returns the lowercase file extension.
    """

    if not filename or "." not in filename:
        return ""

    return filename.rsplit(
        ".",
        1,
    )[-1].lower()


def validate_resume(file_storage):
    """
    Validates an uploaded resume.

    Checks:
    - File exists
    - File extension
    - MIME type
    - Maximum file size

    Returns:
        str: validated extension
    """

    if not file_storage or not file_storage.filename:
        raise UploadError(
            "Please attach a resume file."
        )

    original_filename = (
        file_storage.filename.strip()
    )

    ext = _extension(
        original_filename
    )

    if ext not in ALLOWED_EXTENSIONS:
        raise UploadError(
            "Resume must be a PDF, DOC, or DOCX file."
        )

    # Browser-provided MIME type.
    uploaded_mime = (
        file_storage.mimetype
        or ""
    ).lower()

    # Filename-based MIME guess.
    guessed_mime, _ = mimetypes.guess_type(
        original_filename
    )

    if (
        uploaded_mime not in ALLOWED_MIME_TYPES
        and guessed_mime not in ALLOWED_MIME_TYPES
    ):
        raise UploadError(
            "Unrecognized file type. "
            "Please upload a PDF, DOC, or DOCX file."
        )

    # Check file size without loading the
    # entire file into memory.
    try:

        file_storage.stream.seek(
            0,
            os.SEEK_END,
        )

        size_bytes = (
            file_storage.stream.tell()
        )

        file_storage.stream.seek(
            0
        )

    except Exception as exc:

        raise UploadError(
            "Unable to determine resume file size."
        ) from exc

    max_size_bytes = (
        MAX_UPLOAD_MB
        * 1024
        * 1024
    )

    if size_bytes > max_size_bytes:
        raise UploadError(
            f"Resume must be smaller than "
            f"{MAX_UPLOAD_MB}MB."
        )

    return ext


# ============================================================
# Upload
# ============================================================

def save_resume(file_storage) -> tuple[str, str]:
    """
    Validates and uploads a resume to Supabase Storage.

    Returns:

        (
            storage_path,
            original_filename
        )

    Example:

        (
            "resumes/8c5d1234abcd.pdf",
            "Surya_Resume.pdf"
        )

    Only storage_path is stored in PostgreSQL.
    """

    ext = validate_resume(
        file_storage
    )

    original_filename = (
        file_storage.filename.strip()
    )

    # Server-generated filename.
    # User's original filename is never used
    # as the actual storage filename.
    safe_filename = (
        f"{uuid.uuid4().hex}.{ext}"
    )

    storage_path = (
        f"{RESUME_FOLDER}/{safe_filename}"
    )

    try:

        supabase = get_supabase()

        # Always start from the beginning.
        file_storage.stream.seek(
            0
        )

        file_bytes = (
            file_storage.read()
        )

        content_type = (
            file_storage.mimetype
            or mimetypes.guess_type(
                original_filename
            )[0]
            or "application/octet-stream"
        )

        (
            supabase.storage
            .from_(SUPABASE_BUCKET)
            .upload(
                storage_path,
                file_bytes,
                {
                    "content-type": content_type,
                    "upsert": False,
                },
            )
        )

    except UploadError:
        raise

    except Exception as exc:

        raise UploadError(
            "Unable to upload the resume. "
            "Please try again."
        ) from exc

    return (
        storage_path,
        original_filename,
    )


# ============================================================
# Signed URL
# ============================================================

def create_resume_signed_url(
    storage_path: str,
    expires_in: int = 300,
):
    """
    Creates a short-lived signed URL for a resume.

    The Supabase bucket remains PRIVATE.

    Args:
        storage_path:
            Path stored in PostgreSQL.

        expires_in:
            URL lifetime in seconds.
            Default = 300 seconds (5 minutes).

    Returns:
        str | None:
            Signed URL if successful.
    """

    if not storage_path:
        return None

    # Safety check.
    # Only allow files inside the resumes folder.
    if not storage_path.startswith(
        f"{RESUME_FOLDER}/"
    ):
        raise UploadError(
            "Invalid resume storage path."
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

        raise UploadError(
            "Unable to create resume access URL."
        ) from exc


# ============================================================
# Delete
# ============================================================

def delete_resume(
    storage_path: str,
) -> bool:
    """
    Deletes a resume from Supabase Storage.

    Used when an application is rejected.

    Applicant details remain in PostgreSQL.
    Only the resume file is deleted.

    Returns:
        True  -> deletion completed
        False -> no storage path supplied
    """

    if not storage_path:
        return False

    # Safety check.
    # Never allow deleting anything outside
    # the resumes directory.
    if not storage_path.startswith(
        f"{RESUME_FOLDER}/"
    ):
        raise UploadError(
            "Invalid resume storage path."
        )

    try:

        supabase = get_supabase()

        (
            supabase.storage
            .from_(SUPABASE_BUCKET)
            .remove([
                storage_path
            ])
        )

        return True

    except Exception as exc:

        raise UploadError(
            "Unable to delete the resume."
        ) from exc