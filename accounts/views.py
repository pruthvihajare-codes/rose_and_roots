from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
import json
import re
from accounts.models import *
from django.contrib.auth import logout as auth_logout
from store.models import *
from django.conf import settings

def logout_user(request):
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
            if hasattr(request.user, 'role_id'):
                if request.user.role_id == 1:
                    return redirect('admin_dashboard')
                elif request.user.role_id == 2:
                    return redirect('dashboard')
            return redirect('/')
        
        if request.method == 'GET':
            next_url = request.GET.get('next')
            print(f"Next URL received in GET: {next_url}")
            return render(request, 'account/login.html', {'next': next_url})
        
        if request.method == 'POST':
            try:
                email = request.POST.get('email', '').strip()
                password = request.POST.get('password', '')
                remember_me = request.POST.get('remember_me')
                
                if not email:
                    messages.error(request, 'Email is required.')
                    return render(request, 'account/login.html', {'email': email})
                
                if not password:
                    messages.error(request, 'Password is required.')
                    return render(request, 'account/login.html', {'email': email})
                
                # Authenticate user
                user = authenticate(request, username=email, password=password)
                
                if user is not None:
                    # CRITICAL: Store the OLD session key BEFORE login
                    old_session_key = request.session.session_key
                    print(f"OLD session key before login: {old_session_key}")  # Debug
                    
                    # Perform login (this will change the session key)
                    login(request, user)
                    
                    # Handle remember me
                    if not remember_me:
                        request.session.set_expiry(0)
                    else:
                        request.session.set_expiry(1209600)
                    
                    # NEW session key after login
                    new_session_key = request.session.session_key
                    print(f"NEW session key after login: {new_session_key}")  # Debug
                    
                    # ---------- CART MERGE LOGIC ----------
                    if old_session_key:
                        try:
                            from store.views import merge_carts_on_login
                            
                            # Pass the old session key to the merge function
                            result = merge_carts_on_login(request, old_session_key)
                            
                            if result['merged'] > 0:
                                if result['skipped'] > 0:
                                    messages.warning(
                                        request, 
                                        f'Welcome back! We merged {result["merged"]} item(s) from your guest cart. '
                                        f'{result["skipped"]} item(s) were skipped due to cart limit.'
                                    )
                                else:
                                    messages.success(
                                        request, 
                                        f'Welcome back! We merged {result["merged"]} item(s) from your guest cart.'
                                    )
                        except Exception as cart_error:
                            print(f"Cart merge error: {cart_error}")
                    # --------------------------------------
                    
                    messages.success(request, f'Welcome back, {user.full_name or user.email}!')
                    
                    next_url = request.POST.get('next')
                    print(f"Next URL received in POST: {next_url}")

                    if next_url:
                        return redirect(next_url)
                    
                    if hasattr(user, 'role_id'):
                        if user.role_id == 1:
                            return redirect('admin_dashboard')
                        elif user.role_id == 2:
                            checkout_redirect = request.session.pop('checkout_after_login', None)
                            if checkout_redirect:
                                return redirect('checkout')
                            return redirect('dashboard')
                    
                    return redirect('/')
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
    
# In your cart/views.py, update the merge function to handle imports properly

def merge_carts_on_login(request):
    """
    Called after login to merge guest cart with user cart
    This should be called from your login view after successful authentication
    """
    if not request.user.is_authenticated:
        return {'merged': 0, 'skipped': 0, 'total': 0}
    
    # Check if there's a guest cart
    if not request.session.session_key:
        return {'merged': 0, 'skipped': 0, 'total': 0}
    
    try:
        from .models import Cart, CartItem
        from masters.models import Bouquet
        from rose_and_roots.encryption import enc
        
        guest_cart = Cart.objects.filter(session_key=request.session.session_key).first()
        if not guest_cart:
            return {'merged': 0, 'skipped': 0, 'total': 0}
        
        # Check if guest cart has items
        guest_item_count = CartItem.objects.filter(cart=guest_cart).count()
        if guest_item_count == 0:
            # Delete empty guest cart
            guest_cart.delete()
            return {'merged': 0, 'skipped': 0, 'total': 0}
        
        # Get or create user cart
        user_cart, created = Cart.objects.get_or_create(
            user=request.user,
            defaults={'session_key': None}
        )
        
        # Get current user cart item count
        user_item_count = CartItem.objects.filter(cart=user_cart).count()
        
        # Get all guest items
        guest_items = CartItem.objects.filter(cart=guest_cart).select_related('bouquet')
        
        merged_count = 0
        skipped_count = 0
        
        from django.db import transaction
        
        with transaction.atomic():
            for guest_item in guest_items:
                # Check if user cart already has this bouquet
                if not CartItem.objects.filter(cart=user_cart, bouquet=guest_item.bouquet).exists():
                    # Check if adding would exceed limit
                    if user_item_count + merged_count >= 10:
                        skipped_count += 1
                        continue
                    
                    # Create new item in user cart
                    CartItem.objects.create(
                        cart=user_cart,
                        bouquet=guest_item.bouquet,
                        encrypted_id=guest_item.encrypted_id or enc(str(guest_item.bouquet.id)),
                        price_at_add=guest_item.price_at_add
                    )
                    merged_count += 1
            
            # Delete guest cart and its items
            guest_cart.delete()
        
        # Get final count
        final_count = CartItem.objects.filter(cart=user_cart).count()
        
        return {
            'merged': merged_count,
            'skipped': skipped_count,
            'total': final_count
        }
        
    except ImportError as e:
        print(f"Cart models not available: {e}")
        return {'merged': 0, 'skipped': 0, 'total': 0}
    except Exception as e:
        print(f"Error in cart merge: {e}")
        return {'merged': 0, 'skipped': 0, 'total': 0}
    
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
                phone = request.POST.get('phone', '').strip()
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
                    import re
                    phone_regex = r'^\+?1?\d{9,15}$'
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
                    for field, error in errors.items():
                        messages.error(request, error)
                    
                    context = {
                        'form_data': request.POST,
                        'errors': errors
                    }
                    return render(request, 'account/register.html', context)
                
                # Create user
                try:
                    from django.db import transaction
                    
                    with transaction.atomic():
                        user = CustomUser.objects.create_user(
                            email=email,
                            password=password,
                            first_name=first_name,
                            last_name=last_name,
                            phone=phone,
                            full_name=f"{first_name} {last_name}".strip(),
                            role_id=2,
                            user_type='customer',
                        )
                        
                        # Create user profile automatically
                        UserProfile.objects.create(
                            user=user,
                            # You can set default values here if needed
                        )
                        
                        # Store password in password_storage table
                        try:
                            PasswordStorage.objects.create(
                                user=user,
                                password_text=password
                            )
                        except Exception as password_storage_error:
                            print(f"Password storage error: {password_storage_error}")
                    
                except Exception as create_error:
                    print(f"User creation error: {create_error}")
                    messages.error(request, 'Failed to create account. Please try again.')
                    return render(request, 'account/register.html', {'form_data': request.POST})
                
                # Log the user in immediately after registration
                try:
                    login(request, user)
                    messages.success(request, 'Registration successful! Welcome to LittleCraftOne.')
                    return redirect('dashboard')
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

