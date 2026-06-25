import re
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

import bcrypt

from src.config.settings import settings


_sequence_counters = {}


def _get_sequence(key, today):
    cache_key = f"{key}_{today}"
    if cache_key not in _sequence_counters:
        _sequence_counters[cache_key] = 0
    _sequence_counters[cache_key] += 1
    return _sequence_counters[cache_key]


def generate_receipt_number(branch_code, ref_date=None, session=None):
    today = ref_date or date.today()
    date_str = today.strftime("%Y%m%d")
    prefix = f"RCP-{branch_code}-{date_str}-"

    seq = 0
    if session is not None:
        from sqlalchemy import Integer, cast, func
        from src.database.models import Sale
        max_seq = (
            session.query(
                func.max(cast(func.substr(Sale.receipt_number, -4), Integer))
            )
            .filter(Sale.receipt_number.like(f"{prefix}%"))
            .scalar()
        )
        if max_seq is not None:
            seq = max_seq
    else:
        seq = _get_sequence(f"rcp_{branch_code}", today) - 1

    seq += 1
    return f"{prefix}{seq:04d}"


def generate_invoice_number(ref_date=None, session=None):
    today = ref_date or date.today()
    date_str = today.strftime("%Y%m%d")
    prefix = f"INV-{date_str}-"

    seq = 0
    from sqlalchemy import Integer, cast, func
    from src.database.models import EtimsInvoice

    def _do_query(s):
        return (
            s.query(func.max(cast(func.substr(EtimsInvoice.invoice_number, -4), Integer)))
            .filter(EtimsInvoice.invoice_number.like(f"{prefix}%"))
            .scalar()
        )

    if session is not None:
        max_seq = _do_query(session)
        if max_seq is not None:
            seq = max_seq
    else:
        from src.database.connection import db_manager
        with db_manager.get_session() as s:
            max_seq = _do_query(s)
            if max_seq is not None:
                seq = max_seq

    seq += 1
    return f"{prefix}{seq:04d}"


def format_currency(amount):
    decimal_amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    formatted = f"{decimal_amount:,.2f}"
    return f"KES {formatted}"


def parse_currency(currency_str):
    cleaned = re.sub(r"[^0-9.\-]", "", str(currency_str))
    return Decimal(cleaned).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_today_date():
    return date.today().isoformat()


def get_current_timestamp():
    return datetime.now().isoformat()


def calculate_tax(subtotal, tax_rate=0.16):
    return round(float(subtotal) * tax_rate, 2)


def calculate_discount(amount, discount_pct):
    return round(float(amount) * float(discount_pct) / 100, 2)


def truncate_text(text, max_length):
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def hash_password(password):
    rounds = getattr(settings, "BCRYPT_ROUNDS", 12)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
