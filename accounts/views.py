from django.shortcuts import render

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import re
from django.core.exceptions import ValidationError

@csrf_exempt
@require_POST
def api_login(request):
    """Handle login via API"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        # Validate input
        if not email or not password:
            return JsonResponse({
                'success': False,
                'message': 'Email and password are required.'
            })
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Set session expiration based on remember me
            if not remember_me:
                request.session.set_expiry(0)  # Session expires on browser close
            
            login(request, user)
            return JsonResponse({
                'success': True,
                'message': 'Login successful!',
                'redirect_url': '/'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid email or password.'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.'
        })

@csrf_exempt
@require_POST
def api_register(request):
    """Handle registration via API"""
    try:
        data = json.loads(request.body)
        
        # Extract form data
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        terms_accepted = data.get('terms', False)
        
        # Validation
        errors = {}
        
        # Check required fields
        if not first_name:
            errors['first_name'] = 'First name is required.'
        if not last_name:
            errors['last_name'] = 'Last name is required.'
        if not email:
            errors['email'] = 'Email is required.'
        if not password:
            errors['password'] = 'Password is required.'
        if not confirm_password:
            errors['confirm_password'] = 'Please confirm your password.'
        
        # Validate email format
        if email and '@' not in email:
            errors['email'] = 'Please enter a valid email address.'
        
        # Check if email already exists
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if email and User.objects.filter(email=email).exists():
            errors['email'] = 'This email is already registered.'
        
        # Validate password
        if password:
            if len(password) < 8:
                errors['password'] = 'Password must be at least 8 characters long.'
            elif not re.search(r'[A-Z]', password):
                errors['password'] = 'Password must contain at least one uppercase letter.'
            elif not re.search(r'[a-z]', password):
                errors['password'] = 'Password must contain at least one lowercase letter.'
            elif not re.search(r'\d', password):
                errors['password'] = 'Password must contain at least one number.'
            elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                errors['password'] = 'Password must contain at least one special character.'
        
        # Check password match
        if password and confirm_password and password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'
        
        # Check terms acceptance
        if not terms_accepted:
            errors['terms'] = 'You must agree to the Terms of Service and Privacy Policy.'
        
        # If there are errors, return them
        if errors:
            return JsonResponse({
                'success': False,
                'message': 'Please correct the errors below.',
                'errors': errors
            })
        
        # Create user
        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Log the user in
            login(request, user)
            
            return JsonResponse({
                'success': True,
                'message': 'Registration successful! Welcome to LittleCraftOne.',
                'redirect_url': '/'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error creating account. Please try again.'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid data format.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An unexpected error occurred.'
        })

@login_required
@require_POST
def api_logout(request):
    """Handle logout via API"""
    logout(request)
    return JsonResponse({
        'success': True,
        'message': 'Logged out successfully.',
        'redirect_url': '/'
    })

# Regular view functions for rendering templates
def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'account/login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'account/register.html')

def home(request):
    try:
        return render(request, 'home.html')
    except Exception as e:
        print("Exception caught:", e)
        raise

