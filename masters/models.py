from django.db import models

# Create your models here.

class Occasion(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150, null=True, blank=True)
    slug = models.SlugField(max_length=150, unique=True, null=True, blank=True)
    icon = models.CharField(max_length=255, null=True, blank=True)

    is_active = models.IntegerField(default=1)

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'occasion'

    def __str__(self):
        return self.name or f"Occasion {self.id}"

class Bouquet(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=200, unique=True, null=True, blank=True)

    short_description = models.CharField(max_length=300, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percent = models.IntegerField(null=True, blank=True)

    instruction_text = models.CharField(max_length=500, null=True, blank=True)
    delivery_info = models.CharField(max_length=255, null=True, blank=True)

    same_day_available = models.IntegerField(default=0)
    is_featured = models.IntegerField(default=0)
    is_active = models.IntegerField(default=1)
    
    buy_now = models.IntegerField(default=0, help_text='0: WhatsApp Inquiry, 1: Normal Buy Now')

    occasions = models.ManyToManyField(
        Occasion,
        through='BouquetOccasion',
        related_name='bouquets',
        blank=True
    )
    
    # Add category field - ForeignKey to parameter_master
    category = models.ForeignKey(
        'parameter_master',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bouquets',
        db_column='category_id',
        help_text='Product category from parameter_master'
    )

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'bouquet'

    def __str__(self):
        return self.name or f"Bouquet {self.id}"

class BouquetOccasion(models.Model):
    id = models.AutoField(primary_key=True)

    bouquet = models.ForeignKey(
        Bouquet,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    occasion = models.ForeignKey(
        Occasion,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    class Meta:
        db_table = 'bouquet_occasion'
        unique_together = ('bouquet', 'occasion')

    def __str__(self):
        return f"{self.bouquet} - {self.occasion}"

class BouquetImage(models.Model):
    id = models.AutoField(primary_key=True)

    bouquet = models.ForeignKey(
        Bouquet,
        on_delete=models.CASCADE,
        related_name='images',
        null=True,
        blank=True
    )

    image_name = models.CharField(max_length=255, null=True, blank=True)

    image_path = models.CharField(max_length=255, null=True, blank=True)

    is_active = models.IntegerField(default=1)

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    created_by = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = 'bouquet_image'

    def __str__(self):
        return f"Image for {self.bouquet.name}" if self.bouquet else f"Image {self.id}"

class Vendor(models.Model):
    id = models.AutoField(primary_key=True)

    vendor_name = models.CharField(max_length=200, null=True, blank=True)
    phone_no = models.CharField(max_length=20, null=True, blank=True)
    email = models.CharField(max_length=150, null=True, blank=True)

    area_name = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)

    vendor_address = models.TextField(null=True, blank=True)

    is_active = models.IntegerField(default=1)

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    created_by = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = 'vendor'

    def __str__(self):
        return self.vendor_name or f"Vendor {self.id}"

class DeliveryPincode(models.Model):
    pincode = models.CharField(max_length=6, unique=True)
    place_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=150, null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = 'delivery_pincode'

    def __str__(self):
        return f"{self.pincode} - {self.place_name}"

class parameter_master(models.Model):
    parameter_id = models.AutoField(primary_key=True)
    parameter_name =models.TextField(null=True,blank=True)
    parameter_value =models.TextField(null=True,blank=True)
    isactive = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        db_table = 'parameter_master'
    def __str__(self):
        return self.parameter_name