# store/middleware.py

from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
import re
import logging
import time

logger = logging.getLogger(__name__)

class PageOriginMiddleware:
    """
    Middleware to ensure pages are accessed through proper navigation,
    not by directly typing URL in browser
    """
    
    # Pages that should not be accessed directly via URL
    RESTRICTED_PAGES = [
        r'^/shop/$',                    # Shop page
        r'^/product-detail/',           # Product detail page
        r'^/cart_view/$',               # Cart page
        r'^/checkout/$',                # Checkout page
        r'^/profile/',                  # Profile pages
        r'^/wishlist/',                 # Wishlist page
    ]
    
    # Pages that should clear session on direct access
    CLEAR_SESSION_ON_DIRECT = [
        r'^/shop/$',
        r'^/product-detail/',
        r'^/cart_view/$',
        r'^/checkout/$',
        r'^/profile/',
        r'^/wishlist/',
    ]
    
    # Allowed referrers (internal pages that can access these)
    ALLOWED_REFERRERS = [
        'http://127.0.0.1:8000',
        'http://localhost:8000',
        'https://littlecraftone.com',
        'https://www.littlecraftone.com',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        current_path = request.path
        full_path = request.get_full_path()
        
        # Skip for admin, static, media files, and public pages
        if self._should_skip(request, current_path):
            response = self.get_response(request)
            return response
        
        # Check if current page is restricted from direct access
        if self._is_restricted_page(current_path):
            # Check if request is coming from internal navigation
            if not self._has_valid_referrer(request):
                # Log unauthorized attempt
                self._log_unauthorized_access(request, full_path)
                
                # Clear session on direct access for sensitive pages
                if self._should_clear_session(current_path):
                    self._clear_user_session(request)
                
                # Add warning message
                messages.warning(request, 
                    '🚫 Direct URL access is not allowed. Please use the navigation menu.')
                
                # Redirect to home
                return redirect('/')
        
        response = self.get_response(request)
        return response
    
    def _should_skip(self, request, path):
        """Skip certain paths"""
        skip_paths = [
            '/admin/', '/static/', '/media/', 
            '/login/', '/register/', '/logout/', 
            '/accounts/', '/api/', '/__debug__/',
            '/',  # Home page
            '/about-us/',  # About page
            '/contact-us/',  # Contact page
        ]
        for skip in skip_paths:
            if path.startswith(skip):
                return True
        return False
    
    def _is_restricted_page(self, path):
        """Check if current path is restricted from direct access"""
        for pattern in self.RESTRICTED_PAGES:
            if re.match(pattern, path):
                return True
        return False
    
    def _should_clear_session(self, path):
        """Check if we should clear session for this page"""
        for pattern in self.CLEAR_SESSION_ON_DIRECT:
            if re.match(pattern, path):
                return True
        return False
    
    def _clear_user_session(self, request):
        """Clear user session and logout the user"""
        try:
            # Store user info for logging
            user_email = request.user.email if request.user.is_authenticated else 'Anonymous'
            session_key = request.session.session_key
            
            # Log the session clear
            logger.warning(f"Clearing session for user: {user_email}, Session: {session_key}")
            
            # Logout the user
            if request.user.is_authenticated:
                logout(request)
            
            # Clear all session data
            request.session.flush()
            
            logger.info(f"Session cleared successfully for: {user_email}")
            
        except Exception as e:
            logger.error(f"Error clearing session: {str(e)}")
    
    def _has_valid_referrer(self, request):
        """
        Check if request has a valid referrer (came from internal navigation)
        """
        referer = request.META.get('HTTP_REFERER')
        
        # If no referrer, it's likely direct URL access
        if not referer:
            return False
        
        # Check if referrer is from our own site
        for allowed_referrer in self.ALLOWED_REFERRERS:
            if referer.startswith(allowed_referrer):
                return True
        
        return False
    
    def _log_unauthorized_access(self, request, path):
        """Log unauthorized direct access attempts"""
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        user_email = request.user.email if request.user.is_authenticated else 'Anonymous'
        
        logger.warning(f"DIRECT URL ACCESS - User: {user_email}, Path: {path}, IP: {ip}, UA: {user_agent[:100]}")


class SessionValidationMiddleware:
    """
    Validate session integrity and prevent session hijacking
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for public pages
        public_paths = ['/login/', '/register/', '/', '/shop/', '/about-us/', '/contact-us/', '/product-detail/']
        
        # Check if current path is in public paths or starts with any
        is_public = False
        for public_path in public_paths:
            if request.path.startswith(public_path):
                is_public = True
                break
        
        if is_public:
            response = self.get_response(request)
            return response
        
        # Only validate for authenticated users
        if request.user.is_authenticated:
            # Check session creation time
            session_created = request.session.get('session_created_at')
            if session_created:
                current_time = time.time()
                
                # Session older than 30 minutes? Require re-login
                if current_time - session_created > 1800:  # 30 minutes
                    logout(request)
                    request.session.flush()
                    messages.warning(request, 'Your session has expired. Please login again.')
                    return redirect('/login/')
            
            # Check IP address (optional, but good for security)
            current_ip = request.META.get('REMOTE_ADDR')
            session_ip = request.session.get('ip_address')
            if session_ip and current_ip and current_ip != session_ip:
                # IP changed - possible session hijacking
                logout(request)
                request.session.flush()
                messages.error(request, 'Security alert: IP address changed. Please login again.')
                return redirect('/login/')
        
        response = self.get_response(request)
        return response


class ProductAccessMiddleware:
    """
    Ensure products are accessed through shop page, not directly
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if it's a product detail request
        if '/product-detail/' in request.path:
            # Get the product ID from query params
            product_id = request.GET.get('id')
            
            if product_id:
                # Check if user came from shop page
                referer = request.META.get('HTTP_REFERER')
                
                # If no referrer or referrer is not from shop, redirect
                if not referer:
                    # Direct access
                    self._log_direct_product_access(request, product_id)
                    messages.warning(request, 'Please browse products from our shop page first.')
                    return redirect('/shop/')
                
                # Check if referrer is from shop or home
                valid_referrers = ['/shop/', '/', '/product-detail/']
                is_valid = False
                for valid in valid_referrers:
                    if valid in referer:
                        is_valid = True
                        break
                
                if not is_valid:
                    self._log_direct_product_access(request, product_id)
                    messages.warning(request, 'Please browse products from our shop page first.')
                    return redirect('/shop/')
                
                # Valid access - store in session for tracking
                request.session['last_viewed_product'] = product_id
                request.session['product_view_timestamp'] = time.time()
        
        response = self.get_response(request)
        return response
    
    def _log_direct_product_access(self, request, product_id):
        """Log direct product access attempts"""
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        user_email = request.user.email if request.user.is_authenticated else 'Anonymous'
        
        logger.warning(f"DIRECT PRODUCT ACCESS - User: {user_email}, Product: {product_id}, IP: {ip}, UA: {user_agent[:100]}")