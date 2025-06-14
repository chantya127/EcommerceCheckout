import asyncio
import uuid
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import validator, field_validator


# TODO:
#  Move to pydantic
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

class PaymentMethod(Enum):
    CARD = "CARD"
    UPI = "UPI"


@dataclass
class Product:
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
    product: Product
    quantity: int


@dataclass
class PaymentInfo:
    method: PaymentMethod     # CARD, UPI, etc
    bank_name: Optional[str]
    card_type: Optional[str]  # CREDIT, DEBIT


@dataclass
class DiscountedPrice:
    original_price: Decimal
    final_price: Decimal
    applied_discounts: Dict[str, dict]  # discount_name -> amount
    message: str


@dataclass
class CustomerProfile:
    customer_tier: CustomerTier
    name: str
    email: str
    id: str



# instead of directly storing discount in db, we can use this and store in sql-like db
@dataclass
class Discount:

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

    @field_validator("amount", "percentage")
    def validate_amount_or_percentage(cls, value):
        if value is None:
            raise ValueError("Either amount or percentage must be provided")
        return value


class InventoryRepository:

    def __init__(self):
        self._products = {}

    async def upsert(self, product: Product):
        self._products[product.id] = product

    async def get_product(self, product_id: str) -> Product:
        if product_id not in self._products:
            raise ValueError(f"Product with id {product_id} does not exist")
        return self._products[product_id]

    async def get_all_products(self) -> List[Product]:
        return list(self._products.values())

    async def add_products(self, products: List[Product]):
        for product in products:
            await self.upsert(product=product)


class DiscountRepository:

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
            "COUPON_DISCOUNT": {
            CustomerTier.PREMIUM: {"PUMA": Decimal(0.1), "ADIDAS": Decimal(0.1), "NIKE": Decimal(0.1)},
            CustomerTier.REGULAR: {"PUMA": Decimal(0.05), "ADIDAS": Decimal(0.05), "NIKE": Decimal(0.05)},
            CustomerTier.BUDGET: {"PUMA": Decimal(0.05), "ADIDAS": Decimal(0.05), "NIKE": Decimal(0.05)}
            }
        }

    async def upsert(self, discount: Discount):
        self._discounts[discount.name] = discount

    async def get_discount(self, discount_name: str) -> Discount:
        if discount_name not in self._discounts:
            raise ValueError(f"Discount with name {discount_name} does not exist")
        return self._discounts[discount_name]

    async def get_all_discounts(self) -> List[Discount]:
        return list(self._discounts.values())


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
            product.current_price = product.current_price - (product.current_price * percentage)
            product.current_price = max(product.current_price, product.min_price_possible)
            return True, product.current_price * percentage

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
            product.current_price = product.current_price - (product.current_price * percentage)
            product.current_price = max(product.current_price, product.min_price_possible)
            return True, product.current_price * percentage
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
            product.current_price = product.current_price - (product.current_price * percentage)
            product.current_price = max(product.current_price, product.min_price_possible)
            return True, product.current_price * percentage
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
            print(f"Coupon discount not applicable for {product.id}")
            return False, Decimal(0)

        percentage = discount_repo.coupon_discounts[code]
        product.current_price = product.current_price - (product.current_price * percentage)
        product.current_price = max(product.current_price, product.min_price_possible)
        return True, product.current_price * percentage

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


class ProductService:

    def __init__(self, inventory_repository: InventoryRepository):
        self._product_repository = inventory_repository

    async def check_if_quantity_available(self, product: Product, quantity: int) -> bool:
        product: Product = await self._product_repository.get_product(product_id=product.id)
        return product.quantity >= quantity

    async def set_min_price(self, product: Product, min_price: Decimal):
        product: Product = await self._product_repository.get_product(product_id=product.id)
        product.min_price_possible = min_price
        await self._product_repository.upsert(product=product)

    async def get_all_products(self) -> List[Product]:
        return await self._product_repository.get_all_products()

    async def get_product_by_id(self, product_id: str) -> Product:
        return await self._product_repository.get_product(product_id=product_id)


class DiscountService:

    def __init__(self, product_service: ProductService,
                 discount_repository: DiscountRepository = DiscountRepository()):
        self._discount_strategies: list[DiscountStrategy] = []
        self.discount_repository =discount_repository
        self.product_service = product_service


    async def add_discount_strategy(self, discount_strategy: DiscountStrategy):
        self._discount_strategies.append(discount_strategy)


    async def check_if_quantity_available(self, cart_items: List[CartItem]) -> bool:

        for cart_item in cart_items:
            product: Product = cart_item.product
            if not await self.product_service.check_if_quantity_available(product=product, quantity=cart_item.quantity):
                return False
        return True

    async def calculate_cart_discounts(
            self,
            cart_items: List[CartItem],
            customer: CustomerProfile,
            payment_info: Optional[PaymentInfo] = None,
            code: Optional[str] = None
    ) -> DiscountedPrice:
        """
        Calculate final price after applying discount logic:
        - First apply brand/category discounts
        - Then apply coupon codes
        - Then apply bank offers
        """
        curr_applied_discounts: Dict[str, dict] = {}
        original_price: Decimal = \
            Decimal(sum(cart_item.product.current_price * cart_item.quantity for cart_item in cart_items))
        final_price: Decimal = Decimal(0)

        await self.check_if_quantity_available(cart_items=cart_items)

        for cart_item in cart_items:
            product: Product = cart_item.product

            id_ = product.id
            db_product = await self.product_service.get_product_by_id(product_id=id_)
            product.base_price = db_product.base_price
            product.min_price_possible = db_product.min_price_possible

            for discount_strategy in self._discount_strategies:
                applied, discount_applied = await discount_strategy.apply_discounts(
                    product=product,
                    customer=customer,
                    discount_repo=self.discount_repository,
                    payment_info=payment_info,
                    code=code)
                if not applied:
                    continue

                if product.id not in curr_applied_discounts:
                    curr_applied_discounts[product.id] = {}

                curr_applied_discounts[product.id][discount_strategy.name] = discount_applied
            final_price += product.current_price * cart_item.quantity

        return DiscountedPrice(
            original_price=original_price,
            final_price=final_price,
            applied_discounts=curr_applied_discounts,
            message=f"Final price after applying discounts: {final_price}"
        )

    async def validate_discount_code(
            self,
            code: str,
            cart_items: List[CartItem],
            customer: CustomerProfile) -> bool:
        """
        Validate if a discount code can be applied.
        Handle Myntra-specific cases like:
        - Brand exclusions
        - Category restrictions
        - Customer tier requirements
        """

        await self.check_if_quantity_available(cart_items=cart_items)

        for cart_item in cart_items:
            product: Product = cart_item.product

            for discount_strategy in self._discount_strategies:
                if not discount_strategy.validate_discount_code(code=code, product=product, customer=customer):
                    return False

        return True


class ECommerceFactory:

    async def setup(self):

        # inventory-setup
        inventory_repository = InventoryRepository()
        p1 = Product(
            id='1', brand='PUMA', brand_tier=BrandTier.PREMIUM,
            category='Shoes', base_price=Decimal(1000), current_price=Decimal(1000),
            quantity=10, min_price_possible=Decimal(800))

        p2 = Product(id='2', brand='ADIDAS', brand_tier=BrandTier.PREMIUM, category='Shoes',
                     base_price=Decimal(1000), current_price=Decimal(1000), quantity=10,
                     min_price_possible=Decimal(700))

        p3 = Product(id='3', brand='NIKE', brand_tier=BrandTier.PREMIUM,
                     category='Shoes', base_price=Decimal(1000), current_price=Decimal(1000),
                     quantity=10, min_price_possible=Decimal(850))

        await inventory_repository.add_products(products=[p1, p2, p3])
        product_service = ProductService(inventory_repository=inventory_repository)

        curr_discount_service = DiscountService(product_service=product_service, discount_repository=DiscountRepository())
        await curr_discount_service.add_discount_strategy(CategoryDiscountStrategy(name="CategoryDiscountStrategy"))
        await curr_discount_service.add_discount_strategy(BrandDiscountStrategy(name="BrandDiscountStrategy"))
        await curr_discount_service.add_discount_strategy(PaymentDiscountStrategy(name="PaymentDiscountStrategy"))
        return curr_discount_service

if __name__ == "__main__":
    factory = ECommerceFactory()
    discount_service = asyncio.run(factory.setup())

    curr_cart_items = [
        CartItem(product=Product(id='1', brand='PUMA', brand_tier=BrandTier.PREMIUM, category='SHOES', current_price=Decimal(1000)), quantity=2),
        CartItem(product=Product(id='2', brand='ADIDAS', brand_tier=BrandTier.PREMIUM, category='T-SHIRT', current_price=Decimal(1000)), quantity=1),
    ]
    customer = CustomerProfile(customer_tier=CustomerTier.PREMIUM, name="John Doe", email="example@example.com", id="123")
    payment_info = PaymentInfo(method=PaymentMethod.CARD, card_type=CardType.DEBIT, bank_name="HDFC")
    discounted_price = asyncio.run(
        discount_service.calculate_cart_discounts(
            cart_items=curr_cart_items, customer=customer, payment_info=payment_info,
            code="PUMA20"
        )
    )
    print(discounted_price.__dict__)
