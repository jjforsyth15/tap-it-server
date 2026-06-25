import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")
BUCKET = os.getenv("SUPABASE_AVATAR_BUCKET")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_avatar(file_bytes: bytes, path: str, content_type: str):
    supabase.storage.from_(BUCKET).upload(
        path=path, 
        file=file_bytes,
        file_options= {
            "content-type": content_type,
            "upsert": "true"
        },
    )
    
    public_url = supabase.storage.from_(BUCKET).get_public_url(path)
    
    return public_url