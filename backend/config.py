"""Environment configuration; stable paths regardless of launch directory."""
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True)
DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{ROOT / 'backend' / 'dispatch.db'}")
secret_file = DATA_DIR / '.jwt-secret'
if not os.getenv('JWT_SECRET') and not secret_file.exists():
    try:
        with secret_file.open('x') as handle:
            handle.write(secrets.token_urlsafe(48))
    except FileExistsError:
        pass
SECRET_KEY = os.getenv('JWT_SECRET') or secret_file.read_text().strip()
