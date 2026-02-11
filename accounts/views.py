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
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.shortcuts import render, redirect
from accounts.models import *
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect, render

from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.shortcuts import redirect

def logout(request):
    try:
        auth_logout(request)  # correct logout

        messages.success(request, "You have been successfully logged out.")

        return redirect('home')

    except Exception as e:
        print(f"Logout error: {e}")
        messages.error(request, "Something went wrong. Please try again later.")
        return redirect('home')

# Regular view functions for rendering templates

def login_view(request):
    try:
        if request.user.is_authenticated:
            return redirect('/')
        
        if request.method == 'GET':
            return render(request, 'account/login.html')
        
        if request.method == 'POST':
            try:
                email = request.POST.get('email', '').strip()
                password = request.POST.get('password', '')
                remember_me = request.POST.get('remember_me')
                
                # Validation
                if not email:
                    messages.error(request, 'Email is required.')
                    return render(request, 'account/login.html', {'email': email})
                
                if not password:
                    messages.error(request, 'Password is required.')
                    return render(request, 'account/login.html', {'email': email})
                
                # Authenticate user
                try:
                    user = authenticate(request, username=email, password=password)
                except Exception as auth_error:
                    print(f"Authentication error: {auth_error}")
                    messages.error(request, 'Authentication service error. Please try again.')
                    return render(request, 'account/login.html', {'email': email})
                
                if user is not None:
                    try:
                        login(request, user)
                        
                        # Handle remember me
                        if not remember_me:
                            request.session.set_expiry(0)  # Session expires when browser closes
                        else:
                            request.session.set_expiry(1209600)  # 2 weeks (default)
                        
                        messages.success(request, f'Welcome back, {user.full_name or user.email}!')
                        
                        # Redirect to next page if exists
                        return redirect('admin_dashboard')
                    except Exception as login_error:
                        print(f"Login error: {login_error}")
                        messages.error(request, 'Login failed. Please try again.')
                        return render(request, 'account/login.html', {'email': email})
                else:
                    messages.error(request, 'Invalid email or password.')
                    return render(request, 'account/login.html', {'email': email})
                    
            except Exception as post_error:
                print(f"Login POST error: {post_error}")
                messages.error(request, 'An error occurred. Please try again.')
                return render(request, 'account/login.html')
                
    except Exception as e:
        print(f"Login view unexpected error: {e}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return render(request, 'account/login.html')

def register_view(request):
    try:
        if request.user.is_authenticated:
            return redirect('/')
        
        if request.method == 'GET':
            return render(request, 'account/register.html')
        
        if request.method == 'POST':
            try:
                # Get form data with defaults
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                email = request.POST.get('email', '').strip().lower()
                phone = request.POST.get('phone', '').strip()  # Added phone field
                password = request.POST.get('password', '')
                confirm_password = request.POST.get('confirm_password', '')
                terms = request.POST.get('terms')
                
                # Validation
                errors = {}
                
                if not first_name:
                    errors['first_name'] = 'First name is required.'
                
                if not last_name:
                    errors['last_name'] = 'Last name is required.'
                
                if not email:
                    errors['email'] = 'Email is required.'
                else:
                    try:
                        if CustomUser.objects.filter(email=email).exists():
                            errors['email'] = 'This email is already registered.'
                    except Exception as db_error:
                        print(f"Database error checking email: {db_error}")
                        errors['email'] = 'Unable to verify email. Please try again.'
                
                # Phone validation (optional but if provided, validate format)
                if phone:
                    # Basic phone validation - adjust regex as per your requirements
                    import re
                    phone_regex = r'^\+?1?\d{9,15}$'  # Simple international format
                    if not re.match(phone_regex, phone):
                        errors['phone'] = 'Please enter a valid phone number.'
                
                if not password:
                    errors['password'] = 'Password is required.'
                elif len(password) < 8:
                    errors['password'] = 'Password must be at least 8 characters long.'
                elif not any(char.isupper() for char in password):
                    errors['password'] = 'Password must contain at least one uppercase letter.'
                elif not any(char.islower() for char in password):
                    errors['password'] = 'Password must contain at least one lowercase letter.'
                elif not any(char.isdigit() for char in password):
                    errors['password'] = 'Password must contain at least one number.'
                elif not any(char in '!@#$%^&*(),.?":{}|<>' for char in password):
                    errors['password'] = 'Password must contain at least one special character.'
                
                if password != confirm_password:
                    errors['confirm_password'] = 'Passwords do not match.'
                
                if not terms:
                    errors['terms'] = 'You must agree to the terms and conditions.'
                
                if errors:
                    # Store errors in messages
                    for field, error in errors.items():
                        messages.error(request, error)
                    
                    # Pass form data back to template
                    context = {
                        'form_data': request.POST,
                        'errors': errors
                    }
                    return render(request, 'account/register.html', context)
                
                # Create user
                try:
                    user = CustomUser.objects.create_user(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,  # Added phone field
                        full_name=f"{first_name} {last_name}".strip(),
                        user_type='guest'
                    )
                    
                    # Store password in password_storage table
                    try:
                        PasswordStorage.objects.create(
                            user=user,
                            password_text=password  # Note: This stores plain text password - consider encryption
                        )
                    except Exception as password_storage_error:
                        print(f"Password storage error: {password_storage_error}")
                        # Don't fail registration if password storage fails, just log it
                    
                except Exception as create_error:
                    print(f"User creation error: {create_error}")
                    messages.error(request, 'Failed to create account. Please try again.')
                    return render(request, 'account/register.html', {'form_data': request.POST})
                
                # Log the user in immediately after registration
                try:
                    login(request, user)
                    messages.success(request, 'Registration successful! Welcome to LittleCraftOne.')
                    return redirect('admin_dashboard')
                except Exception as login_error:
                    print(f"Auto-login error: {login_error}")
                    messages.success(request, 'Registration successful! Please login to continue.')
                    return redirect('login')
                    
            except Exception as post_error:
                print(f"Register POST error: {post_error}")
                messages.error(request, 'An error occurred during registration. Please try again.')
                return render(request, 'account/register.html', {'form_data': request.POST})
                
    except Exception as e:
        print(f"Register view unexpected error: {e}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return render(request, 'account/register.html')

def home(request):
    try:
        return render(request, 'home.html')
    except Exception as e:
        print("Exception caught:", e)
        raise

