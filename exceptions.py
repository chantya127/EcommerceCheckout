class ECommerceException(Exception):
    """Base exception class for all e-commerce related exceptions.
    
    This serves as the parent class for all custom exceptions in the e-commerce system,
    allowing for catching all e-commerce specific exceptions in a single except block.
    """
    pass


class ProductNotFound(ECommerceException):
    """Exception raised when a requested product cannot be found in the system.
    
    This exception is typically raised when attempting to access or manipulate a product
    that doesn't exist or has been removed from the catalog.
    """
    pass


class InsufficientInventory(ECommerceException):
    """Exception raised when there's not enough stock to fulfill an order.
    
    Raised when a customer attempts to purchase a quantity of a product that exceeds
    the available inventory.
    """
    pass


class InvalidDiscountCode(ECommerceException):
    """Exception raised when an invalid or expired discount code is applied.
    
    This exception is raised when a discount code is either not recognized, has expired,
    or cannot be applied to the current order (e.g., minimum order value not met).
    """
    pass
