from enum import Enum


# Create enums for card type, payment method, discount type, brands, etc

class BrandTier(str, Enum):
    PREMIUM = "PREMIUM"
    REGULAR = "REGULAR"
    BUDGET = "BUDGET"


class CustomerTier(str, Enum):
    PREMIUM = "PREMIUM"
    REGULAR = "REGULAR"
    BUDGET = "BUDGET"


class CardType(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class PaymentMethod(str, Enum):
    CARD = "CARD"
    UPI = "UPI"
