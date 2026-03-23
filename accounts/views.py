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
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
# Add this at the top of your views.py or in a separate utils.py
import time
import uuid
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
logger = logging.getLogger(__name__)

# accounts/views.py

def logout_user(request):
    try:
        if request.user.is_authenticated:
            user_email = request.user.email
            
            # Set logout flag BEFORE logout
            request.session['logout_completed'] = True
            request.session['auth_flow_completed'] = False
            
            # Clear expected_next_url
            if 'expected_next_url' in request.session:
                del request.session['expected_next_url']
            
            logger.info(f"User {user_email} logged out. Flags set: logout_completed=True")
        
        logout(request)
        request.session.flush()
        
        messages.success(request, "You have been successfully logged out.")
        return redirect('home')
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        messages.error(request, "Something went wrong.")
        return redirect('home')

# Regular view functions for rendering templates
# accounts/views.py

@sensitive_post_parameters()
@csrf_protect
@never_cache
def login_view(request):
    try:
        # If user is already logged in, redirect based on role
        if request.user.is_authenticated:
            # Check if this is a back/forward navigation attempt
            if request.session.get('logout_completed', False):
                # Clear the logout flag and redirect to home
                if 'logout_completed' in request.session:
                    del request.session['logout_completed']
                messages.warning(request, '🔒 Session expired. Please login again.')
                logout(request)
                request.session.flush()
                return redirect('home')
            
            # Normal redirect for already logged in users
            if hasattr(request.user, 'role_id'):
                if request.user.role_id == 1:
                    return redirect('admin_dashboard')
                elif request.user.role_id == 2:
                    return redirect('dashboard')
            return redirect('/')
        
        if request.method == 'GET':
            next_url = request.GET.get('next')
            # Clear any stale session flags on login page access
            if 'logout_completed' in request.session:
                del request.session['logout_completed']
            if 'auth_flow_completed' in request.session:
                del request.session['auth_flow_completed']
            
            logger.info(f"Login page accessed with next URL: {next_url}")
            return render(request, 'account/login.html', {'next': next_url})
        
        if request.method == 'POST':
            try:
                email = request.POST.get('email', '').strip().lower()
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
                user = authenticate(request, username=email, password=password)
                
                if user is not None:
                    # Check if user is active
                    if not user.is_active:
                        messages.error(request, 'Your account has been deactivated. Please contact support.')
                        return render(request, 'account/login.html', {'email': email})
                    
                    # Store the OLD session key BEFORE login
                    old_session_key = request.session.session_key
                    logger.debug(f"OLD session key before login: {old_session_key}")
                    
                    # ========== CLEAN UP OLD SESSION FLAGS ==========
                    # Clear any existing session flags before login
                    session_keys_to_clear = [
                        'auth_flow_completed', 'logout_completed', 'expected_next_url',
                        'last_visited_url', 'session_validated', 'login_timestamp'
                    ]
                    for key in session_keys_to_clear:
                        if key in request.session:
                            del request.session[key]
                    
                    # Perform login (this will change the session key)
                    login(request, user)
                    
                    # ========== SET NEW SESSION FLAGS FOR AUTH FLOW ==========
                    request.session['auth_flow_completed'] = True
                    request.session['role_id'] = user.role_id
                    request.session['logout_completed'] = False
                    
                    # Set expected next URL based on role
                    if user.role_id == 1:  # Admin
                        request.session['expected_next_url'] = '/admin-dashboard/'
                    elif user.role_id == 2:  # Customer
                        request.session['expected_next_url'] = '/dashboard/'
                    
                    # Clear any previous navigation flags
                    if 'expected_next_url' in request.session:
                        # Already set above
                        pass
                    
                    # ========== SESSION SECURITY SETUP ==========
                    import time
                    import uuid
                    
                    # Set session markers for security tracking
                    request.session['session_created_at'] = time.time()
                    request.session['session_id'] = str(uuid.uuid4())
                    request.session['ip_address'] = request.META.get('REMOTE_ADDR')
                    request.session['user_agent'] = request.META.get('HTTP_USER_AGENT', 'Unknown')[:255]
                    request.session['login_timestamp'] = time.time()
                    request.session['login_email'] = user.email
                    request.session['session_validated'] = True
                    
                    # Handle remember me
                    if not remember_me:
                        # Session expires when browser closes
                        request.session.set_expiry(0)
                        logger.debug(f"Session set to expire on browser close for user: {user.email}")
                    else:
                        # Session expires in 30 days (2,592,000 seconds)
                        request.session.set_expiry(2592000)
                        logger.debug(f"Session set to expire in 30 days for user: {user.email}")
                    
                    # NEW session key after login
                    new_session_key = request.session.session_key
                    logger.debug(f"NEW session key after login: {new_session_key}")
                    
                    # ========== CART MERGE LOGIC ==========
                    if old_session_key:
                        try:
                            from store.views import merge_carts_on_login
                            
                            # Pass the old session key to the merge function
                            result = merge_carts_on_login(request, old_session_key)
                            
                            if result.get('merged', 0) > 0:
                                if result.get('skipped', 0) > 0:
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
                            logger.error(f"Cart merge error: {cart_error}")
                    # ======================================
                    
                    # Success message
                    messages.success(request, f'Welcome back, {user.full_name or user.email}!')
                    
                    # Handle redirect
                    next_url = request.POST.get('next')
                    logger.debug(f"Next URL received in POST: {next_url}")
                    
                    if next_url:
                        return redirect(next_url)
                    
                    if hasattr(user, 'role_id'):
                        if user.role_id == 1:
                            return redirect('admin_dashboard')
                        elif user.role_id == 2:
                            # Check for checkout redirect
                            checkout_redirect = request.session.pop('checkout_after_login', None)
                            if checkout_redirect:
                                return redirect('checkout')
                            return redirect('dashboard')
                    
                    return redirect('/')
                else:
                    # Failed login attempt
                    logger.warning(f"Failed login attempt for email: {email} from IP: {request.META.get('REMOTE_ADDR')}")
                    messages.error(request, 'Invalid email or password.')
                    return render(request, 'account/login.html', {'email': email})
                    
            except Exception as post_error:
                logger.error(f"Login POST error: {post_error}")
                messages.error(request, 'An error occurred. Please try again.')
                return render(request, 'account/login.html')
                
    except Exception as e:
        logger.error(f"Login view unexpected error: {e}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return render(request, 'account/login.html')

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

def send_order_confirmation_email(order, order_items, encrypted_order_id):
    """Send order confirmation email to customer with HTML template"""
    try:
        subject = f'Order Confirmation - #{order.order_number}'
        
        # Get the domain (you should set this in settings.py)
        domain = settings.SITE_URL  # e.g., 'https://www.littlecraftone.com'
        
        # Render HTML template
        html_content = render_to_string('emails/order_confirmation.html', {
            'order': order,
            'order_items': order_items,
            'encrypted_order_id': encrypted_order_id,
            'domain': domain,
            'year': timezone.now().year,
        })
        
        # Create plain text version from HTML
        text_content = strip_tags(html_content)
        
        # Create email with both HTML and plain text versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,  # plain text version
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send(fail_silently=False)
        
        logger.info(f"Order confirmation email sent for order #{order.order_number}")
        
    except Exception as e:
        logger.warning(f"Failed to send confirmation email for order #{order.order_number}: {e}")