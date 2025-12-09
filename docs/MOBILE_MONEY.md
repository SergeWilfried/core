# Mobile Money Integration Guide

## Overview

The BaaS Core Banking System now supports mobile money payments as a first-class payment method. This enables seamless integration with major mobile money providers across Africa and other emerging markets.

## Supported Providers

### Currently Supported

| Provider | Countries | Currency Codes | Notes |
|----------|-----------|----------------|-------|
| **M-Pesa** | KE, TZ, MZ, ZA | KES, TZS, MZN, ZAR | Most popular in East Africa |
| **MTN Mobile Money** | UG, GH, CI, CM, ZM, BJ, CG, RW | UGX, GHS, XOF, XAF, ZMW | Largest mobile money network in Africa |
| **Airtel Money** | KE, TZ, UG, ZM, MW, NG, CD, RW, GA | Multiple | Pan-African coverage |
| **Orange Money** | SN, ML, BF, CI, CM, NE, MG, GN | XOF, XAF | West/Central Africa focus |
| **Vodacom** | ZA, TZ, MZ, LS | ZAR, TZS, MZN | Southern Africa |
| **Tigo Pesa** | TZ, RW, GH | TZS, GHS | East Africa |
| **EcoCash** | ZW, ZM | ZWL, ZMW | Zimbabwe, Zambia |
| **Wave** | SN, CI, BF, ML | XOF | West Africa, low fees |
| **Chipper Cash** | KE, UG, GH, NG, ZA, TZ, RW | Multiple | Pan-African digital payments |
| **Flutterwave** | Multiple | Multiple | Payment aggregator |

## Architecture

### Data Flow

```
1. Client Request
   ↓
2. API Endpoint (/api/v1/payments/mobile-money)
   ↓
3. Validation Layer
   - E.164 phone number format
   - Provider operates in country
   - Currency is valid
   ↓
4. Payment Service
   - Format destination string
   - Add metadata
   ↓
5. Formance Repository
   - Create ledger postings
   - Call provider API (TODO)
   ↓
6. Response (Payment object with PENDING status)
```

### Destination String Format

Mobile money payments use a structured destination format:

```
provider:country_code:phone_number
```

**Examples**:
- M-Pesa Kenya: `mpesa:KE:+254712345678`
- MTN Uganda: `mtn:UG:+256771234567`
- Airtel Tanzania: `airtel:TZ:+255712345678`

This format allows easy parsing and routing to the appropriate provider.

## Implementation Details

### 1. Models

**File**: [`core/models/payment.py`](../core/models/payment.py)

#### PaymentMethod Enum
```python
class PaymentMethod(str, Enum):
    # ... existing methods
    MOBILE_MONEY = "mobile_money"
```

#### MobileMoneyProvider Enum
```python
class MobileMoneyProvider(str, Enum):
    MPESA = "mpesa"
    MTN_MOBILE_MONEY = "mtn"
    AIRTEL_MONEY = "airtel"
    # ... etc
```

#### MobileMoneyDestination
```python
class MobileMoneyDestination(BaseModel):
    phone_number: str  # E.164 format
    provider: MobileMoneyProvider
    country_code: str  # ISO 3166-1 alpha-2

    def to_destination_string(self) -> str:
        """Convert to: provider:country:phone"""
        return f"{self.provider.value}:{self.country_code}:{self.phone_number}"
```

### 2. Validators

**File**: [`core/utils/validators.py`](../core/utils/validators.py)

#### E.164 Phone Validation
```python
def validate_e164_phone(phone: str) -> None:
    """
    Validates phone number in E.164 format
    Pattern: +[country_code][subscriber_number]
    Example: +254712345678
    """
```

#### Provider-Country Validation
```python
def validate_mobile_money_provider(provider: str, country_code: str) -> None:
    """
    Validates that a provider operates in the specified country
    Raises ValidationError if provider doesn't support the country
    """
```

### 3. Service Layer

**File**: [`core/services/payments.py`](../core/services/payments.py)

```python
async def process_mobile_money_payment(
    self,
    from_account_id: str,
    phone_number: str,
    provider: MobileMoneyProvider,
    country_code: str,
    amount: Decimal,
    currency: str,
    description: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Payment:
    """Process a mobile money payment"""

    # Validates inputs
    validate_e164_phone(phone_number)
    validate_country_code(country_code)
    validate_mobile_money_provider(provider.value, country_code)

    # Creates payment with structured metadata
    # Returns Payment object in PENDING status
```

### 4. API Endpoint

**File**: [`core/api/v1/payments.py`](../core/api/v1/payments.py)

**Endpoint**: `POST /api/v1/payments/mobile-money`

**Request Schema**:
```json
{
  "from_account_id": "acc_123",
  "phone_number": "+254712345678",
  "provider": "mpesa",
  "country_code": "KE",
  "amount": 1000.00,
  "currency": "KES",
  "description": "Payment to merchant",
  "metadata": {}
}
```

**Response Schema**:
```json
{
  "id": "pay_abc123",
  "from_account_id": "acc_123",
  "amount": 1000.00,
  "currency": "KES",
  "payment_method": "mobile_money",
  "destination": "mpesa:KE:+254712345678",
  "status": "pending",
  "description": "Payment to merchant",
  "reference": null
}
```

## Usage Examples

### cURL

```bash
curl -X POST http://localhost:8000/api/v1/payments/mobile-money \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from_account_id": "acc_123",
    "phone_number": "+254712345678",
    "provider": "mpesa",
    "country_code": "KE",
    "amount": 1000.00,
    "currency": "KES",
    "description": "Merchant payment"
  }'
```

### Python SDK

```python
from decimal import Decimal
from core.models.payment import MobileMoneyProvider

# Send M-Pesa payment
payment = await payment_service.process_mobile_money_payment(
    from_account_id="acc_123",
    phone_number="+254712345678",
    provider=MobileMoneyProvider.MPESA,
    country_code="KE",
    amount=Decimal("1000.00"),
    currency="KES",
    description="Payment to merchant"
)

print(f"Payment created: {payment.id}")
print(f"Status: {payment.status}")
```

### JavaScript/TypeScript

```typescript
const response = await fetch('/api/v1/payments/mobile-money', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    from_account_id: 'acc_123',
    phone_number: '+254712345678',
    provider: 'mpesa',
    country_code: 'KE',
    amount: 1000.00,
    currency: 'KES',
    description: 'Merchant payment'
  })
});

const payment = await response.json();
```

## Formance Ledger Integration

### Recommended Posting Structure

Mobile money payments should create a two-step posting in the Formance ledger:

#### Step 1: Initial Debit (PENDING)
```
Posting:
  Source: customer:{account_id}:main
  Destination: mobile_money:{provider}:pending
  Amount: {amount}
  Currency: {currency}
```

#### Step 2: Confirmation (COMPLETED)
```
Posting:
  Source: mobile_money:{provider}:pending
  Destination: mobile_money:{provider}:{phone_number}
  Amount: {amount}
  Currency: {currency}
```

### Metadata Tracking

Each mobile money payment includes structured metadata:

```json
{
  "mobile_money_provider": "mpesa",
  "country_code": "KE",
  "phone_number": "+254712345678",
  "provider_transaction_id": "ABC123XYZ",  // From provider callback
  "provider_fee": "10.00",  // If applicable
  "exchange_rate": "1.0"  // If cross-currency
}
```

## Provider Integration (TODO)

The current implementation provides the foundation. Next steps include:

### 1. Direct Provider APIs

Integrate with provider-specific APIs:

- **M-Pesa**: Safaricom/Vodacom M-Pesa API
- **MTN Mobile Money**: MTN MoMo API
- **Airtel Money**: Airtel Money API
- etc.

### 2. Aggregator Services

Use payment aggregators for easier multi-provider support:

- **Flutterwave**: Supports 10+ mobile money providers
- **Paystack**: Nigeria, Ghana, South Africa, Kenya
- **DPO Pay**: Pan-African
- **Chipper Cash**: Pan-African digital payments

### 3. Webhook Handling

Implement webhook endpoints to receive payment status updates:

```python
@router.post("/webhooks/mobile-money/{provider}")
async def mobile_money_webhook(
    provider: str,
    payload: dict,
    signature: str = Header(...),
):
    """
    Handle mobile money provider webhooks
    - Verify signature
    - Update payment status
    - Update ledger postings
    """
```

### 4. Status Reconciliation

Implement background jobs to check payment status:

```python
async def reconcile_pending_mobile_money_payments():
    """
    Query provider APIs for pending payments
    Update status in database and ledger
    """
```

## Validation Rules

### Phone Number
- **Format**: E.164 (`+[country_code][subscriber_number]`)
- **Length**: 8-15 digits after country code
- **Example**: `+254712345678` (Kenya)

### Country Code
- **Format**: ISO 3166-1 alpha-2
- **Length**: Exactly 2 characters
- **Example**: `KE` (Kenya), `UG` (Uganda)

### Provider-Country Mapping

The system validates that a provider operates in the specified country:

```python
# Valid
provider="mpesa", country="KE"  ✓

# Invalid - M-Pesa doesn't operate in Uganda
provider="mpesa", country="UG"  ✗
```

## Error Handling

### Validation Errors

```python
# Invalid phone format
ValidationError: "Invalid phone number format. Must be in E.164 format (e.g., +254712345678)"

# Provider doesn't operate in country
ValidationError: "Provider 'mpesa' does not operate in country 'UG'. Supported countries: KE, TZ, MZ, ZA"

# Invalid country code
ValidationError: "Invalid country code: ABC. Must be 2-letter ISO 3166-1 alpha-2 code"
```

### Payment Errors

```python
# Insufficient funds
InsufficientFundsError: "Account balance insufficient for payment"

# Account not found
AccountNotFoundError: "Account acc_123 not found"

# Payment failed
PaymentFailedError: "Mobile money payment failed: [provider error message]"
```

## Testing

### Unit Tests

Test the mobile money service methods:

```python
async def test_mobile_money_payment_mpesa_kenya():
    payment = await payment_service.process_mobile_money_payment(
        from_account_id="acc_test",
        phone_number="+254712345678",
        provider=MobileMoneyProvider.MPESA,
        country_code="KE",
        amount=Decimal("1000.00"),
        currency="KES",
    )

    assert payment.payment_method == PaymentMethod.MOBILE_MONEY
    assert payment.destination == "mpesa:KE:+254712345678"
    assert payment.metadata["mobile_money_provider"] == "mpesa"
```

### Integration Tests

Test the API endpoint:

```python
async def test_create_mobile_money_payment_api():
    response = await client.post(
        "/api/v1/payments/mobile-money",
        json={
            "from_account_id": "acc_123",
            "phone_number": "+254712345678",
            "provider": "mpesa",
            "country_code": "KE",
            "amount": 1000.00,
            "currency": "KES",
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["payment_method"] == "mobile_money"
```

## Currency Support

The system now supports African currencies commonly used with mobile money:

| Currency Code | Currency Name | Countries |
|---------------|---------------|-----------|
| KES | Kenyan Shilling | Kenya |
| TZS | Tanzanian Shilling | Tanzania |
| UGX | Ugandan Shilling | Uganda |
| GHS | Ghanaian Cedi | Ghana |
| ZAR | South African Rand | South Africa |
| XOF | West African CFA Franc | Senegal, Mali, Burkina Faso, Ivory Coast, etc. |
| XAF | Central African CFA Franc | Cameroon, Gabon, etc. |
| ZMW | Zambian Kwacha | Zambia |
| ZWL | Zimbabwean Dollar | Zimbabwe |
| MZN | Mozambican Metical | Mozambique |

## Security Considerations

### PII Protection
- Phone numbers are considered PII
- Log only masked phone numbers: `+254****5678`
- Encrypt phone numbers in database
- Include phone numbers in metadata only when necessary

### API Security
- Rate limiting on mobile money endpoints
- Fraud detection for unusual patterns
- Country-specific transaction limits
- Implement 2FA for large transactions

### Provider Credentials
- Store provider API keys securely (env vars, secrets manager)
- Rotate credentials regularly
- Use separate credentials for production/staging

## Future Enhancements

1. **Batch Payments**: Support bulk mobile money disbursements
2. **Recurring Payments**: Schedule recurring mobile money transfers
3. **Payment Links**: Generate payment links for mobile money collection
4. **QR Codes**: Generate QR codes for mobile money payments
5. **Balance Inquiry**: Check mobile money wallet balances
6. **Transaction History**: Fetch provider transaction history
7. **Refunds**: Support mobile money refunds/reversals
8. **Currency Conversion**: Automatic FX for cross-currency payments

## Resources

### Provider Documentation
- [M-Pesa API](https://developer.safaricom.co.ke/)
- [MTN Mobile Money API](https://momodeveloper.mtn.com/)
- [Flutterwave Docs](https://developer.flutterwave.com/)

### Standards
- [E.164 Phone Numbers](https://www.itu.int/rec/T-REC-E.164/)
- [ISO 3166-1 Country Codes](https://www.iso.org/iso-3166-country-codes.html)
- [ISO 4217 Currency Codes](https://www.iso.org/iso-4217-currency-codes.html)

## Support

For questions or issues with mobile money integration:
- GitHub Issues: [Link to repo issues]
- Documentation: [Link to main docs]
- Email: support@yourcompany.com
