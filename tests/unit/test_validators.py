"""
Unit tests for validators
"""

from decimal import Decimal

import pytest

from core.exceptions import (
    InvalidAmountError,
    InvalidCurrencyError,
    ValidationError,
)
from core.utils.validators import (
    validate_amount,
    validate_currency,
    validate_email,
    validate_phone,
    validate_routing_number,
    validate_swift_code,
)


class TestAmountValidator:
    """Tests for amount validation"""

    def test_valid_amount(self):
        """Test valid amount"""
        validate_amount(Decimal("100.00"))  # Should not raise

    def test_negative_amount(self):
        """Test negative amount raises error"""
        with pytest.raises(InvalidAmountError):
            validate_amount(Decimal("-10.00"))

    def test_zero_amount(self):
        """Test zero amount raises error"""
        with pytest.raises(InvalidAmountError):
            validate_amount(Decimal("0.00"))

    def test_too_many_decimals(self):
        """Test amount with too many decimals"""
        with pytest.raises(InvalidAmountError):
            validate_amount(Decimal("10.123"))


class TestCurrencyValidator:
    """Tests for currency validation"""

    def test_valid_currency(self):
        """Test valid currency codes"""
        validate_currency("USD")
        validate_currency("EUR")
        validate_currency("GBP")

    def test_invalid_currency_length(self):
        """Test invalid currency length"""
        with pytest.raises(InvalidCurrencyError):
            validate_currency("US")

    def test_unsupported_currency(self):
        """Test unsupported currency"""
        with pytest.raises(InvalidCurrencyError):
            validate_currency("XYZ")


class TestEmailValidator:
    """Tests for email validation"""

    def test_valid_email(self):
        """Test valid emails"""
        validate_email("test@example.com")
        validate_email("user.name+tag@example.co.uk")

    def test_invalid_email(self):
        """Test invalid emails"""
        with pytest.raises(ValidationError):
            validate_email("invalid")

        with pytest.raises(ValidationError):
            validate_email("@example.com")


class TestPhoneValidator:
    """Tests for phone validation"""

    def test_valid_phone(self):
        """Test valid phone numbers"""
        validate_phone("+1234567890")
        validate_phone("123-456-7890")
        validate_phone("(123) 456-7890")

    def test_invalid_phone(self):
        """Test invalid phone numbers"""
        with pytest.raises(ValidationError):
            validate_phone("12345")  # Too short

        with pytest.raises(ValidationError):
            validate_phone("abc1234567")  # Contains letters


class TestRoutingNumberValidator:
    """Tests for routing number validation"""

    def test_valid_routing_number(self):
        """Test valid routing number"""
        validate_routing_number("121000248")  # Valid checksum

    def test_invalid_routing_number_length(self):
        """Test invalid routing number length"""
        with pytest.raises(ValidationError):
            validate_routing_number("12345678")


class TestSwiftCodeValidator:
    """Tests for SWIFT code validation"""

    def test_valid_swift_code(self):
        """Test valid SWIFT codes"""
        validate_swift_code("DEUTDEFF")  # 8 characters
        validate_swift_code("DEUTDEFF500")  # 11 characters

    def test_invalid_swift_code_length(self):
        """Test invalid SWIFT code length"""
        with pytest.raises(ValidationError):
            validate_swift_code("DEUT")

    def test_invalid_swift_code_format(self):
        """Test invalid SWIFT code format"""
        with pytest.raises(ValidationError):
            validate_swift_code("1234DEFF")  # Should start with letters
