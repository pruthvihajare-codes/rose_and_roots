# store/middleware_navigation.py
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.utils.deprecation import MiddlewareMixin
import logging
import time

logger = logging.getLogger(__name__)

class BrowserNavigationMiddleware(MiddlewareMixin):
    """
    Prevents authenticated users from accessing protected pages through 
    browser back/forward buttons after logout or session expiration.
    """
    
    PROTECTED_PAGES = [
        '/dashboard/', '/profile/', '/checkout/', '/order-confirmation/',
        '/shop/', '/cart_view', '/bouquets/', '/vendors/', '/occasions/',
        '/users/', '/admin-dashboard/', '/cart/', '/place-order/',
    ]
    
    PUBLIC_PAGES = [
        '/login/', '/register/', '/logout/', 
        '/static/', '/media/', '/admin/',
        '/',  # Home page
        '/check-session/',
    ]
    
    def process_request(self, request):
        current_path = request.path
        
        # ALWAYS allow access to login and register pages
        if current_path in ['/login/', '/register/'] or current_path.startswith('/login') or current_path.startswith('/register'):
            return None
        
        # Skip if user is not authenticated
        if not request.user.is_authenticated:
            return None
            
        # Skip public pages
        if self._is_public_path(current_path):
            return None
        
        # Check if current path is protected
        if self._is_protected_path(current_path):
            # Check if this is a back/forward navigation
            if self._is_browser_navigation(request):
                # Log detailed info for security (not shown to user)
                logger.warning(
                    f"BACK/FORWARD NAVIGATION DETECTED - User: {request.user.email}, "
                    f"Path: {current_path}, IP: {request.META.get('REMOTE_ADDR')}, "
                    f"Referer: {request.META.get('HTTP_REFERER')}"
                )
                
                # Add session flags
                request.session['logout_completed'] = True
                
                # Generic message (security best practice)
                messages.info(request, 'Your session has been refreshed. Please log in again to continue.')
                
                # Clear session and logout
                logout(request)
                request.session.flush()
                
                return redirect('/')
        
        return None
    
    def _is_protected_path(self, path):
        """Check if the path requires protection"""
        for protected in self.PROTECTED_PAGES:
            if path.startswith(protected):
                return True
        return False
    
    def _is_public_path(self, path):
        """Check if path is public"""
        for public_page in self.PUBLIC_PAGES:
            if path.startswith(public_page):
                return True
        return False
    
    def _is_browser_navigation(self, request):
        """Detect browser back/forward button navigation."""
        http_referer = request.META.get('HTTP_REFERER', '')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Don't block AJAX requests
        if is_ajax:
            return False
        
        # If no referer, it could be direct access or bookmark
        if not http_referer:
            return True
        
        # Check for browser cache indicators
        cache_control = request.META.get('HTTP_CACHE_CONTROL', '')
        pragma = request.META.get('HTTP_PRAGMA', '')
        
        if 'max-age=0' in cache_control or 'no-cache' in cache_control or pragma == 'no-cache':
            return True
        
        current_full_url = request.build_absolute_uri()
        
        # If referer is exactly the same as current URL, it's likely a refresh
        if http_referer == current_full_url:
            return False
        
        # Check if the request is coming from a different domain
        try:
            from urllib.parse import urlparse
            referer_domain = urlparse(http_referer).netloc
            current_domain = urlparse(current_full_url).netloc
            
            if referer_domain and referer_domain != current_domain:
                return True
        except:
            pass
        
        return False


class SessionValidationMiddleware(MiddlewareMixin):
    """
    Validates session integrity on browser navigation.
    """
    
    def process_response(self, request, response):
        # Add headers to prevent caching of authenticated pages
        if request.user.is_authenticated:
            # Prevent browser from caching authenticated pages
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            # Add session validation headers
            if hasattr(request, 'session'):
                response['X-Session-Valid'] = str(request.session.get('_auth_user_id', ''))
        
        return response
    
    def process_request(self, request):
        current_path = request.path
        
        # ALWAYS allow access to login and register pages
        if current_path in ['/login/', '/register/'] or current_path.startswith('/login') or current_path.startswith('/register'):
            return None
        
        # ALWAYS allow session check endpoint
        if current_path == '/check-session/':
            return None
        
        # Skip for public pages
        public_pages = ['/static/', '/media/', '/admin/']
        if any(current_path.startswith(page) for page in public_pages):
            return None
        
        # For authenticated users, validate session consistency
        if request.user.is_authenticated:
            # Check if logout was completed
            logout_completed = request.session.get('logout_completed', False)
            if logout_completed:
                logger.warning(f"Session marked as logged out for {request.user.email}")
                messages.info(request, 'Your session has been refreshed. Please log in again to continue.')
                logout(request)
                request.session.flush()
                return redirect('/')
            
            # Check session age
            session_created = request.session.get('session_created_at')
            if session_created:
                current_time = time.time()
                # Session older than 30 minutes?
                if current_time - session_created > 1800:  # 30 minutes
                    logger.info(f"Session expired for {request.user.email}")
                    messages.info(request, 'Your session has expired. Please log in again to continue.')
                    logout(request)
                    request.session.flush()
                    return redirect('/')
            
            # Check for session validation header from client
            session_valid_header = request.META.get('HTTP_X_SESSION_VALID', '')
            current_user_id = str(request.session.get('_auth_user_id', ''))
            
            if session_valid_header and current_user_id and session_valid_header != current_user_id:
                logger.warning(f"Session validation mismatch for {request.user.email}")
                messages.info(request, 'Your session has been refreshed. Please log in again to continue.')
                logout(request)
                request.session.flush()
                return redirect('/')
        
        return None


class CacheControlMiddleware(MiddlewareMixin):
    """
    Adds cache control headers to prevent back/forward button issues.
    """
    
    def process_response(self, request, response):
        # Don't add cache headers for static/media files and login pages
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return response
        
        # Don't add cache headers for login/register pages
        if request.path in ['/login/', '/register/'] or request.path.startswith('/login') or request.path.startswith('/register'):
            return response
        
        # For all other responses, add no-cache headers
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response