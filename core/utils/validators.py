"""
Business rule validators
"""

import re
from decimal import Decimal

from ..exceptions import (
    InvalidAmountError,
    InvalidCurrencyError,
    ValidationError,
)

# Currency codes (ISO 4217)
VALID_CURRENCIES = {
    "USD",
    "EUR",
    "GBP",
    "JPY",
    "CAD",
    "AUD",
    "CHF",
    "CNY",
    "INR",
    "BRL",
    # African currencies for mobile money
    "KES",
    "TZS",
    "UGX",
    "GHS",
    "ZAR",
    "XOF",
    "XAF",
    "ZMW",
    "ZWL",
    "MZN",
}

# Mobile money provider to country mapping
MOBILE_MONEY_PROVIDER_COUNTRIES = {
    "mpesa": ["KE", "TZ", "MZ", "ZA"],
    "mtn": ["UG", "GH", "CI", "CM", "ZM", "BJ", "CG", "RW"],
    "airtel": ["KE", "TZ", "UG", "ZM", "MW", "NG", "CD", "RW", "GA"],
    "orange": ["SN", "ML", "BF", "CI", "CM", "NE", "MG", "GN"],
    "vodacom": ["ZA", "TZ", "MZ", "LS"],
    "tigo": ["TZ", "RW", "GH"],
    "ecocash": ["ZW", "ZM"],
    "wave": ["SN", "CI", "BF", "ML"],
    "chipper": ["KE", "UG", "GH", "NG", "ZA", "TZ", "RW"],
    "flutterwave": ["KE", "UG", "GH", "NG", "ZA", "TZ", "RW"],  # Pan-African aggregator
}


def validate_amount(amount: Decimal, min_amount: Decimal | None = None) -> None:
    """
    Validate transaction amount

    Args:
        amount: Amount to validate
        min_amount: Minimum allowed amount

    Raises:
        InvalidAmountError: If amount is invalid
    """
    if amount <= 0:
        raise InvalidAmountError("Amount must be greater than zero")

    if min_amount and amount < min_amount:
        raise InvalidAmountError(f"Amount must be at least {min_amount}")

    # Check for reasonable precision (2 decimal places for most currencies)
    if amount.as_tuple().exponent < -2:
        raise InvalidAmountError("Amount has too many decimal places (max 2)")


def validate_currency(currency: str) -> None:
    """
    Validate currency code

    Args:
        currency: Currency code to validate

    Raises:
        InvalidCurrencyError: If currency is invalid
    """
    if not currency or len(currency) != 3:
        raise InvalidCurrencyError(
            f"Invalid currency code: {currency}. Must be 3-letter ISO 4217 code"
        )

    if currency.upper() not in VALID_CURRENCIES:
        raise InvalidCurrencyError(f"Unsupported currency: {currency}")


def validate_email(email: str) -> None:
    """
    Validate email address

    Args:
        email: Email to validate

    Raises:
        ValidationError: If email is invalid
    """
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValidationError(f"Invalid email address: {email}")


def validate_phone(phone: str) -> None:
    """
    Validate phone number

    Args:
        phone: Phone number to validate

    Raises:
        ValidationError: If phone is invalid
    """
    # Remove common formatting characters
    cleaned = re.sub(r"[\s\-\(\)\+]", "", phone)

    # Check if it contains only digits
    if not cleaned.isdigit():
        raise ValidationError(f"Invalid phone number: {phone}")

    # Check length (typically 10-15 digits)
    if len(cleaned) < 10 or len(cleaned) > 15:
        raise ValidationError(f"Phone number must be between 10 and 15 digits: {phone}")


def validate_routing_number(routing_number: str) -> None:
    """
    Validate US routing number (ABA routing number)

    Args:
        routing_number: Routing number to validate

    Raises:
        ValidationError: If routing number is invalid
    """
    # Remove any non-digit characters
    cleaned = re.sub(r"\D", "", routing_number)

    if len(cleaned) != 9:
        raise ValidationError("Routing number must be 9 digits")

    # Validate using checksum algorithm
    digits = [int(d) for d in cleaned]
    checksum = (
        3 * (digits[0] + digits[3] + digits[6])
        + 7 * (digits[1] + digits[4] + digits[7])
        + (digits[2] + digits[5] + digits[8])
    ) % 10

    if checksum != 0:
        raise ValidationError("Invalid routing number checksum")


def validate_account_number(account_number: str) -> None:
    """
    Validate account number format

    Args:
        account_number: Account number to validate

    Raises:
        ValidationError: If account number is invalid
    """
    # Remove any non-alphanumeric characters
    cleaned = re.sub(r"\W", "", account_number)

    # Check length (typically 8-17 characters)
    if len(cleaned) < 8 or len(cleaned) > 17:
        raise ValidationError("Account number must be between 8 and 17 characters")


def validate_swift_code(swift_code: str) -> None:
    """
    Validate SWIFT/BIC code

    Args:
        swift_code: SWIFT code to validate

    Raises:
        ValidationError: If SWIFT code is invalid
    """
    # SWIFT code is 8 or 11 characters
    # Format: AAAABBCCDDD
    # AAAA: Bank code
    # BB: Country code
    # CC: Location code
    # DDD: Branch code (optional)

    if len(swift_code) not in [8, 11]:
        raise ValidationError("SWIFT code must be 8 or 11 characters")

    if not swift_code.isalnum():
        raise ValidationError("SWIFT code must contain only letters and numbers")

    # First 4 characters should be letters (bank code)
    if not swift_code[:4].isalpha():
        raise ValidationError("Invalid SWIFT code format")

    # Next 2 characters should be letters (country code)
    if not swift_code[4:6].isalpha():
        raise ValidationError("Invalid SWIFT code country")


def validate_card_number(card_number: str) -> None:
    """
    Validate credit card number using Luhn algorithm

    Args:
        card_number: Card number to validate

    Raises:
        ValidationError: If card number is invalid
    """
    # Remove any non-digit characters
    cleaned = re.sub(r"\D", "", card_number)

    if len(cleaned) < 13 or len(cleaned) > 19:
        raise ValidationError("Card number must be between 13 and 19 digits")

    # Luhn algorithm
    digits = [int(d) for d in cleaned]
    checksum = 0

    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit

    if checksum % 10 != 0:
        raise ValidationError("Invalid card number")


def validate_e164_phone(phone: str) -> None:
    """
    Validate phone number in E.164 format

    E.164 format: +[country code][subscriber number]
    Example: +254712345678 (Kenya)

    Args:
        phone: Phone number to validate

    Raises:
        ValidationError: If phone number is invalid
    """
    # E.164 pattern: + followed by 1-3 digit country code and up to 14 more digits
    e164_pattern = r"^\+[1-9]\d{1,14}$"

    if not re.match(e164_pattern, phone):
        raise ValidationError(
            f"Invalid phone number format. Must be in E.164 format (e.g., +254712345678): {phone}"
        )


def validate_mobile_money_provider(provider: str, country_code: str) -> None:
    """
    Validate that a mobile money provider operates in the specified country

    Args:
        provider: Mobile money provider code (e.g., 'mpesa', 'mtn')
        country_code: ISO 3166-1 alpha-2 country code (e.g., 'KE', 'UG')

    Raises:
        ValidationError: If provider doesn't operate in the country
    """
    provider_lower = provider.lower()
    country_upper = country_code.upper()

    if provider_lower not in MOBILE_MONEY_PROVIDER_COUNTRIES:
        raise ValidationError(f"Unknown mobile money provider: {provider}")

    supported_countries = MOBILE_MONEY_PROVIDER_COUNTRIES[provider_lower]
    if country_upper not in supported_countries:
        raise ValidationError(
            f"Provider '{provider}' does not operate in country '{country_code}'. "
            f"Supported countries: {', '.join(supported_countries)}"
        )


def validate_country_code(country_code: str) -> None:
    """
    Validate ISO 3166-1 alpha-2 country code

    Args:
        country_code: Country code to validate

    Raises:
        ValidationError: If country code is invalid
    """
    if not country_code or len(country_code) != 2:
        raise ValidationError(
            f"Invalid country code: {country_code}. Must be 2-letter ISO 3166-1 alpha-2 code"
        )

    if not country_code.isalpha():
        raise ValidationError(f"Country code must contain only letters: {country_code}")
