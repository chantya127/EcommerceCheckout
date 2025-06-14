"""Data models for the e-commerce application.

This module defines the core data structures used throughout the application,
including products, shopping cart items, payment information, and discount logic.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict

from pydantic import field_validator

from ECommerceCheckout.enums import BrandTier, PaymentMethod, CardType, CustomerTier


@dataclass
class Product:
    """Represents a product in the e-commerce system.
    
    Attributes:
        id: Unique identifier for the product
        brand: Brand name of the product
        brand_tier: Tier classification of the brand (e.g., PREMIUM, BUDGET)
        category: Product category (e.g., 'SHOES', 'T-SHIRTS')
        base_price: Original price before any discounts
        current_price: Current price after applying brand/category discounts
        min_price_possible: Minimum allowed price for the product
        quantity: Available stock quantity
    """
    id: str
    brand: str
    brand_tier: BrandTier
    category: str
    base_price: Optional[Decimal] = None
    current_price: Optional[Decimal] = None  # After brand/category discount
    min_price_possible: Optional[Decimal] = None
    quantity: Optional[int] = None


@dataclass
class CartItem:
    """Represents an item in the shopping cart.
    
    Attributes:
        product: The product being purchased
        quantity: Number of units of the product in the cart
    """
    product: Product
    quantity: int


@dataclass
class PaymentInfo:
    """Contains payment information for an order.
    
    Attributes:
        method: Payment method (e.g., CARD, UPI)
        bank_name: Name of the bank (if applicable)
        card_type: Type of card (CREDIT/DEBIT) if payment method is CARD
    """
    method: PaymentMethod  # CARD, UPI, etc
    bank_name: Optional[str] = None
    card_type: Optional[CardType] = None  # CREDIT, DEBIT


@dataclass
class DiscountedPrice:
    """Represents the result of applying discounts to a cart.
    
    Attributes:
        original_price: Total price before any discounts
        final_price: Total price after applying all discounts
        applied_discounts: Dictionary mapping product IDs to applied discounts
        message: Human-readable summary of the price calculation
    """
    original_price: Decimal
    final_price: Decimal
    applied_discounts: Dict[str, dict]  # discount_name -> amount
    message: str


@dataclass
class CustomerProfile:
    """Stores customer information and preferences.
    
    Attributes:
        customer_tier: Customer's loyalty tier (PREMIUM, REGULAR, BUDGET)
        name: Customer's full name
        email: Customer's email address
        id: Unique customer identifier
    """
    customer_tier: CustomerTier
    name: str
    email: str
    id: str



@dataclass
class Discount:
    """Represents a discount that can be applied to products or orders.
    
    This model supports various types of discounts including:
    - Fixed amount discounts
    - Percentage-based discounts
    - Tiered discounts (by brand, category, customer tier)
    - Time-limited discounts
    
    Attributes:
        name: Name/identifier for the discount
        amount: Fixed discount amount (mutually exclusive with percentage)
        percentage: Percentage discount (0-100, mutually exclusive with amount)
        brand_tier: Brand tier this discount applies to (if any)
        brand_name: Specific brand this discount applies to (if any)
        category: Product category this discount applies to (if any)
        card_type: Card type this discount applies to (if any)
        customer_tier: Customer tier this discount applies to (if any)
        code: Optional promotion code for the discount
        start_date: When the discount becomes active
        end_date: When the discount expires
    """
    name: str
    amount: Optional[Decimal] = None
    percentage: Optional[float] = None
    brand_tier: Optional[BrandTier] = None
    brand_name: Optional[str] = None
    category: Optional[str] = None
    card_type: Optional[CardType] = None
    customer_tier: Optional[CustomerTier] = None
    code: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator("percentage", "amount")
    def validate_amount_or_percentage(cls, v, values):
        """Ensure either amount or percentage is provided, but not both.
        
        This validator ensures that a discount has exactly one of:
        - A fixed amount discount, OR
        - A percentage discount
        
        Raises:
            ValueError: If both or neither amount/percentage are provided
        """
        amount = values.get('amount')
        if amount is None and v is None:
            raise ValueError("Either amount or percentage must be provided")
        if amount is not None and v is not None:
            raise ValueError("Cannot specify both amount and percentage")
        return v
