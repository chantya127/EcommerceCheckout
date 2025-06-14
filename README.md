# E-Commerce Checkout System

A flexible and extensible e-commerce checkout system with support for multiple discount strategies, inventory management, and customer tiers.

## Features

- **Multiple Discount Strategies**:
  - Brand-based discounts
  - Category-based discounts
  - Payment method discounts
  - Coupon code support
  - Customer tier-based pricing

- **Inventory Management**:
  - Real-time stock validation
  - Inventory reservation system
  - Product availability checks

- **Customer Tiers**:
  - Support for different customer tiers (PREMIUM, REGULAR, BUDGET)
  - Tier-specific pricing and discounts
  - Customizable discount rules per tier

## Project Structure

```
ECommerceCheckout/
├── enums.py          # Enumerations for the application
├── exceptions.py     # Custom exceptions
├── main.py           # Example usage and entry point
├── models.py         # Data models (Product, Cart, Customer, etc.)
├── repository.py     # Data access layer
├── service.py        # Business logic layer
└── strategy.py       # Discount strategy implementations
```

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ECommerceCheckout
   ```

2. The project uses Python's standard library only. No additional dependencies are required.

## Usage

### Running the Example

```bash
python main.py
```

This will execute a sample scenario demonstrating:
1. Setting up products and inventory
2. Creating a shopping cart
3. Applying multiple discount strategies
4. Processing payment
5. Displaying the final price with applied discounts

### Creating Products

```python
from decimal import Decimal
from enums import BrandTier
from models import Product

product = Product(
    id='1',
    brand='NIKE',
    brand_tier=BrandTier.PREMIUM,
    category='Shoes',
    base_price=Decimal('1000.00'),
    current_price=Decimal('1000.00'),
    quantity=10,
    min_price_possible=Decimal('850.00')
)
```

### Processing a Checkout

```python
from service import ECommerceFactory

async def process_checkout():
    # Initialize the system
    factory = ECommerceFactory()
    discount_service = await factory.setup()
    
    # Get cart items, customer, and payment info
    cart_items, customer, payment_info = create_sample_cart()
    
    # Calculate final price with discounts
    result = await discount_service.calculate_cart_discounts(
        cart_items=cart_items,
        customer=customer,
        payment_info=payment_info,
        code="SUMMER20",
        reserve_inventory=True
    )
    
    print(f"Final Price: ₹{result.final_price}")
    print(f"Applied Discounts: {result.applied_discounts}")
```

## Discount Strategies

The system supports multiple discount strategies that can be combined:

1. **Brand Discounts**: Apply discounts based on product brand
2. **Category Discounts**: Discounts for specific product categories
3. **Payment Method Discounts**: Special offers for specific payment methods
4. **Coupon Codes**: One-time use or limited-time discount codes

## Error Handling

The system includes comprehensive error handling for:
- Insufficient inventory
- Invalid discount codes
- Product not found
- Invalid price calculations
- Expired discounts

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Python 3.8+
- Uses Python's built-in `decimal` module for precise financial calculations
- Follows clean architecture principles
