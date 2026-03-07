import uuid
import os
import json
import logging
from decimal import Decimal, InvalidOperation
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, DatabaseError
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from django.http import HttpResponse
from rose_and_roots.access_control import no_direct_access
from accounts.models import *
from masters.models import *
from rose_and_roots.encryption import *
from rose_and_roots.settings import MEDIA_URL
from django.shortcuts import render
from django.db.models import Q, Avg, Min, Max
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import F
from store.models import *

logger = logging.getLogger(__name__)

def shop_view(request):
    try:
        """
        Display all bouquets with filtering by occasion and price range
        """
        # Get filter parameters
        selected_occasions_encrypted = request.GET.getlist('occasion')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        sort_by = request.GET.get('sort', 'popular')
        
        # Decrypt occasion IDs
        selected_occasions = []
        for enc_id in selected_occasions_encrypted:
            try:
                dec_id = dec(str(enc_id))
                selected_occasions.append(int(dec_id))
            except:
                pass
        
        # Base queryset - only active bouquets
        bouquets = Bouquet.objects.filter(is_active=1).prefetch_related('occasions', 'images')
        
        # Get featured bouquets for homepage or sidebar
        featured_bouquets = Bouquet.objects.filter(is_active=1, is_featured=1).prefetch_related('images')[:4]
        
        # Filter by occasions
        if selected_occasions:
            bouquets = bouquets.filter(occasions__id__in=selected_occasions).distinct()
        
        # Filter by price range
        if min_price and max_price:
            bouquets = bouquets.filter(
                Q(price__gte=min_price) | Q(discount_price__gte=min_price),
                Q(price__lte=max_price) | Q(discount_price__lte=max_price)
            ).distinct()
        elif min_price:
            bouquets = bouquets.filter(
                Q(price__gte=min_price) | Q(discount_price__gte=min_price)
            ).distinct()
        elif max_price:
            bouquets = bouquets.filter(
                Q(price__lte=max_price) | Q(discount_price__lte=max_price)
            ).distinct()
        
        # Sorting
        if sort_by == 'price_low':
            bouquets = bouquets.order_by('price')
        elif sort_by == 'price_high':
            bouquets = bouquets.order_by('-price')
        elif sort_by == 'newest':
            bouquets = bouquets.order_by('-created_at')
        elif sort_by == 'popular':
            bouquets = bouquets.order_by('-is_featured', '-created_at')
        else:
            bouquets = bouquets.order_by('-is_featured', '-created_at')
        
        # Get price range for filter
        price_range = Bouquet.objects.filter(is_active=1).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        
        # Ensure min_price and max_price are set correctly
        min_price_value = min_price if min_price else price_range['min_price']
        max_price_value = max_price if max_price else price_range['max_price']
        
        # Make sure min is less than max
        if min_price_value and max_price_value and float(min_price_value) > float(max_price_value):
            # Swap if they're reversed
            min_price_value, max_price_value = max_price_value, min_price_value
        
        # Get all occasions for filter with encrypted IDs
        occasions = Occasion.objects.filter(is_active=1).order_by('name')
        occasion_list = []
        for occasion in occasions:
            occasion.encrypted_id = enc(str(occasion.id))
            occasion_list.append(occasion)
        
        # Add encrypted ID and primary image to each bouquet
        bouquet_list = []
        for bouquet in bouquets:
            # Add encrypted ID
            bouquet.encrypted_id = enc(str(bouquet.id))
            
            # Get primary image (first active image)
            primary_image = bouquet.images.filter(is_active=1).first()
            if primary_image:
                bouquet.primary_image = primary_image.image_path
            else:
                bouquet.primary_image = None
            
            # Get all images for gallery
            bouquet.all_images = bouquet.images.filter(is_active=1)
            
            # Get occasion names for display
            bouquet.occasion_names = [occ.name for occ in bouquet.occasions.all()]
            
            bouquet_list.append(bouquet)
        
        # Add images to featured bouquets
        featured_list = []
        for bouquet in featured_bouquets:
            bouquet.encrypted_id = enc(str(bouquet.id))
            primary_image = bouquet.images.filter(is_active=1).first()
            bouquet.primary_image = primary_image.image_path if primary_image else None
            featured_list.append(bouquet)
        
        # Pagination
        paginator = Paginator(bouquet_list, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Encrypt selected occasions for template
        selected_occasions_encrypted_list = [enc(str(id)) for id in selected_occasions]
        
        context = {
            'page_obj': page_obj,
            'bouquets': page_obj.object_list,
            'featured_bouquets': featured_list,
            'occasions': occasion_list,
            'price_range': price_range,
            'selected_occasions': selected_occasions_encrypted_list,
            'min_price': min_price,
            'max_price': max_price,
            'sort_by': sort_by,
            "MEDIA_URL": settings.MEDIA_URL,
            'min_price': min_price_value,
            'max_price': max_price_value,
        }
        
        return render(request, 'store/shop.html', context)
    except Exception as e:
        logger.exception(f"Error in shop_view: {str(e)}")
        messages.error(request, "An error occurred while loading the shop. Please try again later.")
        return redirect('home')
    
# views.py - Add product detail view

def product_detail(request):
    """
    Display single product details with reviews
    """
    encrypted_id = request.GET.get('id')
    
    if not encrypted_id:
        messages.error(request, 'Product ID is required.')
        return redirect('shop')
    
    try:
        # Decrypt the ID
        bouquet_id = dec(str(encrypted_id))
        
        # Get bouquet with related data
        bouquet = Bouquet.objects.filter(
            id=bouquet_id, 
            is_active=1
        ).prefetch_related('occasions', 'images', 'reviews').first()
        
        if not bouquet:
            messages.error(request, 'Product not found.')
            return redirect('shop')
        
        # Get all images
        images = bouquet.images.filter(is_active=1).order_by('id')
        
        # Get related products (same occasions)
        occasion_ids = bouquet.occasions.values_list('id', flat=True)
        related_bouquets = Bouquet.objects.filter(
            is_active=1,
            occasions__id__in=occasion_ids
        ).exclude(id=bouquet.id).distinct()[:4]
        
        # Add encrypted IDs and images to related products
        for related in related_bouquets:
            related.encrypted_id = enc(str(related.id))
            primary_image = related.images.filter(is_active=1).first()
            related.primary_image = primary_image.image_path if primary_image else None
        
        # Get all reviews
        all_reviews = bouquet.reviews.filter(is_active=1).select_related('user')
        
        # Check if current user has already reviewed
        user_review = None
        other_reviews = all_reviews
        
        if request.user.is_authenticated:
            # Separate user's review from others
            user_review = all_reviews.filter(user=request.user).first()
            if user_review:
                other_reviews = all_reviews.exclude(user=request.user)
            else:
                other_reviews = all_reviews
        else:
            other_reviews = all_reviews
        
        # Combine with user's review first, then paginate
        if user_review:
            # Create a list with user review first, then others
            combined_reviews = [user_review] + list(other_reviews)
        else:
            combined_reviews = list(other_reviews)
        
        # Paginate the combined list
        paginator = Paginator(combined_reviews, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Calculate average rating
        avg_rating = all_reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        
        context = {
            'bouquet': bouquet,
            'images': images,
            'related_bouquets': related_bouquets,
            'encrypted_id': encrypted_id,
            'reviews': page_obj,
            'page_obj': page_obj,
            'avg_rating': round(avg_rating, 1),
            'total_reviews': all_reviews.count(),
            'user_review': user_review,  # Pass user's review to template
            "MEDIA_URL": settings.MEDIA_URL,
        }
        return render(request, 'store/product_detail.html', context)
        
    except Exception as e:
        logger.exception(f"Error in product_detail: {str(e)}")
        messages.error(request, 'Something went wrong.')
        return redirect('shop')

@login_required
@require_POST
def add_review(request):
    """Add a review for a product"""
    try:
        bouquet_id = request.POST.get('bouquet_id')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        
        # Validation
        if not bouquet_id or not rating or not comment:
            messages.error(request, 'All fields are required')
            return redirect(request.META.get('HTTP_REFERER', 'shop'))
        
        # Decrypt bouquet ID
        try:
            decrypted_id = dec(bouquet_id)
            bouquet = Bouquet.objects.get(id=decrypted_id, is_active=1)
        except:
            messages.error(request, 'Invalid product')
            return redirect('shop')
        
        # Validate rating
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except:
            messages.error(request, 'Invalid rating')
            return redirect(f"{reverse('product_detail')}?id={bouquet_id}")
        
        # Validate comment length
        if len(comment) < 10:
            messages.error(request, 'Review must be at least 10 characters')
            return redirect(f"{reverse('product_detail')}?id={bouquet_id}")
        if len(comment) > 500:
            messages.error(request, 'Review cannot exceed 500 characters')
            return redirect(f"{reverse('product_detail')}?id={bouquet_id}")
        
        # Check if user already reviewed
        existing_review = Review.objects.filter(bouquet=bouquet, user=request.user).first()
        if existing_review:
            messages.error(request, 'You have already reviewed this product')
            return redirect(f"{reverse('product_detail')}?id={bouquet_id}")
        
        # Create review
        Review.objects.create(
            bouquet=bouquet,
            user=request.user,
            rating=rating,
            comment=comment
        )
        
        messages.success(request, 'Thank you for your review!')
        return redirect(f"{reverse('product_detail')}?id={bouquet_id}")
        
    except Exception as e:
        logger.exception(f"Error in add_review: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again.')
        return redirect(request.META.get('HTTP_REFERER', 'shop'))

# ------------------- HELPER FUNCTIONS -------------------

def get_or_create_cart(request):
    """Helper function to get or create cart based on user/session"""
    try:
        if request.user.is_authenticated:
            # Logged in user - get or create cart by user
            cart, created = Cart.objects.get_or_create(
                user=request.user,
                defaults={'session_key': None}
            )
        else:
            # Guest user - use session key
            if not request.session.session_key:
                request.session.create()
                print(f"Created new session: {request.session.session_key}")
            
            cart, created = Cart.objects.get_or_create(
                session_key=request.session.session_key,
                defaults={'user': None}
            )
            print(f"Guest cart: {cart.id}, Created: {created}")
        
        return cart
    except Exception as e:
        print(f"Error in get_or_create_cart: {e}")
        # Return a new cart object as fallback
        if request.user.is_authenticated:
            return Cart.objects.create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            return Cart.objects.create(session_key=request.session.session_key)

def get_cart_item_count(cart):
    """Get number of items in cart"""
    return CartItem.objects.filter(cart=cart).count()

def get_cart_total(cart):
    """Calculate cart total"""
    items = CartItem.objects.filter(cart=cart).select_related('bouquet')
    total = Decimal('0.00')
    
    for item in items:
        # Use price_at_add if available, otherwise use current bouquet price
        if item.price_at_add:
            price = item.price_at_add
        else:
            bouquet = item.bouquet
            price = bouquet.discount_price if bouquet.discount_price else bouquet.price
        total += price
    
    return total

def can_add_to_cart(cart):
    """Check if cart can accept more items (max 10)"""
    return get_cart_item_count(cart) < 10

def get_remaining_slots(cart):
    """Get remaining slots in cart"""
    return 10 - get_cart_item_count(cart)

def get_cart_items_details(cart):
    """Get cart items with bouquet details for display"""
    items = CartItem.objects.filter(cart=cart)
    cart_items = []
    
    for item in items:
        cart_items.append({
            'id': item.id,
            'encrypted_id': item.encrypted_id,
            'name': item.bouquet_name,
            'price': item.price_at_add,
            'image': item.bouquet_image,
            'slug': item.bouquet_slug,
            'item': item
        })
    
    return cart_items

# ------------------- CART OPERATIONS -------------------

@require_POST
def add_to_cart(request):
    """Add item to cart (AJAX endpoint)"""
    try:
        data = json.loads(request.body)
        encrypted_id = data.get('bouquet_id')
        
        if not encrypted_id:
            return JsonResponse({'success': False, 'message': 'Invalid product'})
        
        # Verify product exists
        try:
            bouquet_id = dec(encrypted_id)
            bouquet = Bouquet.objects.filter(id=bouquet_id, is_active=1).first()
            
            if not bouquet:
                return JsonResponse({'success': False, 'message': 'Product not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Invalid product'})
        
        # Get or create cart
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
        
        # Check limits and duplicates
        if CartItem.objects.filter(cart=cart).count() >= 10:
            return JsonResponse({'success': False, 'message': 'Cart limit reached (maximum 10 items)'})
        
        if CartItem.objects.filter(cart=cart, bouquet=bouquet).exists():
            return JsonResponse({'success': False, 'message': 'Item already in cart'})
        
        # Get primary image
        primary_image = bouquet.images.filter(is_active=1).first()
        image_path = primary_image.image_path if primary_image else ''
        
        # Determine price
        price_at_add = bouquet.discount_price if bouquet.discount_price else bouquet.price
        
        # Create cart item with all details
        cart_item = CartItem.objects.create(
            cart=cart,
            bouquet=bouquet,
            bouquet_name=bouquet.name,
            bouquet_slug=bouquet.slug,
            bouquet_image=image_path,
            encrypted_id=encrypted_id,
            price_at_add=price_at_add
        )
        
        new_count = CartItem.objects.filter(cart=cart).count()
        
        return JsonResponse({
            'success': True,
            'message': 'Item added to cart',
            'cart_count': new_count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
    
@require_POST
def remove_from_cart(request):
    """Remove item from cart"""
    try:
        data = json.loads(request.body)
        encrypted_id = data.get('bouquet_id')
        
        if not encrypted_id:
            return JsonResponse({'success': False, 'message': 'Invalid item'})
        
        # Get cart
        cart = get_or_create_cart(request)
        
        # Find and delete the cart item
        # We need to find by encrypted_id or by bouquet
        try:
            bouquet_id = dec(encrypted_id)
            deleted, _ = CartItem.objects.filter(cart=cart, bouquet_id=bouquet_id).delete()
        except:
            # If decryption fails, try matching encrypted_id directly
            deleted, _ = CartItem.objects.filter(cart=cart, encrypted_id=encrypted_id).delete()
        
        if deleted:
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'cart_count': get_cart_item_count(cart),
                'cart_total': float(get_cart_total(cart)),
                'remaining_slots': get_remaining_slots(cart)
            })
        else:
            return JsonResponse({'success': False, 'message': 'Item not found in cart'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def get_cart_count(request):
    """AJAX endpoint to get cart count"""
    cart = get_or_create_cart(request)
    count = get_cart_item_count(cart)
    return JsonResponse({'count': count})

@no_direct_access
@login_required
def checkout(request):
    """Checkout page (requires login)"""
    try:
        # Check if this is a buy now request
        buy_now_id = request.GET.get('buy_now')
        user = request.user
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        if buy_now_id:
            # Buy now - show only this product
            try:
                bouquet_id = dec(buy_now_id)
                bouquet = Bouquet.objects.get(id=bouquet_id, is_active=1)
                
                primary_image = bouquet.images.filter(is_active=1).first()
                
                # Use Decimal consistently
                price = bouquet.discount_price if bouquet.discount_price else bouquet.price
                
                cart_items = [{
                    'encrypted_id': buy_now_id,
                    'bouquet_id': bouquet.id,  # Store bouquet ID for later
                    'name': bouquet.name,
                    'price': price,
                    'original_price': bouquet.price if bouquet.discount_price else None,
                    'discount_percent': bouquet.discount_percent,
                    'image': primary_image.image_path if primary_image else None,
                }]
                
                subtotal = price
                item_count = 1
                
            except Exception as e:
                print(f"Buy now error: {e}")
                messages.error(request, 'Product not found')
                return redirect('shop')
        else:
            # Normal checkout - show cart items
            try:
                cart = get_or_create_cart(request)
                
                if get_cart_item_count(cart) == 0:
                    messages.warning(request, 'Your cart is empty')
                    return redirect('cart_view')
                
                cart_items = get_cart_items_details(cart)
                subtotal = Decimal('0.00')
                
                # Calculate subtotal ensuring Decimal type
                for item in cart_items:
                    if isinstance(item['price'], float):
                        subtotal += Decimal(str(item['price']))
                    else:
                        subtotal += item['price']
                
                item_count = len(cart_items)
                
            except Exception as e:
                print(f"Cart checkout error: {e}")
                messages.error(request, 'Error loading your cart')
                return redirect('cart_view')
        
        # Free shipping calculation (from checkout page logic)
        free_shipping_threshold = 2000
        
        if subtotal >= free_shipping_threshold:
            shipping = Decimal('0.00')
            free_shipping_qualified = True
            remaining_for_free_shipping = 0
        else:
            shipping = Decimal('150.00')
            free_shipping_qualified = False
            remaining_for_free_shipping = free_shipping_threshold - subtotal
        
        total = subtotal + shipping
        
        # Pre-fill form with user data if available
        initial_data = {
            'email': user.email,
            'phone': user.phone or '',
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'address_line1': profile.address_line1 or '',
            'address_line2': profile.address_line2 or '',
            'landmark': profile.landmark or '',
            'city': profile.city or '',
            'state': profile.state or '',
            'pincode': profile.pincode or '',
            'country': profile.country or 'India',
        }
        
        context = {
            'cart_items': cart_items,
            'item_count': item_count,
            'subtotal': float(subtotal),
            'shipping': float(shipping),
            'total': float(total),
            'user': user,
            'profile': profile,
            'initial_data': initial_data,
            'MEDIA_URL': settings.MEDIA_URL,
            'is_buy_now': bool(buy_now_id),
            'buy_now_id': buy_now_id,  # Pass for form action
            'free_shipping_qualified': free_shipping_qualified,
            'free_shipping_threshold': free_shipping_threshold,
            'remaining_for_free_shipping': float(remaining_for_free_shipping),
        }
        
        return render(request, 'store/checkout.html', context)
        
    except Exception as e:
        print(f"Unexpected checkout error: {e}")
        messages.error(request, 'Something went wrong. Please try again.')
        return redirect('shop')

@no_direct_access
@login_required
def buy_now_checkout(request):
    """Checkout page for buy now - shows only the selected product"""
    encrypted_id = request.GET.get('id')
    
    if not encrypted_id:
        messages.error(request, 'Product not specified')
        return redirect('shop')
    
    try:
        # Decrypt and get the product
        bouquet_id = dec(encrypted_id)
        bouquet = Bouquet.objects.get(id=bouquet_id, is_active=1)
        
        # Get product details for checkout
        primary_image = bouquet.images.filter(is_active=1).first()
        
        # Create a single-item "cart" for checkout
        cart_items = [{
            'encrypted_id': encrypted_id,
            'name': bouquet.name,
            'price': float(bouquet.discount_price if bouquet.discount_price else bouquet.price),
            'original_price': float(bouquet.price) if bouquet.discount_price else None,
            'discount_percent': bouquet.discount_percent,
            'image': primary_image.image_path if primary_image else None,
        }]
        
        subtotal = cart_items[0]['price']
        shipping = Decimal('150.00') if subtotal < Decimal('999.00') else Decimal('0.00')
        tax = subtotal * Decimal('0.05')
        total = subtotal + shipping + tax
        
        context = {
            'cart_items': cart_items,
            'item_count': 1,
            'subtotal': float(subtotal),
            'shipping': float(shipping),
            'tax': float(tax),
            'total': float(total),
            'user': request.user,
            'MEDIA_URL': settings.MEDIA_URL,
            'is_buy_now': True,  # Flag to indicate this is a buy now checkout
            'product_id': encrypted_id,
        }
        
        return render(request, 'store/checkout.html', context)
        
    except Exception as e:
        messages.error(request, 'Product not found')
        return redirect('shop')

@no_direct_access    
def cart_view(request):
    """Display cart page"""
    cart = get_or_create_cart(request)
    
    # Get cart items with details
    cart_items = get_cart_items_details(cart)
    subtotal = sum(item['price'] for item in cart_items)
    
    # Free shipping calculation (same as checkout)
    free_shipping_threshold = 2000
    
    if subtotal >= free_shipping_threshold:
        shipping = Decimal('0.00')
        free_shipping_qualified = True
        remaining_for_free_shipping = 0
    else:
        shipping = Decimal('150.00')
        free_shipping_qualified = False
        remaining_for_free_shipping = free_shipping_threshold - subtotal
    
    # No tax
    tax = Decimal('0.00')
    total = subtotal + shipping
    
    # Store checkout redirect in session if user clicks checkout while not logged in
    if not request.user.is_authenticated:
        request.session['checkout_after_login'] = True
    
    context = {
        'cart_items': cart_items,
        'item_count': len(cart_items),
        'subtotal': float(subtotal),
        'shipping': float(shipping),
        'tax': float(tax),
        'total': float(total),
        'cart_limit': 10,
        'remaining_slots': 10 - len(cart_items),
        'cart_id': cart.id,
        'free_shipping_threshold': free_shipping_threshold,
        'free_shipping_qualified': free_shipping_qualified,
        'remaining_for_free_shipping': float(remaining_for_free_shipping),
        'needs_shipping': shipping > 0,
        'is_authenticated': request.user.is_authenticated,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    
    return render(request, 'store/cart.html', context)

# ------------------- CART MERGE ON LOGIN -------------------

def merge_carts_on_login(request, old_session_key):
    """Called after login to merge guest cart with user cart"""
    if not request.user.is_authenticated or not old_session_key:
        return {'merged': 0, 'skipped': 0, 'total': 0}
    
    guest_cart = Cart.objects.filter(session_key=old_session_key).first()
    if not guest_cart or get_cart_item_count(guest_cart) == 0:
        return {'merged': 0, 'skipped': 0, 'total': 0}
    
    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    guest_items = CartItem.objects.filter(cart=guest_cart).select_related('bouquet')
    
    merged_count = 0
    skipped_count = 0
    
    with transaction.atomic():
        for guest_item in guest_items:
            if not CartItem.objects.filter(cart=user_cart, bouquet=guest_item.bouquet).exists():
                if get_cart_item_count(user_cart) + merged_count >= 10:
                    skipped_count += 1
                    continue
                
                # Copy all details from guest item
                CartItem.objects.create(
                    cart=user_cart,
                    bouquet=guest_item.bouquet,
                    bouquet_name=guest_item.bouquet_name,
                    bouquet_slug=guest_item.bouquet_slug,
                    bouquet_image=guest_item.bouquet_image,
                    encrypted_id=guest_item.encrypted_id or enc(str(guest_item.bouquet.id)),
                    price_at_add=guest_item.price_at_add
                )
                merged_count += 1
        
        guest_cart.delete()
    
    return {
        'merged': merged_count,
        'skipped': skipped_count,
        'total': get_cart_item_count(user_cart)
    }
    
# ------------------- CART UTILITIES -------------------

@login_required
def clear_cart(request):
    """Clear all items from cart"""
    if request.method == 'POST':
        cart = get_or_create_cart(request)
        CartItem.objects.filter(cart=cart).delete()
        messages.success(request, 'Cart cleared successfully')
    
    return redirect('cart_view')

def update_cart_item_price(request, item_id):
    """Update cart item price to current bouquet price (admin utility)"""
    if request.method == 'POST' and request.user.is_staff:
        try:
            item = CartItem.objects.get(id=item_id)
            item.price_at_add = item.bouquet.discount_price if item.bouquet.discount_price else item.bouquet.price
            item.save()
            return JsonResponse({'success': True})
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Item not found'})
    
    return JsonResponse({'success': False, 'message': 'Unauthorized'})

def cart_modal(request):
    """Return cart modal HTML for AJAX"""
    try:
        # Get or create cart for both logged in and guest users
        cart = get_or_create_cart(request)
        
        # Get items (limit to 3 for modal)
        items = CartItem.objects.filter(cart=cart).select_related('bouquet').prefetch_related('bouquet__images')[:3]
        
        # Get URLs using reverse
        from django.urls import reverse
        cart_url = reverse('cart_view')
        shop_url = reverse('shop')
        
        html = ''
        if items:
            for item in items:
                # Get first image safely
                first_image = item.bouquet.images.filter(is_active=1).first()
                image_path = first_image.image_path if first_image else ''
                image_url = f"{settings.MEDIA_URL}{image_path}" if image_path else ''
                
                html += f'''
                <div class="account-menu-item">
                    <div class="account-menu-icon">
                        <img src="{image_url}" 
                             style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px;"
                             onerror="this.src='https://via.placeholder.com/50'">
                    </div>
                    <div class="account-menu-text">
                        <span class="account-menu-title">{item.bouquet.name}</span>
                        <span class="account-menu-desc">₹{item.price_at_add}</span>
                    </div>
                    <div class="account-menu-arrow">
                        <button class="btn btn-sm" style="color: #dc3545;" onclick="removeFromCartModal('{item.encrypted_id}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
                '''
            
            # Get total
            total = get_cart_total(cart)
            html += f'''
            <div class="mt-3 p-3" style="background: #f0e6ea; border-radius: 8px;">
                <div class="d-flex justify-content-between">
                    <span>Total:</span>
                    <span style="color: #8c0d4f; font-weight: bold;">₹{total}</span>
                </div>
            </div>
            <div class="d-grid gap-2 mt-3">
                <a href="{cart_url}" class="btn" style="background: #8c0d4f; color: white; border: none; padding: 10px; border-radius: 8px;">
                    View Full Cart
                </a>
            </div>
            '''
        else:
            html = f'''
            <div class="text-center py-4">
                <i class="bi bi-cart3" style="font-size: 48px; color: #8c0d4f; opacity: 0.5;"></i>
                <p class="mt-3">Your cart is empty</p>
                <a href="{shop_url}" class="btn mt-2" style="background: #8c0d4f; color: white; border: none; padding: 8px 20px; border-radius: 8px;">
                    Continue Shopping
                </a>
            </div>
            '''
        
        return HttpResponse(html)
        
    except Exception as e:
        print(f"Error in cart_modal: {e}")
        import traceback
        traceback.print_exc()
        
        from django.urls import reverse
        shop_url = reverse('shop')
        
        return HttpResponse(f'''
        <div class="text-center py-4">
            <i class="bi bi-exclamation-triangle" style="font-size: 48px; color: #dc3545; opacity: 0.5;"></i>
            <p class="mt-3 text-danger">Could not load your cart</p>
            <a href="{shop_url}" class="btn mt-2" style="background: #8c0d4f; color: white;">
                Continue Shopping
            </a>
        </div>
        ''')
        
@no_direct_access
@login_required
@require_POST
def place_order(request):
    """Place order after checkout"""
    try:
        user = request.user
        profile = user.profile
        
        # Get form data
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        address_line1 = request.POST.get('address_line1', '').strip()
        address_line2 = request.POST.get('address_line2', '').strip()
        landmark = request.POST.get('landmark', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        country = request.POST.get('country', 'India').strip()
        
        # Get delivery and payment from checkout page
        delivery_option = 'standard'
        payment_method = 'cod'
        notes = request.POST.get('notes', '').strip()
        
        # Check if this is a buy now request
        buy_now_id = request.POST.get('buy_now_id') or request.GET.get('buy_now')
        
        # Validation
        import re
        errors = []
        
        if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors.append('Valid email is required.')
        
        if not phone or not re.match(r'^\d{10}$', phone):
            errors.append('Valid 10-digit phone number is required.')
        
        if not first_name:
            errors.append('First name is required.')
        
        if not last_name:
            errors.append('Last name is required.')
        
        if not address_line1:
            errors.append('Address is required.')
        
        if not city:
            errors.append('City is required.')
        
        if not state:
            errors.append('State is required.')
        
        if not pincode or not re.match(r'^\d{6}$', pincode):
            errors.append('Valid 6-digit pincode is required.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            if buy_now_id:
                return redirect(f"{reverse('checkout')}?buy_now={buy_now_id}")
            else:
                return redirect('checkout')
        
        with transaction.atomic():
            # Calculate order totals
            if buy_now_id:
                # Buy now - single product
                try:
                    bouquet_id = dec(buy_now_id)
                    bouquet = Bouquet.objects.get(id=bouquet_id, is_active=1)
                    
                    price = bouquet.discount_price if bouquet.discount_price else bouquet.price
                    subtotal = price
                    
                    order_items_data = [{
                        'bouquet': bouquet,
                        'bouquet_name': bouquet.name,
                        'bouquet_slug': bouquet.slug,
                        'price': price,
                        'original_price': bouquet.price if bouquet.discount_price else None,
                        'discount_percent': bouquet.discount_percent or 0,
                    }]
                    
                except Exception as e:
                    messages.error(request, 'Product not found.')
                    return redirect('shop')
            else:
                # Normal checkout - get cart items
                cart = get_or_create_cart(request)
                cart_items = CartItem.objects.filter(cart=cart).select_related('bouquet')
                
                if not cart_items.exists():
                    messages.error(request, 'Your cart is empty.')
                    return redirect('cart_view')
                
                subtotal = Decimal('0.00')
                order_items_data = []
                
                for item in cart_items:
                    bouquet = item.bouquet
                    price = item.price_at_add
                    subtotal += price
                    
                    order_items_data.append({
                        'bouquet': bouquet,
                        'bouquet_name': bouquet.name,
                        'bouquet_slug': bouquet.slug,
                        'price': price,
                        'original_price': bouquet.price if bouquet.discount_price else None,
                        'discount_percent': bouquet.discount_percent or 0,
                    })
            
            # Calculate shipping
            free_shipping_threshold = 2000
            if subtotal >= free_shipping_threshold:
                shipping = Decimal('0.00')
            else:
                shipping = Decimal('150.00')
            
            total = subtotal + shipping
            
            # Create order
            order = Order.objects.create(
                user=user,
                email=email,
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                address_line1=address_line1,
                address_line2=address_line2 or None,
                landmark=landmark or None,
                city=city,
                state=state,
                pincode=pincode,
                country=country,
                delivery_option=delivery_option,
                delivery_charge=shipping,
                payment_method=payment_method,
                order_notes=notes or None,
                subtotal=subtotal,
                total=total,
                status='pending',
                payment_status='pending'
            )
            
            # Create order items
            for item_data in order_items_data:
                OrderItem.objects.create(
                    order=order,
                    bouquet=item_data['bouquet'],
                    bouquet_name=item_data['bouquet_name'],
                    bouquet_slug=item_data['bouquet_slug'],
                    price=item_data['price'],
                    original_price=item_data['original_price'],
                    discount_percent=item_data['discount_percent']
                )
            
            # Clear the cart (only for normal checkout)
            if not buy_now_id:
                CartItem.objects.filter(cart=cart).delete()
                cart.delete()
            
            # Update user profile with the new address if it was empty
            profile_updated = False
            if not profile.address_line1:
                profile.address_line1 = address_line1
                profile.address_line2 = address_line2 or None
                profile.landmark = landmark or None
                profile.city = city
                profile.state = state
                profile.pincode = pincode
                profile.country = country
                profile_updated = True
            
            # Update user basic info if empty
            user_updated = False
            if not user.first_name:
                user.first_name = first_name
                user_updated = True
            
            if not user.last_name:
                user.last_name = last_name
                user_updated = True
            
            if not user.phone:
                user.phone = phone
                user_updated = True
            
            if profile_updated:
                profile.save()
            
            if user_updated:
                user.save()
        
        # Encrypt order ID for redirect
        encrypted_order_id = enc(str(order.id))
        messages.success(request, f'Order placed successfully! Order #{order.order_number}')
        return redirect('order_confirmation', order_id=encrypted_order_id)
        
    except Exception as e:
        logger.exception(f"Error placing order: {e}")
        messages.error(request, 'Failed to place order. Please try again.')
        if buy_now_id:
            return redirect(f"{reverse('checkout')}?buy_now={buy_now_id}")
        else:
            return redirect('checkout')

@no_direct_access
@login_required
def order_confirmation(request, order_id):
    """Show order confirmation after successful order"""
    try:
        # Decrypt the order ID
        decrypted_id = dec(str(order_id))
        
        # Get the order and verify it belongs to the logged-in user
        order = Order.objects.get(id=decrypted_id, user=request.user)
        
        # Get order items with bouquet details
        order_items = order.items.all().select_related('bouquet')
        
        # Encrypt order ID for any links
        encrypted_order_id = enc(str(order.id))
        
        context = {
            'order': order,
            'order_items': order_items,
            'encrypted_order_id': encrypted_order_id,
        }
        return render(request, 'store/order_confirmation.html', context)
        
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('shop')
    except Exception as e:
        logger.exception(f"Error in order_confirmation: {e}")
        messages.error(request, 'Something went wrong. Please try again.')
        return redirect('shop')