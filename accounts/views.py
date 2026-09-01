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
import time
import uuid
import logging
from django.core.mail import EmailMultiAlternatives
from rose_and_roots.encryption import enc, dec
from accounts.utils.rate_limiter import email_otp_limiter, otp_verify_limiter, resend_otp_limiter
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
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
            # Clear OTP session data on GET
            if 'verified_email' in request.session:
                del request.session['verified_email']
            if 'otp_verified' in request.session:
                del request.session['otp_verified']
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
                
                # ========== CHECK OTP VERIFICATION ==========
                # Verify that OTP was verified
                if not request.session.get('otp_verified', False):
                    messages.error(request, 'Please verify your email with OTP first.')
                    return render(request, 'account/register.html', {'form_data': request.POST})
                
                # Verify that the email matches
                verified_email = request.session.get('verified_email', '')
                if verified_email != email:
                    messages.error(request, 'Email mismatch. Please verify your email again.')
                    return render(request, 'account/register.html', {'form_data': request.POST})
                
                # Check if OTP verification was recent (within 15 minutes)
                from datetime import datetime, timedelta
                verified_at_str = request.session.get('otp_verified_at')
                if verified_at_str:
                    verified_at = datetime.fromisoformat(verified_at_str)
                    if timezone.now() - verified_at > timedelta(minutes=15):
                        messages.error(request, 'OTP verification expired. Please verify again.')
                        if 'otp_verified' in request.session:
                            del request.session['otp_verified']
                        return render(request, 'account/register.html', {'form_data': request.POST})
                # ==========================================
                
                # Validation
                errors = {}
                
                if not first_name:
                    errors['first_name'] = 'First name is required.'
                
                if not last_name:
                    errors['last_name'] = 'Last name is required.'
                
                if not email:
                    errors['email'] = 'Email is required.'
                else:
                    if CustomUser.objects.filter(email=email).exists():
                        errors['email'] = 'This email is already registered.'
                
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
                            full_name=f"{first_name} {last_name}".strip(),
                            role_id=2,
                            user_type='guest',
                            email_verified=True,  # Since we verified via OTP
                        )
                        
                        # Create user profile
                        UserProfile.objects.create(
                            user=user,
                        )
                        
                        # Store password
                        PasswordStorage.objects.create(
                            user=user,
                            password_text=password
                        )
                        
                        # ========== CLEAN UP OTP ==========
                        # Delete all OTPs for this email
                        EmailOTP.objects.filter(email=email).delete()
                        
                        # Clear session data
                        if 'verified_email' in request.session:
                            del request.session['verified_email']
                        if 'otp_verified' in request.session:
                            del request.session['otp_verified']
                        if 'otp_verified_at' in request.session:
                            del request.session['otp_verified_at']
                        # ===================================
                    
                except Exception as create_error:
                    logger.error(f"User creation error: {create_error}")
                    messages.error(request, 'Failed to create account. Please try again.')
                    return render(request, 'account/register.html', {'form_data': request.POST})
                
                # Log the user in
                try:
                    login(request, user)
                    messages.success(request, 'Registration successful! Welcome to LittleCraftOne.')
                    return redirect('dashboard')
                except Exception as login_error:
                    logger.error(f"Auto-login error: {login_error}")
                    messages.success(request, 'Registration successful! Please login to continue.')
                    return redirect('login')
                    
            except Exception as post_error:
                logger.error(f"Register POST error: {post_error}")
                messages.error(request, 'An error occurred during registration. Please try again.')
                return render(request, 'account/register.html', {'form_data': request.POST})
               
    except Exception as e:
        print(f"Register view unexpected error: {e}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return render(request, 'account/register.html')

def home(request):
    """Homepage view"""
    try:
        # Get featured bouquets
        featured_bouquets = Bouquet.objects.filter(
            is_active=1, 
            is_featured=1
        ).prefetch_related('images', 'occasions')[:8]
        
        # Add encrypted IDs and primary images
        bouquet_list = []
        for bouquet in featured_bouquets:
            bouquet.encrypted_id = enc(str(bouquet.id))
            primary_image = bouquet.images.filter(is_active=1).first()
            bouquet.primary_image = primary_image.image_path if primary_image else None
            bouquet.occasion_names = [occ.name for occ in bouquet.occasions.all()]
            bouquet.category_name = bouquet.category.parameter_value if bouquet.category else 'Uncategorized'
            bouquet_list.append(bouquet)
        
        # Get categories with counts
        categories = parameter_master.objects.filter(
            parameter_name='Product Categories',
            isactive=1
        ).order_by('parameter_value')
        
        category_list = []
        for category in categories:
            category.encrypted_id = enc(str(category.parameter_id))
            category.bouquet_count = Bouquet.objects.filter(
                category_id=category.parameter_id, 
                is_active=1
            ).count()
            category_list.append(category)
        
        # Get occasions
        occasions = Occasion.objects.filter(is_active=1).order_by('name')
        occasion_list = []
        for occasion in occasions:
            occasion.encrypted_id = enc(str(occasion.id))
            occasion_list.append(occasion)
        
        # Get admin WhatsApp
        admin_user = CustomUser.objects.filter(role_id=1, is_active=True).first()
        admin_whatsapp = admin_user.phone if admin_user else '918805433102'
        
        context = {
            'bouquets': bouquet_list,
            'categories': category_list,
            'occasions': occasion_list,
            'admin_whatsapp': admin_whatsapp,
            'MEDIA_URL': settings.MEDIA_URL,
        }
        
        return render(request, 'home.html', context)
        
    except Exception as e:
        logger.exception(f"Error in home view: {str(e)}")
        # Fallback context
        return render(request, 'home.html', {
            'bouquets': [],
            'categories': [],
            'occasions': [],
            'admin_whatsapp': '918805433102',
            'MEDIA_URL': settings.MEDIA_URL,
        })

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

@csrf_exempt
@require_POST
def send_otp_view(request):
    """Send OTP to email"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        
        # Validate email
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email is required'
            }, status=400)
        
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address'
            }, status=400)
        
        # Check if email is already registered
        if CustomUser.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': 'This email is already registered'
            }, status=400)
        
        # Rate limiting
        if not email_otp_limiter.is_allowed(email):
            remaining_time = email_otp_limiter.get_time_remaining(email)
            return JsonResponse({
                'success': False,
                'message': f'Too many attempts. Please wait {remaining_time} seconds and try again.',
                'rate_limited': True,
                'time_remaining': remaining_time
            }, status=429)
        
        # Create OTP
        otp = EmailOTP.create_otp(email)
        
        # Send OTP email
        email_sent = send_otp_email(email, otp.otp_code)
        
        if not email_sent:
            return JsonResponse({
                'success': False,
                'message': 'Failed to send OTP. Please try again.'
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'message': 'OTP sent successfully to your email',
            'email': email,
            'expires_in': 600,  # 10 minutes in seconds
            'remaining_attempts': email_otp_limiter.get_remaining_attempts(email)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request format'
        }, status=400)
    except Exception as e:
        logger.error(f"Send OTP error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }, status=500)

@csrf_exempt
@require_POST
def verify_otp_view(request):
    """Verify OTP"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        otp_code = data.get('otp', '').strip()
        
        if not email or not otp_code:
            return JsonResponse({
                'success': False,
                'message': 'Email and OTP are required'
            }, status=400)
        
        # Rate limiting for verification attempts
        if not otp_verify_limiter.is_allowed(email):
            return JsonResponse({
                'success': False,
                'message': 'Too many verification attempts. Please try again later.',
                'rate_limited': True
            }, status=429)
        
        # Find OTP record
        try:
            otp = EmailOTP.objects.filter(
                email=email,
                is_verified=False
            ).latest('created_at')
        except EmailOTP.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'No OTP found for this email. Please request a new one.'
            }, status=404)
        
        # Check if expired
        if otp.is_expired():
            otp.delete()  # Clean up expired OTP
            return JsonResponse({
                'success': False,
                'message': 'OTP has expired. Please request a new one.'
            }, status=400)
        
        # Check attempts
        if not otp.can_attempt():
            otp.delete()  # Delete after max attempts
            return JsonResponse({
                'success': False,
                'message': 'Maximum attempts exceeded. Please request a new OTP.'
            }, status=400)
        
        # Verify OTP
        if otp.otp_code != otp_code:
            otp.increment_attempt()
            remaining = otp.max_attempts - otp.attempt_count
            return JsonResponse({
                'success': False,
                'message': f'Invalid OTP. {remaining} attempts remaining.',
                'remaining_attempts': remaining
            }, status=400)
        
        # OTP is correct - mark as verified
        otp.is_verified = True
        otp.save()
        
        # Store email in session for registration
        request.session['verified_email'] = email
        request.session['otp_verified'] = True
        request.session['otp_verified_at'] = str(timezone.now())
        
        # Clean up rate limiters
        email_otp_limiter.reset(email)
        otp_verify_limiter.reset(email)
        
        return JsonResponse({
            'success': True,
            'message': 'OTP verified successfully!',
            'email': email
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request format'
        }, status=400)
    except Exception as e:
        logger.error(f"Verify OTP error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }, status=500)

@csrf_exempt
@require_POST
def resend_otp_view(request):
    """Resend OTP"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email is required'
            }, status=400)
        
        # Rate limiting for resend
        if not resend_otp_limiter.is_allowed(email):
            return JsonResponse({
                'success': False,
                'message': 'Please wait before requesting another OTP',
                'rate_limited': True
            }, status=429)
        
        # Check if email is already registered
        if CustomUser.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': 'This email is already registered'
            }, status=400)
        
        # Create new OTP
        otp = EmailOTP.create_otp(email)
        
        # Send OTP email
        email_sent = send_otp_email(email, otp.otp_code)
        
        if not email_sent:
            return JsonResponse({
                'success': False,
                'message': 'Failed to send OTP. Please try again.'
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'message': 'New OTP sent successfully',
            'expires_in': 600
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request format'
        }, status=400)
    except Exception as e:
        logger.error(f"Resend OTP error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }, status=500)       
        
# send OTP email function
def send_otp_email(email, otp_code):
    """Send OTP via email"""
    try:
        subject = 'Verify Your Email - LittleCraftOne'
        
        # Render HTML template
        html_content = render_to_string('emails/otp_email.html', {
            'otp_code': otp_code,
            'email': email,
            'year': timezone.now().year,
            'site_name': 'LittleCraftOne',
        })
        
        # Create plain text version
        text_content = f"""
        Dear User,
        
        Thank you for registering with LittleCraftOne!
        
        Your OTP for email verification is: {otp_code}
        
        This OTP is valid for 10 minutes.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        LittleCraftOne Team
        """
        
        # Create email
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        
        # Attach HTML version
        email_message.attach_alternative(html_content, "text/html")
        
        # Send email
        email_message.send(fail_silently=False)
        
        logger.info(f"OTP email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {e}")
        return False