import os
import sys
from pathlib import Path


class Settings:
    APP_NAME = "Wines & Spirits POS"
    APP_VERSION = "1.0.0"
    BASE_DIR = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent.parent

    if getattr(sys, "frozen", False):
        DB_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME / "data"
    else:
        DB_DIR = BASE_DIR / "data"
    DB_FILENAME = "pos.db"
    DB_PRAGMA_JOURNAL_MODE = "WAL"
    DB_PRAGMA_FOREIGN_KEYS = "ON"
    BCRYPT_ROUNDS = 12
    SESSION_TIMEOUT_MINUTES = 480
    MPESA_ENVIRONMENT = "sandbox"
    MPESA_CONSUMER_KEY = ""
    MPESA_CONSUMER_SECRET = ""
    MPESA_PASSKEY = ""
    MPESA_SHORTCODE = ""
    MPESA_CALLBACK_URL = ""
    ETIMS_ENDPOINT = ""
    ETIMS_USERNAME = ""
    ETIMS_PASSWORD = ""
    SYNC_INTERVAL_SECONDS = 300
    SYNC_API_URL = ""
    SYNC_API_KEY = ""
    SYNC_EXPORT_DIR = str(BASE_DIR / "data" / "pos_databases")
    PRINTER_WIDTH_58MM = 32
    PRINTER_WIDTH_80MM = 48
    PRINTER_DEFAULT = "58mm"
    RECEIPT_FOOTER = "Thank you for your purchase!\nVisit us again."
    COMPANY_NAME = "Wines & Spirits"
    COMPANY_TAGLINE = "Premium Wines & Spirits"

    @classmethod
    def get_db_path(cls, branch_code=None):
        cls.DB_DIR.mkdir(parents=True, exist_ok=True)
        if branch_code:
            return str(cls.DB_DIR / f"pos_{branch_code}.db")
        return str(cls.DB_DIR / cls.DB_FILENAME)


settings = Settings()
