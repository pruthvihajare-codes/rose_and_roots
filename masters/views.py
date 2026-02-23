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
            return redirect('/')
        
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

@no_direct_access
@login_required
@transaction.atomic
def bouquet_list(request):
    """
    Display list of all bouquets
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # Get all bouquets with related data
        bouquets = Bouquet.objects.all().order_by('-created_at').select_related().prefetch_related('occasions', 'images')
        
        # Get all active occasions for the filter dropdown
        occasions = Occasion.objects.filter(is_active=1).order_by('name')
        
        # Add encrypted IDs
        bouquet_list = []
        for bouquet in bouquets:
            bouquet.encrypted_id = enc(str(bouquet.id))
            
            # Get primary image (first active image)
            primary_image = bouquet.images.filter(is_active=1).first()
            bouquet.primary_image = primary_image.image_path if primary_image else None
            
            # Get occasion names
            occasion_names = [occ.name for occ in bouquet.occasions.all()]
            bouquet.occasion_list = ', '.join(occasion_names[:3])  # Show first 3 occasions
            if len(occasion_names) > 3:
                bouquet.occasion_list += f' +{len(occasion_names)-3} more'
                
            bouquet_list.append(bouquet)
        
        context = {
            'bouquets': bouquet_list,
            'occasions': occasions,  # ← This was missing!
        }
        return render(request, 'masters/bouquet_list.html', context)
        
    except Exception as e:
        logger.exception(f"Error in bouquet_list: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('admin_dashboard')

@no_direct_access
@login_required
def view_bouquet(request):
    """
    View bouquet details using encrypted ID from query parameter
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # Get encrypted ID from query parameter
        encrypted_id = request.GET.get('bouquet_id')
        
        if not encrypted_id:
            messages.error(request, 'Bouquet ID is required.')
            return redirect('bouquet_list')
        
        # Decrypt the bouquet ID
        decrypted_id = dec(str(encrypted_id))
        
        # Get bouquet with related data
        bouquet = get_object_or_404(
            Bouquet.objects.prefetch_related('occasions', 'images'), 
            id=decrypted_id
        )
        
        # Get all occasions for this bouquet
        occasions = bouquet.occasions.all()
        
        # Get all images for this bouquet
        images = bouquet.images.filter(is_active=1).order_by('id')
        
        context = {
            'bouquet': bouquet,
            'occasions': occasions,
            'images': images,
            'encrypted_id': encrypted_id,
        }
        return render(request, 'masters/view_bouquet.html', context)
        
    except Exception as e:
        logger.exception(f"Error in view_bouquet: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('bouquet_list')

@no_direct_access
@login_required
@transaction.atomic
def edit_bouquet(request):
    """
    Edit bouquet details using encrypted ID from query parameter
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # Get encrypted ID from query parameter
        encrypted_id = request.GET.get('bouquet_id')
        
        if not encrypted_id:
            messages.error(request, 'Bouquet ID is required.')
            return redirect('bouquet_list')
        
        # Decrypt the bouquet ID
        decrypted_id = dec(str(encrypted_id))
        
        # Get bouquet
        bouquet = get_object_or_404(
            Bouquet.objects.prefetch_related('occasions', 'images'), 
            id=decrypted_id
        )
        
        # Get all active occasions for selection
        occasions = Occasion.objects.filter(is_active=1).order_by('name')
        
        # Get selected occasion IDs
        selected_occasion_ids = list(bouquet.occasions.values_list('id', flat=True))
        
        # Get all images
        images = bouquet.images.filter(is_active=1).order_by('id')
        
        # GET request - display form
        if request.method == 'GET':
            context = {
                'bouquet': bouquet,
                'occasions': occasions,
                'selected_occasions': [str(id) for id in selected_occasion_ids],
                'images': images,
                'encrypted_id': encrypted_id,
            }
            return render(request, 'masters/edit_bouquet.html', context)
        
        # POST request - process form
        if request.method == 'POST':
            
            bouquet_name = request.POST.get('bouquet_name', '').strip()
            short_description = request.POST.get('short_description', '').strip()
            description = request.POST.get('description', '').strip()
            delivery_info = request.POST.get('delivery_info', '').strip()
            instruction_text = request.POST.get('instruction_text', '').strip()
            price = request.POST.get('price', 0)
            discount = request.POST.get('discount', 0)
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
            
            if errors:
                for error in errors.values():
                    messages.error(request, error)
                return redirect(f'{request.path}?bouquet_id={encrypted_id}')
            
            # ---------------- UPDATE DATA ---------------- #
            
            try:
                with transaction.atomic():
                    
                    # Calculate discount price
                    discount_price = None
                    if discount_int > 0:
                        discount_price = price_decimal - (price_decimal * discount_int / 100)
                    
                    # Update slug if name changed
                    if bouquet.name != bouquet_name:
                        base_slug = slugify(bouquet_name)
                        slug = base_slug
                        counter = 1
                        while Bouquet.objects.filter(slug=slug).exclude(id=decrypted_id).exists():
                            slug = f"{base_slug}-{counter}"
                            counter += 1
                        bouquet.slug = slug
                    
                    # Update bouquet
                    bouquet.name = bouquet_name
                    bouquet.short_description = short_description
                    bouquet.description = description
                    bouquet.delivery_info = delivery_info
                    bouquet.instruction_text = instruction_text
                    bouquet.price = price_decimal
                    bouquet.discount_percent = discount_int
                    bouquet.discount_price = discount_price
                    bouquet.is_active = 1 if is_active == '1' else 0
                    
                    bouquet.save()
                    
                    # ---------------- UPDATE OCCASIONS ---------------- #
                    
                    # Clear existing occasions
                    BouquetOccasion.objects.filter(bouquet=bouquet).delete()
                    
                    # Add new occasions
                    new_occasions = Occasion.objects.filter(
                        id__in=occasion_ids,
                        is_active=1
                    )
                    
                    for occasion in new_occasions:
                        BouquetOccasion.objects.create(
                            bouquet=bouquet,
                            occasion=occasion
                        )
                    
                    # ---------------- HANDLE NEW IMAGES ---------------- #
                    
                    new_images = request.FILES.getlist('bouquet_images')
                    
                    if new_images:
                        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
                        
                        # Check total images count
                        current_count = bouquet.images.filter(is_active=1).count()
                        if current_count + len(new_images) > 5:
                            messages.warning(request, f'Maximum 5 images allowed. Some images were not uploaded.')
                        
                        # Folder: bouquets/<bouquet_id>/
                        relative_path = f"bouquets/{bouquet.id}/"
                        upload_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                        os.makedirs(upload_path, exist_ok=True)
                        
                        for image_file in new_images[:5 - current_count]:  # Limit to 5 total
                            
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
                    
                messages.success(request, "Bouquet updated successfully!")
                return redirect('bouquet_list')
                
            except Exception as e:
                logger.exception(str(e))
                messages.error(request, "Something went wrong while updating.")
                return redirect(f'{request.path}?bouquet_id={encrypted_id}')
                
    except Exception as e:
        logger.exception(f"Unexpected error in edit_bouquet: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('bouquet_list')

@no_direct_access
@login_required
@transaction.atomic
def delete_bouquet(request):
    """
    Delete bouquet
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to perform this action.')
            return redirect('/')
        
        if request.method == 'POST':
            encrypted_bouquet_id = request.POST.get('bouquet_id')
            
            if not encrypted_bouquet_id:
                messages.error(request, 'Bouquet ID is required.')
                return redirect('bouquet_list')
            
            try:
                # Decrypt the bouquet ID
                bouquet_id = dec(str(encrypted_bouquet_id))
                bouquet = Bouquet.objects.get(id=bouquet_id)
                
                bouquet_name = bouquet.name
                
                # Delete images from filesystem
                images = BouquetImage.objects.filter(bouquet=bouquet)
                for image in images:
                    if image.image_path:
                        image_path = os.path.join(settings.MEDIA_ROOT, image.image_path)
                        if os.path.exists(image_path):
                            os.remove(image_path)
                
                # Delete bouquet (cascades to BouquetImage and BouquetOccasion)
                bouquet.delete()
                
                messages.success(request, f"Bouquet '{bouquet_name}' deleted successfully!")
                
            except Bouquet.DoesNotExist:
                messages.error(request, 'Bouquet not found.')
            except Exception as e:
                logger.exception(f"Error deleting bouquet: {str(e)}")
                messages.error(request, 'Something went wrong while deleting the bouquet.')
        
        return redirect('bouquet_list')
        
    except Exception as e:
        logger.exception(f"Unexpected error in delete_bouquet: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('bouquet_list')
    
# vendor list

@no_direct_access
@login_required
@transaction.atomic
def vendor_list(request):
    """
    Display list of all vendors
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # Get all vendors
        vendors = Vendor.objects.all().order_by('-created_at')
        vendor_list = []
        for ven in vendors:
            ven.encrypted_id = enc(str(ven.id))  # Add encrypted ID as attribute
            vendor_list.append(ven)
        
        context = {
            'vendors': vendor_list,
        }
        return render(request, 'masters/vendor_list.html', context)
        
    except Exception as e:
        logger.exception(f"Error in vendor_list: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('admin_dashboard')

@no_direct_access
@login_required
@transaction.atomic
def add_vendor(request):
    """
    Add new vendor
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # Get all delivery pincodes for dropdown - CHANGE HERE
        delivery_pincodes = DeliveryPincode.objects.filter(is_active=1).order_by('pincode')
        pincode_dict = {p.pincode: p.place_name for p in delivery_pincodes}
        
        # GET request - display form
        if request.method == 'GET':
            context = {
                'delivery_pincodes': pincode_dict,  # Now passing as dict, not JSON
                'form_data': request.session.pop('form_data', {}),
            }
            return render(request, 'masters/add_vendor.html', context)
        
        # POST request - process form
        if request.method == 'POST':
            
            vendor_name = request.POST.get('vendor_name', '').strip()
            phone_no = request.POST.get('phone_no', '').strip()
            email = request.POST.get('email', '').strip()
            pincode = request.POST.get('pincode', '').strip()
            vendor_address = request.POST.get('vendor_address', '').strip()
            is_active = request.POST.get('is_active', '0')
            
            errors = {}
            
            # ---------------- VALIDATION ---------------- #
            
            if not vendor_name:
                errors['vendor_name'] = 'Vendor name is required.'
            elif len(vendor_name) < 3:
                errors['vendor_name'] = 'Vendor name must be at least 3 characters.'
            
            if not phone_no:
                errors['phone_no'] = 'Phone number is required.'
            elif not phone_no.isdigit() or len(phone_no) != 10:
                errors['phone_no'] = 'Please enter a valid 10-digit mobile number.'
            
            if email and '@' not in email:
                errors['email'] = 'Please enter a valid email address.'
            
            if not pincode:
                errors['pincode'] = 'Pincode is required.'
            else:
                # Check if pincode exists in delivery_pincodes
                if pincode not in pincode_dict:
                    errors['pincode'] = 'Invalid pincode selected.'
            
            if errors:
                # Store form data in session
                request.session['form_data'] = request.POST.dict()
                for error in errors.values():
                    messages.error(request, error)
                return redirect('add_vendor')
            
            # ---------------- SAVE DATA ---------------- #
            
            try:
                with transaction.atomic():
                    
                    # Get area_name from pincode_dict - CHANGE HERE
                    area_name = pincode_dict.get(pincode, '')
                    
                    # Create vendor
                    vendor = Vendor.objects.create(
                        vendor_name=vendor_name,
                        phone_no=phone_no,
                        email=email if email else None,
                        area_name=area_name,  # Now using place name from delivery_pincodes
                        pincode=pincode,
                        vendor_address=vendor_address,
                        is_active=1 if is_active == '1' else 0,
                        created_by=request.user.email or 'admin'
                    )
                    
                messages.success(request, f"Vendor '{vendor_name}' created successfully!")
                return redirect('vendor_list')
                
            except Exception as e:
                logger.exception(f"Error creating vendor: {str(e)}")
                messages.error(request, "Something went wrong while saving the vendor.")
                return redirect('add_vendor')
                
    except Exception as e:
        logger.exception(f"Unexpected error in add_vendor: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('add_vendor')

@no_direct_access
@login_required
def view_vendor(request):
    """
    View vendor details using encrypted ID from query parameter
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # Get encrypted ID from query parameter
        encrypted_id = request.GET.get('vendor_id')
        
        if not encrypted_id:
            messages.error(request, 'Vendor ID is required.')
            return redirect('vendor_list')
        
        # Decrypt the vendor ID
        decrypted_id = dec(str(encrypted_id))
        
        # Get vendor
        vendor = get_object_or_404(Vendor, id=decrypted_id)
        
        context = {
            'vendor': vendor,
            'encrypted_id': encrypted_id,
        }
        return render(request, 'masters/view_vendor.html', context)
        
    except Exception as e:
        logger.exception(f"Error in view_vendor: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('vendor_list')

@no_direct_access
@login_required
@transaction.atomic
def edit_vendor(request):
    """
    Edit vendor details using encrypted ID from query parameter
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # Get encrypted ID from query parameter
        encrypted_id = request.GET.get('vendor_id')
        
        if not encrypted_id:
            messages.error(request, 'Vendor ID is required.')
            return redirect('vendor_list')
        
        # Decrypt the vendor ID
        decrypted_id = dec(str(encrypted_id))
        
        # Get vendor
        vendor = get_object_or_404(Vendor, id=decrypted_id)
        
        # Get all delivery pincodes for dropdown
        delivery_pincodes = DeliveryPincode.objects.filter(is_active=1).order_by('pincode')
        pincode_dict = {p.pincode: p.place_name for p in delivery_pincodes}
        
        # GET request - display form
        if request.method == 'GET':
            context = {
                'vendor': vendor,
                'delivery_pincodes': pincode_dict,
                'encrypted_id': encrypted_id,  # Pass back to template for form action
            }
            return render(request, 'masters/edit_vendor.html', context)
        
        # POST request - process form
        if request.method == 'POST':
            
            vendor_name = request.POST.get('vendor_name', '').strip()
            phone_no = request.POST.get('phone_no', '').strip()
            email = request.POST.get('email', '').strip()
            pincode = request.POST.get('pincode', '').strip()
            vendor_address = request.POST.get('vendor_address', '').strip()
            is_active = request.POST.get('is_active', '0')
            
            errors = {}
            
            # ---------------- VALIDATION ---------------- #
            
            if not vendor_name:
                errors['vendor_name'] = 'Vendor name is required.'
            elif len(vendor_name) < 3:
                errors['vendor_name'] = 'Vendor name must be at least 3 characters.'
            
            if not phone_no:
                errors['phone_no'] = 'Phone number is required.'
            elif not phone_no.isdigit() or len(phone_no) != 10:
                errors['phone_no'] = 'Please enter a valid 10-digit mobile number.'
            
            if email and '@' not in email:
                errors['email'] = 'Please enter a valid email address.'
            
            if not pincode:
                errors['pincode'] = 'Pincode is required.'
            else:
                # Check if pincode exists in delivery_pincodes
                if pincode not in pincode_dict:
                    errors['pincode'] = 'This pincode is not in our delivery network.'
            
            if errors:
                for error in errors.values():
                    messages.error(request, error)
                return redirect(f'{request.path}?vendor_id={encrypted_id}')
            
            # ---------------- UPDATE DATA ---------------- #
            
            try:
                with transaction.atomic():
                    
                    # Get area_name from pincode_dict
                    area_name = pincode_dict.get(pincode, '')
                    
                    # Update vendor
                    vendor.vendor_name = vendor_name
                    vendor.phone_no = phone_no
                    vendor.email = email if email else None
                    vendor.area_name = area_name
                    vendor.pincode = pincode
                    vendor.vendor_address = vendor_address
                    vendor.is_active = 1 if is_active == '1' else 0
                    
                    vendor.save()
                    
                messages.success(request, f"Vendor '{vendor_name}' updated successfully!")
                return redirect('vendor_list')
                
            except Exception as e:
                logger.exception(f"Error updating vendor: {str(e)}")
                messages.error(request, "Something went wrong while updating the vendor.")
                return redirect(f'{request.path}?vendor_id={encrypted_id}')
                
    except Exception as e:
        logger.exception(f"Unexpected error in edit_vendor: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('vendor_list')

@no_direct_access
@login_required
@transaction.atomic
def delete_vendor(request):
    """
    Delete vendor
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to perform this action.')
            return redirect('/')
        
        if request.method == 'POST':
            encrypted_vendor_id = request.POST.get('vendor_id')
            
            try:
                # Decrypt the vendor ID
                vendor_id = dec(str(encrypted_vendor_id))
                vendor = Vendor.objects.get(id=vendor_id)
                
                vendor_name = vendor.vendor_name
                vendor.delete()
                
                messages.success(request, f"Vendor '{vendor_name}' deleted successfully!")
                
            except Vendor.DoesNotExist:
                messages.error(request, 'Vendor not found.')
            except Exception as e:
                logger.exception(f"Error deleting vendor: {str(e)}")
                messages.error(request, 'Something went wrong while deleting the vendor.')
        
        return redirect('vendor_list')
        
    except Exception as e:
        logger.exception(f"Unexpected error in delete_vendor: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('vendor_list')
    
# occasion list

@no_direct_access
@login_required
@transaction.atomic
def occasion_list(request):
    """
    Display list of all occasions
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # Get all occasions
        occasions = Occasion.objects.all().order_by('-created_at')
        occasion_list = []
        for occ in occasions:
            occ.encrypted_id = enc(str(occ.id))
            occasion_list.append(occ)
        
        context = {
            'occasions': occasion_list,
        }
        return render(request, 'masters/occasion_list.html', context)
        
    except Exception as e:
        logger.exception(f"Error in occasion_list: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('admin_dashboard')

@no_direct_access
@login_required
@transaction.atomic
def add_occasion(request):
    """
    Add new occasion
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # GET request - display form
        if request.method == 'GET':
            context = {
                'form_data': request.session.pop('form_data', {}),
            }
            return render(request, 'masters/add_occasion.html', context)
        
        # POST request - process form
        if request.method == 'POST':
            
            name = request.POST.get('name', '').strip()
            icon = request.POST.get('icon', '').strip()
            is_active = request.POST.get('is_active', '0')
            
            errors = {}
            
            # ---------------- VALIDATION ---------------- #
            
            if not name:
                errors['name'] = 'Occasion name is required.'
            elif len(name) < 3:
                errors['name'] = 'Occasion name must be at least 3 characters.'
            else:
                # Check if occasion with same name already exists
                if Occasion.objects.filter(name__iexact=name).exists():
                    errors['name'] = 'An occasion with this name already exists.'
            
            if errors:
                # Store form data in session
                request.session['form_data'] = request.POST.dict()
                for error in errors.values():
                    messages.error(request, error)
                return redirect('add_occasion')
            
            # ---------------- SAVE DATA ---------------- #
            
            try:
                with transaction.atomic():
                    
                    # Generate slug from name
                    from django.utils.text import slugify
                    base_slug = slugify(name)
                    slug = base_slug
                    counter = 1
                    while Occasion.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1
                    
                    # Create occasion
                    occasion = Occasion.objects.create(
                        name=name,
                        slug=slug,
                        icon=icon if icon else None,
                        is_active=1 if is_active == '1' else 0
                    )
                    
                messages.success(request, f"Occasion '{name}' created successfully!")
                return redirect('occasion_list')
                
            except Exception as e:
                logger.exception(f"Error creating occasion: {str(e)}")
                messages.error(request, "Something went wrong while saving the occasion.")
                return redirect('add_occasion')
                
    except Exception as e:
        logger.exception(f"Unexpected error in add_occasion: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('add_occasion')

@no_direct_access
@login_required
def view_occasion(request):
    """
    View occasion details using encrypted ID from query parameter
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # Get encrypted ID from query parameter
        encrypted_id = request.GET.get('occasion_id')
        
        if not encrypted_id:
            messages.error(request, 'Occasion ID is required.')
            return redirect('occasion_list')
        
        # Decrypt the occasion ID
        decrypted_id = dec(str(encrypted_id))
        
        # Get occasion
        occasion = get_object_or_404(Occasion, id=decrypted_id)
        
        context = {
            'occasion': occasion,
            'encrypted_id': encrypted_id,
        }
        return render(request, 'masters/view_occasion.html', context)
        
    except Exception as e:
        logger.exception(f"Error in view_occasion: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('occasion_list')

@no_direct_access
@login_required
@transaction.atomic
def edit_occasion(request):
    """
    Edit occasion details using encrypted ID from query parameter
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # Get encrypted ID from query parameter
        encrypted_id = request.GET.get('occasion_id')
        
        if not encrypted_id:
            messages.error(request, 'Occasion ID is required.')
            return redirect('occasion_list')
        
        # Decrypt the occasion ID
        decrypted_id = dec(str(encrypted_id))
        
        # Get occasion
        occasion = get_object_or_404(Occasion, id=decrypted_id)
        
        # GET request - display form
        if request.method == 'GET':
            context = {
                'occasion': occasion,
                'encrypted_id': encrypted_id,
            }
            return render(request, 'masters/edit_occasion.html', context)
        
        # POST request - process form
        if request.method == 'POST':
            
            name = request.POST.get('name', '').strip()
            icon = request.POST.get('icon', '').strip()
            is_active = request.POST.get('is_active', '0')
            
            errors = {}
            
            # ---------------- VALIDATION ---------------- #
            
            if not name:
                errors['name'] = 'Occasion name is required.'
            elif len(name) < 3:
                errors['name'] = 'Occasion name must be at least 3 characters.'
            else:
                # Check if another occasion with same name exists (excluding current)
                if Occasion.objects.filter(name__iexact=name).exclude(id=decrypted_id).exists():
                    errors['name'] = 'An occasion with this name already exists.'
            
            if errors:
                for error in errors.values():
                    messages.error(request, error)
                return redirect(f'{request.path}?occasion_id={encrypted_id}')
            
            # ---------------- UPDATE DATA ---------------- #
            
            try:
                with transaction.atomic():
                    
                    # Update slug if name changed
                    from django.utils.text import slugify
                    if occasion.name != name:
                        base_slug = slugify(name)
                        slug = base_slug
                        counter = 1
                        while Occasion.objects.filter(slug=slug).exclude(id=decrypted_id).exists():
                            slug = f"{base_slug}-{counter}"
                            counter += 1
                        occasion.slug = slug
                    
                    # Update occasion
                    occasion.name = name
                    occasion.icon = icon if icon else None
                    occasion.is_active = 1 if is_active == '1' else 0
                    
                    occasion.save()
                    
                messages.success(request, f"Occasion '{name}' updated successfully!")
                return redirect('occasion_list')
                
            except Exception as e:
                logger.exception(f"Error updating occasion: {str(e)}")
                messages.error(request, "Something went wrong while updating the occasion.")
                return redirect(f'{request.path}?occasion_id={encrypted_id}')
                
    except Exception as e:
        logger.exception(f"Unexpected error in edit_occasion: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('occasion_list')

@no_direct_access
@login_required
@transaction.atomic
def delete_occasion(request):
    """
    Delete occasion
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to perform this action.')
            return redirect('/')
        
        if request.method == 'POST':
            encrypted_occasion_id = request.POST.get('occasion_id')
            
            if not encrypted_occasion_id:
                messages.error(request, 'Occasion ID is required.')
                return redirect('occasion_list')
            
            try:
                # Decrypt the occasion ID
                occasion_id = dec(str(encrypted_occasion_id))
                occasion = Occasion.objects.get(id=occasion_id)
                
                occasion_name = occasion.name
                occasion.delete()
                
                messages.success(request, f"Occasion '{occasion_name}' deleted successfully!")
                
            except Occasion.DoesNotExist:
                messages.error(request, 'Occasion not found.')
            except Exception as e:
                logger.exception(f"Error deleting occasion: {str(e)}")
                messages.error(request, 'Something went wrong while deleting the occasion.')
        
        return redirect('occasion_list')
        
    except Exception as e:
        logger.exception(f"Unexpected error in delete_occasion: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('occasion_list')

# user management
    
@no_direct_access
@login_required
@transaction.atomic
def user_list(request):
    """
    Display list of all users with filtering
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # Get filter parameters from request
        search_query = request.GET.get('search', '')
        role_filter = request.GET.get('role', '')
        status_filter = request.GET.get('status', '')
        
        # Base queryset
        users = CustomUser.objects.all().order_by('-date_joined')
        
        # Apply filters
        if search_query:
            users = users.filter(
                models.Q(full_name__icontains=search_query) |
                models.Q(email__icontains=search_query) |
                models.Q(phone__icontains=search_query) |
                models.Q(first_name__icontains=search_query) |
                models.Q(last_name__icontains=search_query)
            )
        
        if role_filter:
            users = users.filter(role_id=role_filter)
        
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
        
        # Add encrypted IDs
        user_list = []
        for user in users:
            user.encrypted_id = enc(str(user.id))
            user_list.append(user)
        
        # Get roles for filter dropdown
        roles = Roles.objects.all().order_by('role_name')
        
        context = {
            'users': user_list,
            'roles': roles,
            'search_query': search_query,
            'role_filter': role_filter,
            'status_filter': status_filter,
        }
        return render(request, 'masters/user_list.html', context)
        
    except Exception as e:
        logger.exception(f"Error in user_list: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('admin_dashboard')

@no_direct_access
@login_required
@transaction.atomic
def add_user(request):
    """
    Add new user
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # Get all roles for dropdown
        roles = Roles.objects.all().order_by('role_name')
        
        # GET request - display form
        if request.method == 'GET':
            context = {
                'roles': roles,
                'form_data': request.session.pop('form_data', {}),
            }
            return render(request, 'masters/add_user.html', context)
        
        # POST request - process form
        if request.method == 'POST':
            
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip().lower()
            phone = request.POST.get('phone', '').strip()
            role_id = request.POST.get('role_id', '').strip()
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')
            is_active = request.POST.get('is_active', '0')
            user_type = request.POST.get('user_type', 'guest')
            
            errors = {}
            
            # ---------------- VALIDATION ---------------- #
            
            # Name validation
            if not first_name:
                errors['first_name'] = 'First name is required.'
            
            # Email validation
            if not email:
                errors['email'] = 'Email address is required.'
            else:
                # Check if email already exists
                if CustomUser.objects.filter(email=email).exists():
                    errors['email'] = 'A user with this email already exists.'
            
            # Phone validation (optional but if provided, must be valid)
            if phone and (not phone.isdigit() or len(phone) not in [10, 12]):
                errors['phone'] = 'Please enter a valid phone number (10 digits).'
            
            # Role validation
            if not role_id:
                errors['role_id'] = 'Please select a role.'
            else:
                try:
                    role = Roles.objects.get(id=role_id)
                except Roles.DoesNotExist:
                    errors['role_id'] = 'Invalid role selected.'
            
            # Password validation
            if not password:
                errors['password'] = 'Password is required.'
            elif len(password) < 8:
                errors['password'] = 'Password must be at least 8 characters long.'
            elif not any(char.isdigit() for char in password):
                errors['password'] = 'Password must contain at least one number.'
            elif not any(char.isupper() for char in password):
                errors['password'] = 'Password must contain at least one uppercase letter.'
            elif not any(char.islower() for char in password):
                errors['password'] = 'Password must contain at least one lowercase letter.'
            elif not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in password):
                errors['password'] = 'Password must contain at least one special character.'
            
            # Confirm password
            if password != confirm_password:
                errors['confirm_password'] = 'Passwords do not match.'
            
            if errors:
                # Store form data in session
                request.session['form_data'] = request.POST.dict()
                for error in errors.values():
                    messages.error(request, error)
                return redirect('add_user')
            
            # ---------------- SAVE DATA ---------------- #
            
            try:
                with transaction.atomic():
                    
                    # Generate full name
                    full_name = f"{first_name} {last_name}".strip() if last_name else first_name
                    
                    # Create user
                    user = CustomUser.objects.create_user(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        full_name=full_name,
                        phone=phone if phone else None,
                        role_id=int(role_id),
                        user_type=user_type,
                        is_active=1 if is_active == '1' else 0,
                        is_staff=1 if user_type == 'admin' else 0,
                        first_time_login=1
                    )
                    
                    # Store password in PasswordStorage (if needed)
                    PasswordStorage.objects.create(
                        user=user,
                        password_text=password  # Note: This stores plain text - consider encrypting
                    )
                    
                messages.success(request, f"User '{email}' created successfully!")
                return redirect('user_list')
                
            except Exception as e:
                logger.exception(f"Error creating user: {str(e)}")
                messages.error(request, "Something went wrong while saving the user.")
                return redirect('add_user')
                
    except Exception as e:
        logger.exception(f"Unexpected error in add_user: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('add_user')

@no_direct_access
@login_required
def view_user(request):
    """
    View user details using encrypted ID from query parameter
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # Get encrypted ID from query parameter
        encrypted_id = request.GET.get('user_id')
        
        if not encrypted_id:
            messages.error(request, 'User ID is required.')
            return redirect('user_list')
        
        # Decrypt the user ID
        decrypted_id = dec(str(encrypted_id))
        
        # Get user
        user = get_object_or_404(CustomUser, id=decrypted_id)
        
        # Get user role
        role = None
        if user.role_id:
            try:
                role = Roles.objects.get(id=user.role_id)
            except Roles.DoesNotExist:
                pass
        
        # Get password storage (if needed)
        password_storage = PasswordStorage.objects.filter(user=user).first()
        
        context = {
            'user': user,
            'role': role,
            'password_storage': password_storage,
            'encrypted_id': encrypted_id,
        }
        return render(request, 'masters/view_user.html', context)
        
    except Exception as e:
        logger.exception(f"Error in view_user: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('user_list')

@no_direct_access
@login_required
@transaction.atomic
def edit_user(request):
    """
    Edit user details using encrypted ID from query parameter
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('/')
        
        # Get encrypted ID from query parameter
        encrypted_id = request.GET.get('user_id')
        
        if not encrypted_id:
            messages.error(request, 'User ID is required.')
            return redirect('user_list')
        
        # Decrypt the user ID
        decrypted_id = dec(str(encrypted_id))
        
        # Get user
        user = get_object_or_404(CustomUser, id=decrypted_id)
        
        # Get all roles for dropdown
        roles = Roles.objects.all().order_by('role_name')
        
        # GET request - display form
        if request.method == 'GET':
            context = {
                'user': user,
                'roles': roles,
                'encrypted_id': encrypted_id,
            }
            return render(request, 'masters/edit_user.html', context)
        
        # POST request - process form
        if request.method == 'POST':
            
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            role_id = request.POST.get('role_id', '').strip()
            is_active = request.POST.get('is_active', '0')
            user_type = request.POST.get('user_type', 'guest')
            change_password = request.POST.get('change_password', '0')
            new_password = request.POST.get('new_password', '')
            confirm_new_password = request.POST.get('confirm_new_password', '')
            
            errors = {}
            
            # ---------------- VALIDATION ---------------- #
            
            # Name validation
            if not first_name:
                errors['first_name'] = 'First name is required.'
            
            # Phone validation (optional but if provided, must be valid)
            if phone and (not phone.isdigit() or len(phone) not in [10, 12]):
                errors['phone'] = 'Please enter a valid phone number (10 digits).'
            
            # Role validation
            if not role_id:
                errors['role_id'] = 'Please select a role.'
            else:
                try:
                    role = Roles.objects.get(id=role_id)
                except Roles.DoesNotExist:
                    errors['role_id'] = 'Invalid role selected.'
            
            # Password validation (if changing password)
            if change_password == '1':
                if not new_password:
                    errors['new_password'] = 'New password is required.'
                elif len(new_password) < 8:
                    errors['new_password'] = 'Password must be at least 8 characters long.'
                elif not any(char.isdigit() for char in new_password):
                    errors['new_password'] = 'Password must contain at least one number.'
                elif not any(char.isupper() for char in new_password):
                    errors['new_password'] = 'Password must contain at least one uppercase letter.'
                elif not any(char.islower() for char in new_password):
                    errors['new_password'] = 'Password must contain at least one lowercase letter.'
                elif not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in new_password):
                    errors['new_password'] = 'Password must contain at least one special character.'
                
                # Confirm password
                if new_password != confirm_new_password:
                    errors['confirm_new_password'] = 'Passwords do not match.'
            
            if errors:
                for error in errors.values():
                    messages.error(request, error)
                return redirect(f'{request.path}?user_id={encrypted_id}')
            
            # ---------------- UPDATE DATA ---------------- #
            
            try:
                with transaction.atomic():
                    
                    # Generate full name
                    full_name = f"{first_name} {last_name}".strip() if last_name else first_name
                    
                    # Update user
                    user.first_name = first_name
                    user.last_name = last_name
                    user.full_name = full_name
                    user.phone = phone if phone else None
                    user.role_id = int(role_id)
                    user.user_type = user_type
                    user.is_active = 1 if is_active == '1' else 0
                    user.is_staff = 1 if user_type == 'admin' else 0
                    
                    # Update password if changed
                    if change_password == '1' and new_password:
                        user.set_password(new_password)
                        
                        # Update password in PasswordStorage
                        password_storage = PasswordStorage.objects.filter(user=user).first()
                        if password_storage:
                            password_storage.password_text = new_password
                            password_storage.save()
                        else:
                            PasswordStorage.objects.create(
                                user=user,
                                password_text=new_password
                            )
                    
                    user.save()
                    
                messages.success(request, f"User '{user.email}' updated successfully!")
                return redirect('user_list')
                
            except Exception as e:
                logger.exception(f"Error updating user: {str(e)}")
                messages.error(request, "Something went wrong while updating the user.")
                return redirect(f'{request.path}?user_id={encrypted_id}')
                
    except Exception as e:
        logger.exception(f"Unexpected error in edit_user: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('user_list')

@no_direct_access
@login_required
@transaction.atomic
def delete_user(request):
    """
    Delete user
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/')
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to perform this action.')
            return redirect('/')
        
        if request.method == 'POST':
            encrypted_user_id = request.POST.get('user_id')
            
            if not encrypted_user_id:
                messages.error(request, 'User ID is required.')
                return redirect('user_list')
            
            try:
                # Decrypt the user ID
                user_id = dec(str(encrypted_user_id))
                
                # Prevent deleting yourself
                if int(user_id) == request.user.id:
                    messages.error(request, 'You cannot delete your own account.')
                    return redirect('user_list')
                
                user = CustomUser.objects.get(id=user_id)
                
                # Prevent deleting superuser
                if user.is_superuser:
                    messages.error(request, 'Superuser cannot be deleted.')
                    return redirect('user_list')
                
                user_email = user.email
                user.delete()
                
                messages.success(request, f"User '{user_email}' deleted successfully!")
                
            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found.')
            except Exception as e:
                logger.exception(f"Error deleting user: {str(e)}")
                messages.error(request, 'Something went wrong while deleting the user.')
        
        return redirect('user_list')
        
    except Exception as e:
        logger.exception(f"Unexpected error in delete_user: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('user_list')

@no_direct_access
@login_required
@transaction.atomic
def toggle_user_status(request):
    """
    Toggle user active/inactive status
    Only accessible to Admin (role_id=1)
    """
    try:
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the dashboard.')
            return JsonResponse({'success': False, 'message': 'Authentication required'})
        
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to perform this action.')
            return JsonResponse({'success': False, 'message': 'Permission denied'})
        
        if request.method == 'POST':
            encrypted_user_id = request.POST.get('user_id')
            
            if not encrypted_user_id:
                return JsonResponse({'success': False, 'message': 'User ID is required.'})
            
            try:
                # Decrypt the user ID
                user_id = dec(str(encrypted_user_id))
                
                # Prevent toggling yourself
                if int(user_id) == request.user.id:
                    return JsonResponse({'success': False, 'message': 'You cannot change your own status.'})
                
                user = CustomUser.objects.get(id=user_id)
                
                # Prevent toggling superuser
                if user.is_superuser:
                    return JsonResponse({'success': False, 'message': 'Superuser status cannot be changed.'})
                
                # Toggle status
                user.is_active = not user.is_active
                user.save()
                
                status = "activated" if user.is_active else "deactivated"
                
                return JsonResponse({
                    'success': True, 
                    'message': f"User '{user.email}' {status} successfully!",
                    'is_active': user.is_active
                })
                
            except CustomUser.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'User not found.'})
            except Exception as e:
                logger.exception(f"Error toggling user status: {str(e)}")
                return JsonResponse({'success': False, 'message': 'Something went wrong.'})
        
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})
        
    except Exception as e:
        logger.exception(f"Unexpected error in toggle_user_status: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Something went wrong.'})
    
    