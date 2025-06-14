"""Service layer for handling core business logic.

This module contains service classes that implement the business logic of the e-commerce application,
including inventory management, product operations, and discount calculations. It acts as an intermediary
between the API/controller layer and the repository layer.
"""
import copy
from decimal import Decimal
from typing import List, Optional, Dict

from ECommerceCheckout.exceptions import InsufficientInventory, ProductNotFound, InvalidDiscountCode
from ECommerceCheckout.repository import InventoryRepository, DiscountRepository
from ECommerceCheckout.models import CartItem, Product, CustomerProfile, PaymentInfo, DiscountedPrice
from ECommerceCheckout.strategy import DiscountStrategy


class InventoryService:
    """Service for managing inventory operations.
    
    Handles inventory-related business logic including reserving and releasing items,
    with proper validation to maintain data consistency.
    """
    
    def __init__(self, inventory_repository: InventoryRepository):
        """Initialize with an inventory repository instance.
        
        Args:
            inventory_repository: Repository for inventory data access
        """
        self._inventory_repository = inventory_repository

    async def reserve_items(self, cart_items: List[CartItem]) -> bool:
        """Reserve inventory for cart items.
        
        Args:
            cart_items: List of items to reserve
            
        Returns:
            bool: True if reservation was successful
            
        Raises:
            InsufficientInventory: If any product doesn't have enough stock
        """
        # First pass: Validate all items are available before making any changes
        for cart_item in cart_items:
            product = await self._inventory_repository.get_product(cart_item.product.id)
            if product.quantity < cart_item.quantity:
                raise InsufficientInventory(f"Not enough inventory for product {product.id}")

        # Second pass: Update inventory for all items
        for cart_item in cart_items:
            product = await self._inventory_repository.get_product(cart_item.product.id)
            product.quantity -= cart_item.quantity
            await self._inventory_repository.upsert(product)

        return True

    async def release_items(self, cart_items: List[CartItem]) -> None:
        """Release previously reserved inventory.
        
        Typically called when an order is cancelled or expires.
        
        Args:
            cart_items: List of items to release back to inventory
        """
        for cart_item in cart_items:
            try:
                product = await self._inventory_repository.get_product(cart_item.product.id)
                product.quantity += cart_item.quantity
                await self._inventory_repository.upsert(product)
            except ProductNotFound:
                # Log warning but don't fail the entire operation
                continue


class ProductService:
    """Service for managing product-related operations.
    
    Handles business logic for product management including availability checks,
    price management, and product retrieval.
    """

    def __init__(self, inventory_repository: InventoryRepository):
        """Initialize with a repository instance.
        
        Args:
            inventory_repository: Repository for product data access
        """
        self._product_repository = inventory_repository

    async def check_if_quantity_available(self, product: Product, quantity: int) -> bool:
        """Check if the requested quantity of a product is available in inventory.
        
        Args:
            product: The product to check
            quantity: Desired quantity
            
        Returns:
            bool: True if the requested quantity is available, False otherwise
        """
        product: Product = await self._product_repository.get_product(product_id=product.id)
        return product.quantity >= quantity

    async def set_min_price(self, product: Product, min_price: Decimal) -> None:
        """Set the minimum allowed price for a product.
        
        Args:
            product: The product to update
            min_price: New minimum price
            
        Note:
            This is typically used for enforcing pricing rules and preventing
            selling below cost or minimum advertised price (MAP).
        """
        product: Product = await self._product_repository.get_product(product_id=product.id)
        product.min_price_possible = min_price
        await self._product_repository.upsert(product=product)

    async def get_all_products(self) -> List[Product]:
        """Retrieve all available products.
        
        Returns:
            List[Product]: List of all products in the system
        """
        return await self._product_repository.get_all_products()

    async def get_product_by_id(self, product_id: str) -> Product:
        """Retrieve a single product by its ID.
        
        Args:
            product_id: Unique identifier of the product
            
        Returns:
            Product: The requested product
            
        Raises:
            ProductNotFound: If no product exists with the given ID
        """
        return await self._product_repository.get_product(product_id=product_id)


class DiscountService:
    """Service for managing discount-related business logic.
    
    Handles the application of various discount strategies, inventory validation,
    and price calculations. This service coordinates between different discount
    strategies and ensures proper application order.
    """

    def __init__(self, product_service: ProductService,
                 discount_repository: DiscountRepository,
                 inventory_service: InventoryService):
        """Initialize the discount service with required dependencies.
        
        Args:
            product_service: Service for product-related operations
            discount_repository: Repository for discount data access
            inventory_service: Service for inventory management
        """
        self._discount_strategies: list[DiscountStrategy] = []
        self.discount_repository = discount_repository
        self.product_service = product_service
        self.inventory_service = inventory_service


    async def add_discount_strategy(self, discount_strategy: DiscountStrategy) -> None:
        """Add a discount strategy to be applied during price calculations.
        
        Args:
            discount_strategy: The discount strategy to add
            
        Note:
            The order in which strategies are added determines their application order.
            Earlier strategies are applied first.
        """
        self._discount_strategies.append(discount_strategy)

    async def _validate_inventory_availability(self, cart_items: List[CartItem]) -> None:
        """Validate that all items in the cart have sufficient inventory.
        
        Args:
            cart_items: List of cart items to validate
            
        Raises:
            InsufficientInventory: If any product doesn't have enough stock
            ProductNotFound: If any product doesn't exist in inventory
            
        Note:
            This is a read-only check that doesn't reserve any inventory.
        """
        for cart_item in cart_items:
            try:
                product = await self.inventory_service._inventory_repository.get_product(
                    cart_item.product.id
                )
                if product.quantity < cart_item.quantity:
                    raise InsufficientInventory(
                        f"Product {product.id} has only {product.quantity} units available, "
                        f"but {cart_item.quantity} units requested"
                    )
            except ProductNotFound:
                raise ProductNotFound(f"Product {cart_item.product.id} not found in inventory")


    async def check_if_quantity_available(self, cart_items: List[CartItem]) -> bool:
        """Check if all items in the cart have sufficient inventory.
        
        Args:
            cart_items: List of cart items to check
            
        Returns:
            bool: True if all items have sufficient inventory, False otherwise
        """
        for cart_item in cart_items:
            product: Product = cart_item.product
            if not await self.product_service.check_if_quantity_available(
                product=product, 
                quantity=cart_item.quantity
            ):
                return False
        return True

    async def calculate_cart_discounts(
            self,
            cart_items: List[CartItem],
            customer: CustomerProfile,
            payment_info: Optional[PaymentInfo] = None,
            code: Optional[str] = None,
            reserve_inventory: bool = False
    ) -> DiscountedPrice:
        """Calculate the final price after applying all applicable discounts.
        
        The discount application follows this order:
        1. Brand and category discounts
        2. Coupon codes
        3. Bank/payment method offers
        
        Args:
            cart_items: List of items in the shopping cart
            customer: Customer profile for tier-based discounts
            payment_info: Optional payment information for payment method discounts
            code: Optional discount/promo code
            reserve_inventory: If True, reserves inventory during calculation
            
        Returns:
            DiscountedPrice: Object containing original price, final price, and applied discounts
            
        Raises:
            InsufficientInventory: If any product doesn't have enough stock
            ProductNotFound: If any product doesn't exist in inventory
            
        Note:
            If reserve_inventory is True, inventory will be reserved. The caller is responsible
            for releasing inventory if the order is not completed.
        """
        # First validate inventory before making any changes
        await self._validate_inventory_availability(cart_items=cart_items)

        # Optionally reserve inventory if requested
        if reserve_inventory:
            await self.inventory_service.reserve_items(cart_items)

        try:
            curr_applied_discounts: Dict[str, dict] = {}
            original_price = Decimal(0)
            final_price = Decimal(0)

            # Calculate the original cart total without any discounts
            for cart_item in cart_items:
                original_price += cart_item.product.current_price * cart_item.quantity

            # Process each item to apply discounts
            for cart_item in cart_items:
                # Create a deep copy to avoid modifying the original product
                product_copy = copy.deepcopy(cart_item.product)

                # Get the latest product data from inventory
                db_product = await self.inventory_service._inventory_repository.get_product(
                    product_copy.id
                )
                # Update product with current inventory data
                product_copy.base_price = db_product.base_price
                product_copy.min_price_possible = db_product.min_price_possible
                product_copy.current_price = db_product.current_price

                # Apply each discount strategy in sequence
                for discount_strategy in self._discount_strategies:
                    applied, discount_amount = await discount_strategy.apply_discounts(
                        product=product_copy,
                        customer=customer,
                        discount_repo=self.discount_repository,
                        payment_info=payment_info,
                        code=code
                    )

                    # Track which discounts were applied to which products
                    if applied:
                        if product_copy.id not in curr_applied_discounts:
                            curr_applied_discounts[product_copy.id] = {}
                        curr_applied_discounts[product_copy.id][discount_strategy.name] = discount_amount

                # Add the discounted item price to the final total
                final_price += product_copy.current_price * cart_item.quantity

            # Return the final calculated prices and applied discounts
            return DiscountedPrice(
                original_price=original_price,
                final_price=final_price,
                applied_discounts=curr_applied_discounts,
                message=f"Final price after applying discounts: {final_price}"
            )

        except Exception as e:
            # If any error occurs during calculation and we reserved inventory,
            # make sure to release it before propagating the error
            if reserve_inventory:
                await self.inventory_service.release_items(cart_items)
            raise e  # Re-raise the original exception with full stack trace

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

        # Validate the code against each item in the cart
        for cart_item in cart_items:
            product: Product = cart_item.product

            # Check the code with each discount strategy
            for discount_strategy in self._discount_strategies:
                is_valid = await discount_strategy.validate_discount_code(
                    discount_repo=self.discount_repository,
                    code=code,
                    product=product,
                    customer=customer
                )

                if not is_valid:
                    raise InvalidDiscountCode(
                        f"Discount code {code} is not valid for product {product.id}"
                    )

        return True  # All validations passed
