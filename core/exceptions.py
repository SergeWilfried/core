"""
Custom banking exceptions
"""


class BankingException(Exception):
    """Base exception for banking operations"""

    def __init__(self, message: str, code: str = "BANKING_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


# Account exceptions
class AccountNotFoundError(BankingException):
    """Account not found"""

    def __init__(self, message: str):
        super().__init__(message, code="ACCOUNT_NOT_FOUND")


class AccountFrozenError(BankingException):
    """Account is frozen"""

    def __init__(self, message: str):
        super().__init__(message, code="ACCOUNT_FROZEN")


class AccountClosedError(BankingException):
    """Account is closed"""

    def __init__(self, message: str):
        super().__init__(message, code="ACCOUNT_CLOSED")


class InsufficientFundsError(BankingException):
    """Insufficient funds for transaction"""

    def __init__(self, message: str):
        super().__init__(message, code="INSUFFICIENT_FUNDS")


# Transaction exceptions
class TransactionNotFoundError(BankingException):
    """Transaction not found"""

    def __init__(self, message: str):
        super().__init__(message, code="TRANSACTION_NOT_FOUND")


class TransactionFailedError(BankingException):
    """Transaction failed"""

    def __init__(self, message: str):
        super().__init__(message, code="TRANSACTION_FAILED")


class TransactionLimitExceeded(BankingException):
    """Transaction exceeds allowed limit"""

    def __init__(self, message: str):
        super().__init__(message, code="TRANSACTION_LIMIT_EXCEEDED")


class InvalidTransactionError(BankingException):
    """Invalid transaction"""

    def __init__(self, message: str):
        super().__init__(message, code="INVALID_TRANSACTION")


# Customer exceptions
class CustomerNotFoundError(BankingException):
    """Customer not found"""

    def __init__(self, message: str):
        super().__init__(message, code="CUSTOMER_NOT_FOUND")


class CustomerAlreadyExistsError(BankingException):
    """Customer already exists"""

    def __init__(self, message: str):
        super().__init__(message, code="CUSTOMER_ALREADY_EXISTS")


class KYCRequiredError(BankingException):
    """KYC verification required"""

    def __init__(self, message: str):
        super().__init__(message, code="KYC_REQUIRED")


class KYCFailedError(BankingException):
    """KYC verification failed"""

    def __init__(self, message: str):
        super().__init__(message, code="KYC_FAILED")


# Payment exceptions
class PaymentNotFoundError(BankingException):
    """Payment not found"""

    def __init__(self, message: str):
        super().__init__(message, code="PAYMENT_NOT_FOUND")


class PaymentFailedError(BankingException):
    """Payment failed"""

    def __init__(self, message: str):
        super().__init__(message, code="PAYMENT_FAILED")


class PaymentProcessingError(BankingException):
    """Payment processing error"""

    def __init__(self, message: str):
        super().__init__(message, code="PAYMENT_PROCESSING_ERROR")


class PaymentCancelledError(BankingException):
    """Payment was cancelled"""

    def __init__(self, message: str):
        super().__init__(message, code="PAYMENT_CANCELLED")


# Card exceptions
class CardNotFoundError(BankingException):
    """Card not found"""

    def __init__(self, message: str):
        super().__init__(message, code="CARD_NOT_FOUND")


class CardExpiredError(BankingException):
    """Card expired"""

    def __init__(self, message: str):
        super().__init__(message, code="CARD_EXPIRED")


class CardFrozenError(BankingException):
    """Card is frozen"""

    def __init__(self, message: str):
        super().__init__(message, code="CARD_FROZEN")


class InvalidCardOperationError(BankingException):
    """Invalid card operation"""

    def __init__(self, message: str):
        super().__init__(message, code="INVALID_CARD_OPERATION")


# Ledger exceptions
class LedgerNotFoundError(BankingException):
    """Ledger not found"""

    def __init__(self, message: str):
        super().__init__(message, code="LEDGER_NOT_FOUND")


class LedgerOperationError(BankingException):
    """Ledger operation error"""

    def __init__(self, message: str):
        super().__init__(message, code="LEDGER_OPERATION_ERROR")


# Validation exceptions
class ValidationError(BankingException):
    """Validation error"""

    def __init__(self, message: str):
        super().__init__(message, code="VALIDATION_ERROR")


class InvalidAmountError(ValidationError):
    """Invalid amount"""

    def __init__(self, message: str):
        super().__init__(message)


class InvalidCurrencyError(ValidationError):
    """Invalid currency"""

    def __init__(self, message: str):
        super().__init__(message)


# Authorization exceptions
class UnauthorizedError(BankingException):
    """Unauthorized access"""

    def __init__(self, message: str):
        super().__init__(message, code="UNAUTHORIZED")


class ForbiddenError(BankingException):
    """Forbidden operation"""

    def __init__(self, message: str):
        super().__init__(message, code="FORBIDDEN")


# External service exceptions
class FormanceAPIError(BankingException):
    """Formance API error"""

    def __init__(self, message: str):
        super().__init__(message, code="FORMANCE_API_ERROR")


class ExternalServiceError(BankingException):
    """External service error"""

    def __init__(self, message: str, service_name: str = "unknown"):
        self.service_name = service_name
        super().__init__(
            f"{service_name}: {message}", code="EXTERNAL_SERVICE_ERROR"
        )


# Compliance exceptions
class ComplianceError(BankingException):
    """Compliance error"""

    def __init__(self, message: str):
        super().__init__(message, code="COMPLIANCE_ERROR")


class TransactionBlockedError(ComplianceError):
    """Transaction blocked by compliance"""

    def __init__(self, message: str):
        super().__init__(message)


# Regulatory reporting exceptions
class RegulatoryReportError(BankingException):
    """Regulatory reporting error"""

    def __init__(self, message: str):
        super().__init__(message, code="REGULATORY_REPORT_ERROR")
