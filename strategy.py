from decimal import Decimal
from typing import Optional, Tuple

from ECommerceCheckout.enums import PaymentMethod
from ECommerceCheckout.repository import DiscountRepository
from ECommerceCheckout.models import Product, CustomerProfile, PaymentInfo


class DiscountStrategy:

    def __init__(self, name: str):
        self.name = name

    async def apply_discounts(
            self,
            product: Product,
            customer: CustomerProfile,
            discount_repo: DiscountRepository,
            payment_info: Optional[PaymentInfo] = None,
            code: Optional[str] = None
            ) -> [str, Decimal]:
        raise NotImplementedError

    async def validate_discount_code(
            self, product: Product,
            customer: CustomerProfile,
            discount_repo: DiscountRepository,
            code: Optional[str] = None,
            payment_info: Optional[PaymentInfo] = None) -> bool:
        raise NotImplementedError


class BrandDiscountStrategy(DiscountStrategy):

    def __init__(self, name: str):
        super().__init__(name=name)

    async def apply_discounts(
            self,
            product: Product,
            customer: CustomerProfile,
            discount_repo: DiscountRepository,
            code: Optional[str] = None,
            payment_info: Optional[PaymentInfo] = None) -> Tuple[bool, Decimal]:

        is_valid: bool = await self.validate_discount_code(
            code=None,
            product=product,
            customer=customer,
            discount_repo=discount_repo,
            payment_info=payment_info)

        if not is_valid:
            print(f"Brand discount not applicable for {product.id}")
            return False, Decimal(0)

        brand_discounts = discount_repo.brand_discounts[customer.customer_tier]
        if product.brand in brand_discounts:
            percentage = brand_discounts[product.brand]
            discount_amount = product.current_price * percentage
            product.current_price = product.current_price - (product.current_price * percentage)
            product.current_price = max(product.current_price, product.min_price_possible)
            return True, discount_amount

        else:
            return False, Decimal(0)

    async def validate_discount_code(
            self, product: Product,
            customer: CustomerProfile,
            discount_repo: DiscountRepository,
            code: Optional[str] = None,
            payment_info: Optional[PaymentInfo] = None) -> bool:

        brand_discounts = discount_repo.brand_discounts[customer.customer_tier]
        if product.brand in brand_discounts:
            return True
        else:
            return False


class CategoryDiscountStrategy(DiscountStrategy):
    def __init__(self, name: str):
        super().__init__(name=name)

    async def apply_discounts(
            self, product: Product,
            customer: CustomerProfile,
            discount_repo: DiscountRepository,
            code: Optional[str] = None,
            payment_info: Optional[PaymentInfo] = None) -> Tuple[bool, Decimal]:

        is_valid = await self.validate_discount_code(
            code=None,
            product=product,
            customer=customer,
            discount_repo=discount_repo,
            payment_info=payment_info)

        if not is_valid:
            print(f"Category discount not applicable  for product {product.id}")
            return False, Decimal(0)

        category_discounts = discount_repo.category_discounts[customer.customer_tier]
        if product.category in category_discounts:
            percentage = category_discounts[product.category]
            discount_amount = product.current_price * percentage

            product.current_price = product.current_price - (product.current_price * percentage)
            product.current_price = max(product.current_price, product.min_price_possible)
            return True, discount_amount
        else:
            return False, Decimal(0)

    async def validate_discount_code(
            self, product: Product,
            customer: CustomerProfile,
            discount_repo: DiscountRepository,
            code: Optional[str] = None,
            payment_info: Optional[PaymentInfo] = None) -> bool:

        category_discounts = discount_repo.category_discounts[customer.customer_tier]
        if product.category in category_discounts:
            return True
        else:
            return False


class PaymentDiscountStrategy(DiscountStrategy):

    def __init__(self, name: str):
        super().__init__(name=name)

    async def apply_discounts(
            self, product: Product,
            customer: CustomerProfile,
            discount_repo: DiscountRepository,
            code: Optional[str] = None,
            payment_info: Optional[PaymentInfo] = None) -> Tuple[bool, Decimal]:

        is_valid = await self.validate_discount_code(
            code=None,
            product=product,
            customer=customer,
            discount_repo=discount_repo,
            payment_info=payment_info)

        if not is_valid:
            print(f"Payment discount not applicable for {product.id}")
            return False, Decimal(0)

        card_type_discounts = discount_repo.card_type_discounts[customer.customer_tier]
        if payment_info.card_type in card_type_discounts:
            percentage = card_type_discounts[payment_info.card_type]
            discount_amount = product.current_price * percentage

            product.current_price = product.current_price - (product.current_price * percentage)
            product.current_price = max(product.current_price, product.min_price_possible)
            return True, discount_amount
        else:
            return False, Decimal(0)

    async def validate_discount_code(
            self, product: Product,
            customer: CustomerProfile,
            discount_repo: DiscountRepository,
            code: Optional[str] = None,
            payment_info: Optional[PaymentInfo] = None) -> bool:

        if not payment_info:
            return False

        # don't apply discount if payment method is not card
        if payment_info.method != PaymentMethod.CARD:
            return False

        card_type_discounts = discount_repo.card_type_discounts[customer.customer_tier]
        if payment_info.card_type in card_type_discounts:
            return True
        else:
            return False


class CouponDiscountStrategy(DiscountStrategy):

    def __init__(self, name: str):
        super().__init__(name=name)

    async def apply_discounts(
            self, product: Product,
            customer: CustomerProfile,
            discount_repo: DiscountRepository,
            code: Optional[str] = None,
            payment_info: Optional[PaymentInfo] = None) -> Tuple[bool, Decimal]:

        is_valid = await self.validate_discount_code(
            code=code,
            product=product,
            customer=customer,
            discount_repo=discount_repo,
            payment_info=payment_info)

        if not is_valid:
            print(f"Coupon discount -> {code} not applicable for {product.id}")
            return False, Decimal(0)

        percentage = discount_repo.coupon_discounts[code]
        discount_amount = product.current_price * percentage

        product.current_price = product.current_price - (product.current_price * percentage)
        product.current_price = max(product.current_price, product.min_price_possible)
        return True, discount_amount

    async def validate_discount_code(
            self, product: Product,
            customer: CustomerProfile,
            discount_repo: DiscountRepository,
            code: Optional[str] = None,
            payment_info: Optional[PaymentInfo] = None) -> bool:

        if not code:
            return False

        if code in discount_repo.coupon_discounts:
            return True
        else:
            return False
