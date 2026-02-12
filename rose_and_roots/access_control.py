from django.shortcuts import redirect
from functools import wraps
from django.contrib import messages
from django.contrib.auth import logout
from accounts.views import *  # Avoid circular imports

def no_direct_access(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # First check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, "Please login to access this page.")
            return redirect('login')
        
        # Then check for direct access (no referer or external referer)
        referer = request.META.get('HTTP_REFERER')
        current_host = request.get_host()
        
        # If no referer OR referer doesn't contain current host - it's direct access
        if not referer or current_host not in referer:
            messages.warning(request, "Direct access is not allowed. Please use the navigation menu.")
            
            # Logout the user and clear session
            logout(request)
            request.session.flush()  # Clear the session completely
            
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

# from django.shortcuts import redirect
# from functools import wraps
# from django.contrib import messages
# from accounts.views import *

# def no_direct_access(view_func):
#     @wraps(view_func)
#     def _wrapped_view(request, *args, **kwargs):
#         referer = request.META.get('HTTP_REFERER')
#         current_host = request.get_host()

#         if not referer or current_host not in referer:

#             messages.warning(
#                 request,
#                 "Your session could not be verified."
#             )

#             return logout(request)

#         return view_func(request, *args, **kwargs)

#     return _wrapped_view
