"""Repository module for handling data storage and retrieval operations.

This module contains repository classes that manage the application's data layer,
including product inventory and discount information. It serves as an abstraction
layer between the business logic and data storage.
"""
from decimal import Decimal
from typing import List

from ECommerceCheckout.enums import CustomerTier
from ECommerceCheckout.exceptions import ProductNotFound
from ECommerceCheckout.models import Product, Discount


class InventoryRepository:
    """Repository class for managing product inventory operations.
    
    Provides methods to store, retrieve, and manage product information in memory.
    This implementation uses an in-memory dictionary for storage.
    """

    def __init__(self):
        self._products = {}

    async def upsert(self, product: Product):
        self._products[product.id] = product

    async def get_product(self, product_id: str) -> Product:
        if product_id not in self._products:
            raise ProductNotFound(f"Product with id {product_id} does not exist")
        return self._products[product_id]

    async def get_all_products(self) -> List[Product]:
        return list(self._products.values())

    async def add_products(self, products: List[Product]):
        for product in products:
            await self.upsert(product=product)


class DiscountRepository:
    """Repository class for managing discount-related operations.
    
    Handles storage and retrieval of various types of discounts including:
    - Brand-specific discounts
    - Category-based discounts
    - Card type discounts
    - Coupon codes
    
    Discounts are categorized by customer tier (PREMIUM, REGULAR, BUDGET).
    """

    def __init__(self):
        self._discounts = {}

        self.brand_discounts = {
            CustomerTier.PREMIUM: {"PUMA": Decimal(0.1), "ADIDAS": Decimal(0.1), "NIKE": Decimal(0.1)},
            CustomerTier.REGULAR: {"PUMA": Decimal(0.05), "ADIDAS": Decimal(0.05), "NIKE": Decimal(0.05)},
            CustomerTier.BUDGET: {"PUMA": Decimal(0.05), "ADIDAS": Decimal(0.05), "NIKE": Decimal(0.05)}
        }
        self.category_discounts = {
            CustomerTier.PREMIUM: {"SHOES": Decimal(0.05), "T-SHIRTS": Decimal(0.05), "PANTS": Decimal(0.05)},
            CustomerTier.REGULAR: {"SHOES": Decimal(0.05), "T-SHIRTS": Decimal(0.05), "PANTS": Decimal(0.05)},
            CustomerTier.BUDGET: {"SHOES": Decimal(0.05), "T-SHIRTS": Decimal(0.05), "PANTS": Decimal(0.05)}
        }
        self.card_type_discounts = {
            CustomerTier.PREMIUM: {"CREDIT": Decimal(0.05), "DEBIT": Decimal(0.05)},
            CustomerTier.REGULAR: {"CREDIT": Decimal(0.05), "DEBIT": Decimal(0.05)},
            CustomerTier.BUDGET: {"CREDIT": Decimal(0.05), "DEBIT": Decimal(0.05)}
        }

        self.coupon_discounts = {
            CustomerTier.PREMIUM: {"PUMA10": Decimal(0.1), "ADIDAS10": Decimal(0.1), "NIKE10": Decimal(0.1)},
            CustomerTier.REGULAR: {"PUMA": Decimal(0.05), "ADIDAS": Decimal(0.05), "NIKE": Decimal(0.05)},
            CustomerTier.BUDGET: {"PUMA": Decimal(0.05), "ADIDAS": Decimal(0.05), "NIKE": Decimal(0.05)}
        }

    async def upsert(self, discount: Discount):
        self._discounts[discount.name] = discount

    async def get_discount(self, discount_name: str) -> Discount:
        if discount_name not in self._discounts:
            raise ValueError(f"Discount with name {discount_name} does not exist")
        return self._discounts[discount_name]

    async def get_all_discounts(self) -> List[Discount]:
        return list(self._discounts.values())
