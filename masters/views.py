from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import DatabaseError
import logging
from rose_and_roots.access_control import no_direct_access

logger = logging.getLogger(__name__)

no_direct_access
@login_required
def admin_dashboard(request):
    try:
        context = {
            "page_title": "Admin Dashboard"
        }

        return render(request, "masters/admin_dashboard.html", context)

    except Exception as e:
        logger.exception("Unexpected error in admin_dashboard")
        messages.error(request, "Something went wrong.")
        return render(request, "masters/admin_dashboard.html")
    
no_direct_access
@login_required
def dashboard(request):
    try:
        context = {
            "page_title": "Dashboard"
        }

        return render(request, "masters/dashboard.html", context)

    except Exception as e:
        logger.exception("Unexpected error in dashboard")
        messages.error(request, "Something went wrong.")
        return render(request, "masters/dashboard.html")