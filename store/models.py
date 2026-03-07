# models.py (in your app, e.g., cart/models.py or add to existing models)

from django.db import models
from django.conf import settings
from masters.models import *
from accounts.models import *

class Cart(models.Model):
    """Shopping cart header model - pure table definition only"""
    id = models.AutoField(primary_key=True)
    
    # For guest users
    session_key = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    
    # For logged-in users
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cart'
        # One cart per session or per user
        constraints = [
            models.UniqueConstraint(fields=['session_key'], name='unique_session_cart'),
            models.UniqueConstraint(fields=['user'], name='unique_user_cart'),
        ]
    
    def __str__(self):
        if self.user:
            return f"Cart - {self.user.email}"
        return f"Cart - {self.session_key}"

class CartItem(models.Model):
    """Shopping cart items - pure table definition only"""
    id = models.AutoField(primary_key=True)
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    bouquet = models.ForeignKey(
        Bouquet,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    
    # Store useful product information for quick reference
    bouquet_name = models.CharField(max_length=200, null=True, blank=True)
    bouquet_slug = models.SlugField(max_length=200, null=True, blank=True)
    bouquet_image = models.CharField(max_length=500, null=True, blank=True)
    
    # Store encrypted ID for URL safety
    encrypted_id = models.CharField(max_length=500, null=True, blank=True)
    
    # Price at time of adding
    price_at_add = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cart_item'
        unique_together = ['cart', 'bouquet']
    
    def __str__(self):
        return f"{self.bouquet_name or 'Product'} in cart"
    
# models.py (add this in your masters app or create a new reviews app)

class Review(models.Model):
    """Product reviews model"""
    id = models.AutoField(primary_key=True)
    
    bouquet = models.ForeignKey(
        Bouquet,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1 to 5 stars
    comment = models.TextField(max_length=500)  # Word limit handled here
    
    is_active = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product_reviews'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review for {self.bouquet.name} by {self.user.email}"
    
# models.py

class Order(models.Model):
    """Main order model to store checkout information"""
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    id = models.AutoField(primary_key=True)
    
    # User who placed the order (FK to CustomUser)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    # Order Information
    order_number = models.CharField(max_length=50, unique=True)
    order_date = models.DateTimeField(auto_now_add=True)
    
    # Customer Information (snapshot at time of order)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    
    # Shipping Address (snapshot at time of order)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    country = models.CharField(max_length=100, default='India')
    
    # Delivery Information (from checkout page)
    delivery_option = models.CharField(max_length=50, default='standard')
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment Information (from checkout page)
    payment_method = models.CharField(max_length=50, default='cod')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Order Totals (calculated from cart/buy now)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    
    # Additional Information
    order_notes = models.TextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-order_date']
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number: ORD + YYYYMMDD + random 4 digits
            from datetime import datetime
            import random
            date_str = datetime.now().strftime('%Y%m%d')
            rand_str = str(random.randint(1000, 9999))
            self.order_number = f"ORD-{date_str}-{rand_str}"
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    """Items in an order"""
    id = models.AutoField(primary_key=True)
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    # Foreign Key to Bouquet (keep the relationship)
    bouquet = models.ForeignKey(
        Bouquet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items'
    )
    
    # Store product snapshot at time of order (NO image field)
    bouquet_name = models.CharField(max_length=200)
    bouquet_slug = models.SlugField(max_length=200, null=True, blank=True)
    
    # Price snapshot
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percent = models.IntegerField(default=0)
    
    # Quantity (keeping for future, though you use x1)
    quantity = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_items'
    
    def __str__(self):
        return f"{self.bouquet_name} x {self.quantity}"