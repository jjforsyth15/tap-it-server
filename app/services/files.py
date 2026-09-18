import re


# strips a user-controlled name down to characters safe for a
# Content-Disposition filename, since raw user input shouldn't land directly
# in a response header
def sanitize_filename(name: str, fallback: str = "file") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 _-]", "", name).strip()
    return cleaned or fallback
