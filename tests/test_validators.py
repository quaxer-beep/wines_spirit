import pytest

from src.utils.exceptions import ValidationError
from src.utils.validators import (
    sanitize_phone,
    validate_phone,
    validate_positive_number,
    validate_password,
    validate_required,
)


class TestValidateRequired:
    def test_passes_with_value(self):
        assert validate_required("hello", "Field") == "hello"
        assert validate_required(0, "Field") == 0
        assert validate_required(False, "Field") is False

    def test_fails_with_none(self):
        with pytest.raises(ValidationError):
            validate_required(None, "Field")

    def test_fails_with_empty_string(self):
        with pytest.raises(ValidationError):
            validate_required("", "Field")

    def test_fails_with_whitespace(self):
        with pytest.raises(ValidationError):
            validate_required("   ", "Field")

    def test_error_message(self):
        with pytest.raises(ValidationError) as exc:
            validate_required(None, "Username")
        assert "Username" in str(exc.value)
        assert "required" in str(exc.value)


class TestValidatePhone:
    def test_passes_valid_07XX(self):
        assert validate_phone("0712345678") == "0712345678"

    def test_passes_valid_01XX(self):
        assert validate_phone("0112345678") == "0112345678"

    def test_passes_valid_254_prefix(self):
        assert validate_phone("+254712345678") == "+254712345678"

    def test_fails_too_short(self):
        with pytest.raises(ValidationError):
            validate_phone("071234")

    def test_fails_invalid_prefix(self):
        with pytest.raises(ValidationError):
            validate_phone("0812345678")

    def test_fails_with_letters(self):
        with pytest.raises(ValidationError):
            validate_phone("07abcdefgh")

    def test_fails_empty(self):
        with pytest.raises(ValidationError):
            validate_phone("")


class TestSanitizePhone:
    def test_converts_07XX(self):
        result = sanitize_phone("0712345678")
        assert result == "254712345678"

    def test_converts_011XX(self):
        result = sanitize_phone("0112345678")
        assert result == "254112345678"

    def test_converts_plus_254(self):
        result = sanitize_phone("+254712345678")
        assert result == "254712345678"

    def test_passes_already_sanitized(self):
        result = sanitize_phone("254712345678")
        assert result == "254712345678"

    def test_fails_invalid(self):
        with pytest.raises(ValidationError):
            sanitize_phone("12345")


class TestValidatePositiveNumber:
    def test_passes_for_positive(self):
        assert validate_positive_number(5, "Qty") == 5.0

    def test_fails_for_zero(self):
        with pytest.raises(ValidationError):
            validate_positive_number(0, "Qty")

    def test_fails_for_negative(self):
        with pytest.raises(ValidationError):
            validate_positive_number(-1, "Qty")

    def test_fails_for_none(self):
        with pytest.raises(ValidationError):
            validate_positive_number(None, "Qty")


class TestValidatePassword:
    def test_passes_valid(self):
        assert validate_password("Pass123") == "Pass123"

    def test_fails_short(self):
        with pytest.raises(ValidationError):
            validate_password("Ab1")

    def test_fails_no_uppercase(self):
        with pytest.raises(ValidationError):
            validate_password("pass123")

    def test_fails_no_digit(self):
        with pytest.raises(ValidationError):
            validate_password("Password")

    def test_error_messages(self):
        with pytest.raises(ValidationError) as exc:
            validate_password("short")
        assert "6 characters" in str(exc.value)

        with pytest.raises(ValidationError) as exc:
            validate_password("nouppercase1")
        assert "uppercase" in str(exc.value)

        with pytest.raises(ValidationError) as exc:
            validate_password("NODIGITS")
        assert "digit" in str(exc.value)
