"""
Resume upload handling: extension + MIME + size validation, safe
server-generated filenames, storage outside any publicly-served static
directory (only reachable via authenticated admin download route).
"""
import os
import uuid
import mimetypes

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_UPLOAD_MB = int(os.environ.get("UPLOAD_MAX_MB", 5))

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")


class UploadError(Exception):
    pass


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def validate_resume(file_storage):
    if not file_storage or file_storage.filename == "":
        raise UploadError("Please attach a resume file.")

    ext = _extension(file_storage.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadError("Resume must be a PDF, DOC, or DOCX file.")

    mime, _ = mimetypes.guess_type(file_storage.filename)
    if file_storage.mimetype not in ALLOWED_MIME_TYPES and mime not in ALLOWED_MIME_TYPES:
        raise UploadError("Unrecognized file type. Please upload a PDF, DOC, or DOCX file.")

    file_storage.stream.seek(0, os.SEEK_END)
    size_mb = file_storage.stream.tell() / (1024 * 1024)
    file_storage.stream.seek(0)
    if size_mb > MAX_UPLOAD_MB:
        raise UploadError(f"Resume must be smaller than {MAX_UPLOAD_MB}MB.")

    return ext


def save_resume(file_storage) -> tuple[str, str]:
    """Validates and saves the resume. Returns (safe_filename, original_filename)."""
    ext = validate_resume(file_storage)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    dest = os.path.join(UPLOAD_DIR, safe_name)
    file_storage.save(dest)
    return safe_name, file_storage.filename


def resume_path(safe_filename: str) -> str:
    path = os.path.join(UPLOAD_DIR, safe_filename)
    if not os.path.abspath(path).startswith(os.path.abspath(UPLOAD_DIR)):
        raise UploadError("Invalid file path.")
    return path
