# store/middleware.py

from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
import logging

logger = logging.getLogger(__name__)

class DirectAccessMiddleware:
    """
    Strict middleware to block ALL direct URL access with active sessions.
    """
    
    PUBLIC_PAGES = [
        '/login/', '/register/', '/logout/', 
        '/admin/', '/static/', '/media/', '/accounts/',
    ]
    
    EXTERNAL_ALLOWED_PAGES = []
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        current_path = request.path
        
        # Check if user has active session
        if request.user.is_authenticated:
            # For home page - special handling
            if current_path == '/':
                if self._is_direct_browser_access(request):
                    return self._handle_logout_redirect(request, current_path)
            
            # For other pages
            elif not self._is_public_path(current_path):
                access_type = self._get_access_type(request)
                
                if access_type == 'direct':
                    return self._handle_logout_redirect(request, current_path)
                
                elif access_type == 'external' and not self._is_external_allowed(current_path):
                    return self._handle_logout_redirect(request, current_path)
        
        response = self.get_response(request)
        return response
    
    def _is_public_path(self, path):
        """Check if path is public (excluding home)"""
        for public_page in self.PUBLIC_PAGES:
            if path.startswith(public_page):
                return True
        return False
    
    def _is_direct_browser_access(self, request):
        """Detect direct browser access (typing URL)"""
        referer = request.META.get('HTTP_REFERER')
        
        if not referer:
            return True
        
        our_domains = [
            'http://127.0.0.1:8000',
            'http://localhost:8000',
            'https://littlecraftone.com',
            'https://www.littlecraftone.com',
        ]
        
        for domain in our_domains:
            if referer.startswith(domain):
                return False
        
        return True
    
    def _get_access_type(self, request):
        """Determine how the page was accessed"""
        referer = request.META.get('HTTP_REFERER')
        
        if not referer:
            return 'direct'
        
        current_full_url = request.build_absolute_uri()
        
        if referer == current_full_url:
            return 'internal'
        
        our_domains = [
            'http://127.0.0.1:8000',
            'http://localhost:8000',
            'https://littlecraftone.com',
            'https://www.littlecraftone.com',
        ]
        
        for domain in our_domains:
            if referer.startswith(domain):
                return 'internal'
        
        return 'external'
    
    def _is_external_allowed(self, path):
        """Check if external access is allowed"""
        for allowed in self.EXTERNAL_ALLOWED_PAGES:
            if path.startswith(allowed):
                return True
        return False
    
    def _handle_logout_redirect(self, request, path):
        """Handle logout and redirect to home with generic message"""
        user_email = request.user.email if request.user.is_authenticated else 'Anonymous'
        
        # Generic user-friendly message (security best practice)
        message = 'Your session has been refreshed. Please log in again to continue.'
        
        # Log detailed information for security monitoring (not shown to user)
        logger.warning(
            f"ACCESS BLOCKED - User: {user_email}, "
            f"Path: {path}, IP: {request.META.get('REMOTE_ADDR')}, "
            f"User-Agent: {request.META.get('HTTP_USER_AGENT')}"
        )
        
        # Add generic message BEFORE logout
        messages.info(request, message)
        
        # Logout and clear session
        logout(request)
        request.session.flush()
        
        logger.info(f"Session cleared for user: {user_email}")
        
        # Redirect to home page
        return redirect('/')