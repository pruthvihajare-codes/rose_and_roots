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
    
class UserProfile(models.Model):
    """Extended profile information for users"""
    id = models.AutoField(primary_key=True)
    
    # Link to the user
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        null=True, 
        blank=True
    )
    
    # Address Information (Single Address - No office/home distinction)
    address_line1 = models.CharField(max_length=255, null=True, blank=True)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    landmark = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)
    country = models.CharField(max_length=100, default='India')
    
    # Contact Information (additional)
    alternate_phone = models.CharField(max_length=15, null=True, blank=True)
    
    # Preferences
    newsletter_subscribed = models.BooleanField(default=False)
    sms_notifications = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"Profile for {self.user.email}"
    
    def get_full_address(self):
        """Return formatted full address"""
        parts = []
        if self.address_line1:
            parts.append(self.address_line1)
        if self.address_line2:
            parts.append(self.address_line2)
        if self.landmark:
            parts.append(f"Near {self.landmark}")
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.pincode:
            parts.append(self.pincode)
        if self.country:
            parts.append(self.country)
        return ', '.join(parts)
    
    def get_completion_percentage(self):
        """Calculate profile completion percentage"""
        total_fields = 0
        completed_fields = 0
        
        # Personal Information fields
        personal_fields = [
            self.user.first_name,
            self.user.last_name,
            self.user.phone,
            self.date_of_birth,
            self.gender,
            self.alternate_phone,
        ]
        
        # Address fields
        address_fields = [
            self.address_line1,
            self.city,
            self.state,
            self.pincode,
        ]
        
        # Count total fields
        total_fields = len(personal_fields) + len(address_fields)
        
        # Count completed personal fields
        for field in personal_fields:
            if field and str(field).strip():
                completed_fields += 1
        
        # Count completed address fields
        for field in address_fields:
            if field and str(field).strip():
                completed_fields += 1
        
        # Calculate percentage
        if total_fields == 0:
            return 0
        
        percentage = (completed_fields / total_fields) * 100
        return round(percentage)
    
    def get_missing_fields(self):
        """Return list of missing fields"""
        missing = []
        
        if not self.user.first_name:
            missing.append("First Name")
        if not self.user.last_name:
            missing.append("Last Name")
        if not self.user.phone:
            missing.append("Phone Number")
        if not self.date_of_birth:
            missing.append("Date of Birth")
        if not self.gender:
            missing.append("Gender")
        if not self.alternate_phone:
            missing.append("Alternate Phone")
        if not self.address_line1:
            missing.append("Address")
        if not self.city:
            missing.append("City")
        if not self.state:
            missing.append("State")
        if not self.pincode:
            missing.append("Pincode")
        
        return missing
    
class EmailOTP(models.Model):
    """Store OTPs for email verification"""
    id = models.AutoField(primary_key=True)
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempt_count = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    class Meta:
        db_table = 'email_otp'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['otp_code']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.email} - {self.otp_code}"
    
    def is_expired(self):
        """Check if OTP has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def can_attempt(self):
        """Check if user can attempt verification"""
        return self.attempt_count < self.max_attempts
    
    def increment_attempt(self):
        """Increment attempt count"""
        self.attempt_count += 1
        self.save()
    
    @classmethod
    def generate_otp(cls):
        """Generate a 6-digit OTP"""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    @classmethod
    def create_otp(cls, email):
        """Create a new OTP for email"""
        from django.utils import timezone
        import datetime
        
        # Delete any existing unverified OTPs for this email
        cls.objects.filter(email=email, is_verified=False).delete()
        
        # Generate OTP
        otp_code = cls.generate_otp()
        
        # Set expiry (10 minutes from now)
        expires_at = timezone.now() + datetime.timedelta(minutes=10)
        
        # Create OTP record
        otp = cls.objects.create(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at
        )
        
        return otp