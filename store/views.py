import uuid
import os
import json
import logging
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, DatabaseError
from django.conf import settings
from django.utils.text import slugify

from rose_and_roots.access_control import no_direct_access
from accounts.models import *
from masters.models import *
from rose_and_roots.encryption import *

logger = logging.getLogger(__name__)

# views.py (customer facing views)

from django.shortcuts import render
from django.db.models import Q, Min, Max
from masters.models import Bouquet, Occasion, BouquetImage
from django.core.paginator import Paginator

# views.py (customer facing views)

from django.shortcuts import render
from django.db.models import Q, Min, Max
from masters.models import Bouquet, Occasion, BouquetImage
from django.core.paginator import Paginator
from rose_and_roots.encryption import enc  # Import your encryption function

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
    Display single product details
    """
    encrypted_id = request.GET.get('id')
    
    if not encrypted_id:
        messages.error(request, 'Product ID is required.')
        return redirect('shop')
    
    try:
        # Decrypt the ID
        from rose_and_roots.encryption import dec
        bouquet_id = dec(str(encrypted_id))
        
        # Get bouquet with related data
        bouquet = Bouquet.objects.filter(
            id=bouquet_id, 
            is_active=1
        ).prefetch_related('occasions', 'images').first()
        
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
        
        context = {
            'bouquet': bouquet,
            'images': images,
            'related_bouquets': related_bouquets,
            'encrypted_id': encrypted_id,
        }
        return render(request, 'store/product_detail.html', context)
        
    except Exception as e:
        logger.exception(f"Error in product_detail: {str(e)}")
        messages.error(request, 'Something went wrong.')
        return redirect('shop')