from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import DatabaseError
import logging
from rose_and_roots.access_control import no_direct_access
from django.shortcuts import render, redirect

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
    
no_direct_access
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
        if not hasattr(request.user, 'role_id') or request.user.role_id != 1:
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
    
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
import logging
from accounts.models import CustomUser
from masters.models import Bouquet, BouquetImage, BouquetOccasion, Occasion, Vendor

logger = logging.getLogger(__name__)

@login_required
@transaction.atomic
def add_bouquet(request):
    """
    Add new bouquet with images and occasions
    Only accessible to Admin (role_id=1)
    """
    try:
        # Check if user is admin
        if request.user.role_id != 1:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        if request.method == 'GET':
            # Get all active occasions for dropdown
            occasions = Occasion.objects.filter(is_active=True).order_by('name')
            
            # Get all active vendors
            vendors = Vendor.objects.filter(is_active=True).order_by('vendor_name')
            
            context = {
                'page_title': 'Add Bouquet',
                'occasions': occasions,
                'vendors': vendors,
                'selected_occasions': [],  # Empty list for new form
                'form_data': request.POST if request.method == 'POST' else {}
            }
            return render(request, 'masters/add_bouquet.html', context)
        
        if request.method == 'POST':
            try:
                # Extract form data
                bouquet_name = request.POST.get('bouquet_name', '').strip()
                short_description = request.POST.get('short_description', '').strip()
                description = request.POST.get('description', '').strip()
                price = request.POST.get('price', 0)
                discount = request.POST.get('discount', 0) or 0
                vendor_id = request.POST.get('vendor')
                occasion_ids = request.POST.getlist('occasions')
                is_active = request.POST.get('is_active', 1)
                
                # Validation
                errors = {}
                
                if not bouquet_name:
                    errors['bouquet_name'] = 'Bouquet name is required.'
                
                if not short_description:
                    errors['short_description'] = 'Short description is required.'
                
                if not description:
                    errors['description'] = 'Full description is required.'
                
                if not price or float(price) <= 0:
                    errors['price'] = 'Valid price is required.'
                
                if not vendor_id:
                    errors['vendor'] = 'Please select a vendor.'
                
                if not occasion_ids:
                    errors['occasions'] = 'Please select at least one occasion.'
                
                if errors:
                    for field, error in errors.items():
                        messages.error(request, error)
                    
                    # Get data for form repopulation
                    occasions = Occasion.objects.filter(is_active=True).order_by('name')
                    vendors = Vendor.objects.filter(is_active=True).order_by('vendor_name')
                    
                    context = {
                        'page_title': 'Add Bouquet',
                        'occasions': occasions,
                        'vendors': vendors,
                        'form_data': request.POST,
                        'selected_occasions': occasion_ids  # Pass selected occasions
                    }
                    return render(request, 'masters/add_bouquet.html', context)
                
                # Create bouquet
                vendor = Vendor.objects.get(id=vendor_id)
                
                bouquet = Bouquet.objects.create(
                    bouquet_name=bouquet_name,
                    short_description=short_description,
                    description=description,
                    price=float(price),
                    discount=float(discount),
                    vendor=vendor,
                    is_active=bool(int(is_active)),
                    created_by=request.user.email or request.user.username,
                    updated_by=request.user.email or request.user.username
                )
                
                # Handle multiple image uploads
                images = request.FILES.getlist('bouquet_images')
                
                for index, image_file in enumerate(images):
                    is_primary = (index == 0)  # First image is primary
                    
                    BouquetImage.objects.create(
                        bouquet=bouquet,
                        image=image_file,
                        is_primary=is_primary,
                        created_by=request.user.email or request.user.username
                    )
                
                # Handle occasions
                for occasion_id in occasion_ids:
                    occasion = Occasion.objects.get(id=occasion_id)
                    BouquetOccasion.objects.create(
                        bouquet=bouquet,
                        occasion=occasion,
                        created_by=request.user.email or request.user.username
                    )
                
                messages.success(request, f'Bouquet "{bouquet_name}" created successfully!')
                return redirect('bouquet_list')
                
            except Vendor.DoesNotExist:
                messages.error(request, 'Selected vendor does not exist.')
            except Occasion.DoesNotExist:
                messages.error(request, 'Selected occasion does not exist.')
            except Exception as e:
                logger.exception(f"Error creating bouquet: {str(e)}")
                messages.error(request, 'Failed to create bouquet. Please try again.')
                
            # If error occurs, reload form with data
            occasions = Occasion.objects.filter(is_active=True).order_by('name')
            vendors = Vendor.objects.filter(is_active=True).order_by('vendor_name')
            
            context = {
                'page_title': 'Add Bouquet',
                'occasions': occasions,
                'vendors': vendors,
                'form_data': request.POST
            }
            return render(request, 'masters/add_bouquet.html', context)
            
    except Exception as e:
        logger.exception(f"Unexpected error in add_bouquet: {str(e)}")
        messages.error(request, 'Something went wrong. Please try again later.')
        return redirect('admin_dashboard')