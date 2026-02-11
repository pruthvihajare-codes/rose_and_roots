from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')
        extra_fields.setdefault('full_name', 'Admin')
        
        # Set default values for superuser
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = (
        ('admin', 'Admin'),
        ('guest', 'Guest'),
    )

    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    first_time_login = models.IntegerField(default=1)
    last_login = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Changed default to False
    role_id = models.BigIntegerField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    dark_mode = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    session_key = models.CharField(max_length=255, null=True, blank=True)
    is_logged_in = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='guest')

    objects = CustomUserManager()

    # Authentication using email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']  # email is already required by USERNAME_FIELD

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.full_name or f"{self.first_name or ''} {self.last_name or ''}".strip()

    def get_short_name(self):
        return self.first_name or self.email

class Roles(models.Model):  # Capitalized class name for consistency
    id = models.AutoField(primary_key=True)
    role_name = models.TextField(null=True, blank=True)
    role_disc = models.TextField(null=True, blank=True)
    role_type = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)
    created_by = models.TextField(null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'roles'
    
    def __str__(self):
        return self.role_name or f"Role {self.id}"

class PasswordStorage(models.Model):  # Capitalized class name for consistency
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='password_storage',
        blank=True, 
        null=True,
        db_column='user_id'
    )
    password_text = models.CharField(max_length=255, null=True, blank=True)  # Renamed to snake_case
    
    class Meta:
        db_table = 'password_storage'
    
    def __str__(self):
        return f"Password for {self.user.email}" if self.user else "Password storage"

class ErrorLog(models.Model):  # Capitalized class name for consistency
    id = models.AutoField(primary_key=True)
    method = models.TextField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    error_date = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    user_id = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'error_log'
    
    def __str__(self):
        return f"Error {self.id} - {self.error_date}"