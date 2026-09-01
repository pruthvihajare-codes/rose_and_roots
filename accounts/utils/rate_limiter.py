# Create a new file: accounts/utils/rate_limiter.py

from django.core.cache import cache
import time

class RateLimiter:
    """Rate limiter for OTP requests"""
    
    def __init__(self, key_prefix, max_attempts=3, time_window=60):
        """
        key_prefix: Prefix for cache key
        max_attempts: Maximum attempts allowed
        time_window: Time window in seconds
        """
        self.key_prefix = key_prefix
        self.max_attempts = max_attempts
        self.time_window = time_window
    
    def get_key(self, identifier):
        """Generate cache key"""
        return f"{self.key_prefix}:{identifier}"
    
    def is_allowed(self, identifier):
        """Check if action is allowed"""
        key = self.get_key(identifier)
        
        # Get current attempts
        attempts = cache.get(key, 0)
        
        if attempts >= self.max_attempts:
            return False
        
        # Increment attempts
        cache.set(key, attempts + 1, self.time_window)
        return True
    
    def get_remaining_attempts(self, identifier):
        """Get remaining attempts"""
        key = self.get_key(identifier)
        attempts = cache.get(key, 0)
        return max(0, self.max_attempts - attempts)
    
    def get_time_remaining(self, identifier):
        """Get time remaining in seconds"""
        key = self.get_key(identifier)
        ttl = cache.ttl(key)
        return ttl if ttl else 0
    
    def reset(self, identifier):
        """Reset rate limit"""
        key = self.get_key(identifier)
        cache.delete(key)

# Create specific rate limiters
email_otp_limiter = RateLimiter('email_otp', max_attempts=3, time_window=300)  # 3 attempts in 5 minutes
otp_verify_limiter = RateLimiter('otp_verify', max_attempts=5, time_window=600)  # 5 attempts in 10 minutes
resend_otp_limiter = RateLimiter('resend_otp', max_attempts=2, time_window=120)  # 2 resends in 2 minutes