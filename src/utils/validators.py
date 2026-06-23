import re

from src.utils.exceptions import ValidationError


def validate_required(value, field_name):
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError(f"{field_name} is required and cannot be empty.")
    return value


def validate_positive_number(value, field_name):
    validate_required(value, field_name)
    try:
        val = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid number.")
    if val <= 0:
        raise ValidationError(f"{field_name} must be a positive number.")
    return val


def validate_non_negative(value, field_name):
    validate_required(value, field_name)
    try:
        val = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid number.")
    if val < 0:
        raise ValidationError(f"{field_name} must not be negative.")
    return val


def validate_phone(phone):
    phone = str(phone).strip()
    pattern = r"^(?:\+254|0)?(7[0-9]{8}|11[0-9]{7})$"
    if not re.match(pattern, phone):
        raise ValidationError("Invalid phone number. Use format: 0712345678, 0112345678, or +254712345678.")
    return phone


def validate_email(email):
    email = str(email).strip()
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format.")
    return email


def validate_amount(amount):
    try:
        val = validate_positive_number(amount, "Amount")
    except ValidationError:
        raise ValidationError("Amount must be a positive number.")
    parts = str(val).split(".")
    if len(parts) == 2 and len(parts[1]) > 2:
        raise ValidationError("Amount must have at most 2 decimal places.")
    return round(val, 2)


def validate_barcode(barcode):
    barcode = str(barcode).strip()
    if not barcode or not barcode.isalnum():
        raise ValidationError("Barcode must be a non-empty alphanumeric value.")
    return barcode


def validate_password(password):
    password = str(password)
    if len(password) < 6:
        raise ValidationError("Password must be at least 6 characters long.")
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least 1 digit.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least 1 uppercase letter.")
    return password


def sanitize_phone(phone):
    phone = str(phone).strip()
    if phone.startswith("+"):
        phone = phone[1:]
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    if not phone.startswith("254"):
        raise ValidationError("Unable to sanitize phone number. Provide a valid Kenyan number.")
    if len(phone) != 12:
        raise ValidationError("Sanitized phone number must be 12 digits (2547XXXXXXXX or 25411XXXXXXX).")
    return phone
