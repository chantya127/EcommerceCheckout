"""Main entry point for the e-commerce discount calculation system.

This module demonstrates the usage of the discount calculation system with sample data.
It includes a factory class for setting up the system and example usage of the discount service.
"""

import asyncio
from decimal import Decimal

from ECommerceCheckout.enums import BrandTier, CustomerTier, CardType, PaymentMethod
from ECommerceCheckout.models import Product, CartItem, PaymentInfo, CustomerProfile
from ECommerceCheckout.repository import InventoryRepository, DiscountRepository
from ECommerceCheckout.service import InventoryService, ProductService, DiscountService
from ECommerceCheckout.strategy import (
    BrandDiscountStrategy,
    CategoryDiscountStrategy,
    PaymentDiscountStrategy,
    CouponDiscountStrategy
)


class ECommerceFactory:
    """Factory class for setting up and configuring the e-commerce system.
    
    This class handles the initialization of all necessary components including:
    - Inventory and discount repositories
    - Core services (inventory, product, discount)
    - Discount strategies
    """

    async def setup(self) -> DiscountService:
        """Set up and configure the e-commerce system with sample data.
        
        Returns:
            DiscountService: Configured discount service ready for use
            
        Note:
            This method initializes sample products and configures all discount strategies.
        """

        # Initialize repositories
        inventory_repository = InventoryRepository()
        discount_repository = DiscountRepository()
        
        # Set up sample products with initial inventory and pricing

        # Premium brand products with different minimum price points
        p1 = Product(
            id='1',
            brand='PUMA',
            brand_tier=BrandTier.PREMIUM,
            category='Shoes',
            base_price=Decimal(1000),
            current_price=Decimal(1000),
            quantity=10,
            min_price_possible=Decimal(800)  # 20% below base price
        )

        p2 = Product(
            id='2',
            brand='ADIDAS',
            brand_tier=BrandTier.PREMIUM,
            category='Shoes',
            base_price=Decimal(1000),
            current_price=Decimal(1000),
            quantity=10,
            min_price_possible=Decimal(700)  # 30% below base price
        )

        p3 = Product(
            id='3',
            brand='NIKE',
            brand_tier=BrandTier.PREMIUM,
            category='Shoes',
            base_price=Decimal(1000),
            current_price=Decimal(1000),
            quantity=10,
            min_price_possible=Decimal(850)  # 15% below base price
        )

        # Add products to inventory
        await inventory_repository.add_products(products=[p1, p2, p3])

        # Initialize services
        inventory_service = InventoryService(inventory_repository=inventory_repository)
        product_service = ProductService(inventory_repository=inventory_repository)

        # Set up discount service with all available strategies
        # Note: The order of adding strategies determines their application order
        curr_discount_service = DiscountService(
            product_service=product_service,
            discount_repository=discount_repository,
            inventory_service=inventory_service
        )
        
        # Add discount strategies in order of application:
        # 1. Category-based discounts
        # 2. Brand-based discounts
        # 3. Payment method discounts
        # 4. Coupon-based discounts
        await curr_discount_service.add_discount_strategy(CategoryDiscountStrategy(name="CategoryDiscount"))
        await curr_discount_service.add_discount_strategy(BrandDiscountStrategy(name="BrandDiscount"))
        await curr_discount_service.add_discount_strategy(PaymentDiscountStrategy(name="PaymentDiscount"))
        await curr_discount_service.add_discount_strategy(CouponDiscountStrategy(name="CouponDiscount"))
        
        return curr_discount_service

def create_sample_cart() -> tuple[list[CartItem], CustomerProfile, PaymentInfo]:
    """Create sample shopping cart data for demonstration.
    
    Returns:
        tuple: A tuple containing (cart_items, customer_profile, payment_info)
    """
    # Create sample cart items
    cart_items = [
        CartItem(
            product=Product(
                id='1',
                brand='PUMA',
                brand_tier=BrandTier.PREMIUM,
                category='SHOES',
                current_price=Decimal(1000)
            ),
            quantity=2
        ),
        CartItem(
            product=Product(
                id='2',
                brand='ADIDAS',
                brand_tier=BrandTier.PREMIUM,
                category='SHOES',
                current_price=Decimal(1000)
            ),
            quantity=1
        ),
    ]

    # Create sample customer profile
    customer = CustomerProfile(
        customer_tier=CustomerTier.PREMIUM,
        name="John Doe",
        email="john@example.com",
        id="123"
    )

    # Create sample payment information
    payment_info = PaymentInfo(
        method=PaymentMethod.CARD,
        card_type=CardType.DEBIT,
        bank_name="HDFC"
    )
    
    return cart_items, customer, payment_info


async def main():
    """Main function to demonstrate the discount calculation system."""
    # Initialize the system
    factory = ECommerceFactory()
    discount_service = await factory.setup()
    
    # Create sample data
    cart_items, customer, payment_info = create_sample_cart()
    
    # Example 1: Calculate and display discounts
    print("\n=== Calculating Cart Discounts ===")
    discounted_price = await discount_service.calculate_cart_discounts(
        cart_items=cart_items,
        customer=customer,
        payment_info=payment_info,
        code="COUPON_DISCOUNT",  # Example coupon code
        reserve_inventory=True
    )

    # Display results
    print(f"Original Price: ₹{discounted_price.original_price}")
    print(f"Final Price: ₹{discounted_price.final_price}")
    print(f"Total Discount: ₹{discounted_price.original_price - discounted_price.final_price}")
    print(f"Applied Discounts: {discounted_price.applied_discounts}")
    
    # Example 2: Validate discount code
    print("\n=== Validating Discount Code ===")
    try:
        is_valid = await discount_service.validate_discount_code(
            cart_items=cart_items,
            customer=customer,
            code="COUPON_DISCOUNT"
        )
        print(f"Discount code is valid: {is_valid}")
    except Exception as e:
        print(f"Error validating discount code: {e}")


if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())
