import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")
AVATAR_BUCKET = os.getenv("SUPABASE_AVATAR_BUCKET")
RESUME_BUCKET = os.getenv("SUPABASE_RESUME_BUCKET")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_file(bucket: str, file_bytes: bytes, path: str, content_type: str) -> str:
    supabase.storage.from_(bucket).upload(
        path=path,
        file=file_bytes,
        file_options={"content-type": content_type, "upsert": "true"},
    )

    return supabase.storage.from_(bucket).get_public_url(path)


def download_file(bucket: str, path: str) -> bytes:
    return supabase.storage.from_(bucket).download(path)


def delete_file(bucket: str, path: str) -> None:
    supabase.storage.from_(bucket).remove([path])


def upload_avatar(file_bytes: bytes, path: str, content_type: str) -> str:
    return upload_file(AVATAR_BUCKET, file_bytes, path, content_type)


def upload_resume(file_bytes: bytes, path: str, content_type: str) -> str:
    return upload_file(RESUME_BUCKET, file_bytes, path, content_type)
