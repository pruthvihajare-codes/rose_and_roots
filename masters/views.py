import uuid
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import DatabaseError
import logging
from rose_and_roots.access_control import no_direct_access
from django.shortcuts import render, redirect
from django.db import transaction
from accounts.models import *
from masters.models import *
logger = logging.getLogger(__name__)
from django.conf import settings
import os

@no_direct_access
@login_required
def admin_dashboard(request):
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if not request.session.session_key:
            messages.error(request, 'Your session has expired. Please login again.')
            return redirect('/')
        
        # Check if user has admin role
        if not hasattr(request.user, 'role_id') or request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        context = {
            "page_title": "Admin Dashboard",
            "user": request.user,
            "session_key": request.session.session_key
        }

        return render(request, "masters/admin_dashboard.html", context)

    except Exception as e:
        logger.exception("Unexpected error in admin_dashboard")
        messages.error(request, "Something went wrong.")
        return redirect('login')
    
@no_direct_access
@login_required
def dashboard(request):
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if not request.session.session_key:
            messages.error(request, 'Your session has expired. Please login again.')
            return redirect('/')
        
        # Check if user has admin role
        if not hasattr(request.user, 'role_id') or request.user.role_id != 2:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        context = {
            "page_title": "Dashboard",
            "user": request.user,
            "session_key": request.session.session_key
        }

        return render(request, "masters/dashboard.html", context)

    except Exception as e:
        logger.exception("Unexpected error in dashboard")
        messages.error(request, "Something went wrong.")
        return render(request, "masters/dashboard.html")

import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.utils.text import slugify
from decimal import Decimal, InvalidOperation
from .models import Bouquet, Occasion, BouquetOccasion, BouquetImage, Vendor

logger = logging.getLogger(__name__)

@no_direct_access
@login_required
@transaction.atomic
def add_bouquet(request):
    """
    Add new bouquet with images and occasions
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if not request.session.session_key:
            messages.error(request, 'Your session has expired. Please login again.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        # GET request - display form
        if request.method == 'GET':
            # Get all active occasions for selection
            occasions = Occasion.objects.filter(is_active=1).order_by('name')
            
            # Get all active vendors
            vendors = Vendor.objects.filter(is_active=1).order_by('vendor_name')
            
            context = {
                'occasions': occasions,
                'vendors': vendors,
                'selected_occasions': [],  # Empty list for new form
            }
            return render(request, 'masters/add_bouquet.html', context)
        
        if request.method == 'POST':

            bouquet_name = request.POST.get('bouquet_name', '').strip()
            short_description = request.POST.get('short_description', '').strip()
            description = request.POST.get('description', '').strip()
            delivery_info = request.POST.get('delivery_info', '').strip()
            instruction_text = request.POST.get('instruction_text', '').strip()
            price = request.POST.get('price', 0)
            discount = request.POST.get('discount', 0)
            vendor_id = request.POST.get('vendor')
            occasion_ids_str = request.POST.get('occasions', '')
            occasion_ids = [id for id in occasion_ids_str.split(',') if id]
            is_active = request.POST.get('is_active', '1')

            errors = {}

            # ---------------- VALIDATION ---------------- #

            if not bouquet_name:
                errors['bouquet_name'] = 'Bouquet name is required.'

            if not short_description:
                errors['short_description'] = 'Short description is required.'

            if not description:
                errors['description'] = 'Full description is required.'

            try:
                price_decimal = Decimal(price)
                if price_decimal <= 0:
                    errors['price'] = 'Price must be greater than 0.'
            except (InvalidOperation, TypeError):
                errors['price'] = 'Invalid price format.'

            try:
                discount_int = int(discount) if discount else 0
                if discount_int < 0 or discount_int > 100:
                    errors['discount'] = 'Discount must be between 0 and 100.'
            except ValueError:
                errors['discount'] = 'Invalid discount value.'

            if not occasion_ids:
                errors['occasions'] = 'Select at least one occasion.'

            images = request.FILES.getlist('bouquet_images')

            if not images:
                errors['images'] = 'Upload at least one image.'
            elif len(images) > 5:
                errors['images'] = 'Maximum 5 images allowed.'

            if errors:
                for error in errors.values():
                    messages.error(request, error)
                return render(request, 'masters/add_bouquet.html')

            # ---------------- SAVE DATA ---------------- #

            try:
                with transaction.atomic():

                    # Calculate discount price
                    discount_price = None
                    if discount_int > 0:
                        discount_price = price_decimal - (price_decimal * discount_int / 100)

                    # Generate unique slug
                    base_slug = slugify(bouquet_name)
                    slug = base_slug
                    counter = 1
                    while Bouquet.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1

                    # Create bouquet
                    bouquet = Bouquet.objects.create(
                        name=bouquet_name,
                        slug=slug,
                        short_description=short_description,
                        description=description,
                        delivery_info=delivery_info,
                        instruction_text=instruction_text,
                        price=price_decimal,
                        discount_percent=discount_int,
                        discount_price=discount_price,
                        is_active=1 if is_active == '1' else 0,
                        same_day_available=0,
                        is_featured=0
                    )

                    # ---------------- IMAGE SAVE ---------------- #

                    allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']

                    # Folder: bouquets/<bouquet_id>/
                    relative_path = f"bouquets/{bouquet.id}/"
                    upload_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                    os.makedirs(upload_path, exist_ok=True)

                    for image_file in images:

                        if image_file.size > 6 * 1024 * 1024:
                            continue

                        if image_file.content_type not in allowed_types:
                            continue

                        ext = os.path.splitext(image_file.name)[1]
                        unique_filename = f"{uuid.uuid4().hex}{ext}"

                        full_path = os.path.join(upload_path, unique_filename)

                        with open(full_path, 'wb+') as destination:
                            for chunk in image_file.chunks():
                                destination.write(chunk)

                        db_image_path = f"{relative_path}{unique_filename}"

                        BouquetImage.objects.create(
                            bouquet=bouquet,
                            image_name=image_file.name,
                            image_path=db_image_path,
                            is_active=1,
                            created_by=request.user.id
                        )

                    # ---------------- OCCASIONS ---------------- #

                    occasions = Occasion.objects.filter(
                        id__in=occasion_ids,
                        is_active=1
                    )

                    for occasion in occasions:
                        BouquetOccasion.objects.create(
                            bouquet=bouquet,
                            occasion=occasion
                        )

                messages.success(request, "Bouquet created successfully!")
                return redirect('admin_dashboard')

            except Exception as e:
                logger.exception(str(e))
                messages.error(request, "Something went wrong.")
                return render(request, 'masters/add_bouquet.html')

    except Exception as e:
        logger.exception(f"Unexpected error in add_bouquet: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('add_bouquet')