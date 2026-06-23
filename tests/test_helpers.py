from unittest.mock import patch

from src.utils.helpers import (
    calculate_tax,
    format_currency,
    generate_receipt_number,
    hash_password,
    verify_password,
)


class TestFormatCurrency:
    def test_format_currency_positive(self):
        result = format_currency(1500)
        assert result == "KES 1,500.00"

    def test_format_currency_with_decimals(self):
        result = format_currency(1500.5)
        assert result == "KES 1,500.50"

    def test_format_currency_zero(self):
        result = format_currency(0)
        assert result == "KES 0.00"

    def test_format_currency_large(self):
        result = format_currency(1000000)
        assert result == "KES 1,000,000.00"


class TestCalculateTax:
    def test_default_rate(self):
        result = calculate_tax(1000)
        assert result == 160.0

    def test_custom_rate(self):
        result = calculate_tax(1000, 0.08)
        assert result == 80.0

    def test_zero_subtotal(self):
        result = calculate_tax(0)
        assert result == 0.0

    def test_rounding(self):
        result = calculate_tax(333.33)
        assert result == 53.33


class TestHashAndVerifyPassword:
    def test_round_trip(self):
        password = "SecurePass123!"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("RealPass1")
        assert verify_password("WrongPass1", hashed) is False

    def test_hashed_string_format(self):
        hashed = hash_password("TestPass1")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


class TestGenerateReceiptNumber:
    def test_correct_format(self):
        from datetime import date

        rcp = generate_receipt_number("MB001", date=date(2026, 6, 23))
        assert rcp.startswith("RCP-MB001-20260623-")
        assert rcp.count("-") == 3

    def test_incrementing_sequence(self):
        from datetime import date

        with patch("src.utils.helpers._sequence_counters", {}):
            rcp1 = generate_receipt_number("MB001", date=date(2026, 6, 23))
            rcp2 = generate_receipt_number("MB001", date=date(2026, 6, 23))
            assert rcp1 == "RCP-MB001-20260623-0001"
            assert rcp2 == "RCP-MB001-20260623-0002"

    def test_different_branch_independent_sequences(self):
        from datetime import date

        with patch("src.utils.helpers._sequence_counters", {}):
            rcp1 = generate_receipt_number("MB001", date=date(2026, 6, 23))
            rcp2 = generate_receipt_number("MB002", date=date(2026, 6, 23))
            assert rcp1 == "RCP-MB001-20260623-0001"
            assert rcp2 == "RCP-MB002-20260623-0001"
