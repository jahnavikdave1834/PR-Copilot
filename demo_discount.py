"""Demo pricing and discount calculation module for PR evaluation."""

from typing import Optional


def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate the final discounted price for a product.
    
    Raises:
        ValueError: If price is negative or discount_percent is outside [0, 100].
    """
    if price < 0:
        raise ValueError("Price cannot be negative")
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount percentage must be between 0 and 100")

    discount_amount = price * (discount_percent / 100.0)
    return round(price - discount_amount, 2)


def apply_coupon_code(price: float, coupon_code: Optional[str]) -> float:
    """Apply a promotional coupon code with safe string and format handling."""
    if not coupon_code:
        return price

    try:
        cleaned_code = coupon_code.strip().upper()
        coupons = {
            "SAVE10": 10.0,
            "SAVE20": 20.0,
            "HALFOFF": 50.0,
        }
        if cleaned_code not in coupons:
            return price

        rate = coupons[cleaned_code]
        return calculate_discount(price, rate)
    except Exception as err:
        # Fallback to original price on unexpected error during coupon parsing
        return price
