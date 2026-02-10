"""
URL configuration for rose_and_roots project.

The `urlpatterns` list routes URLs to  For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from accounts.views import *

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),

    # Template views
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    
    # API endpoints
    path('api/login/', api_login, name='api_login'),
    path('api/register/', api_register, name='api_register'),
    path('api/logout/', api_logout, name='api_logout'),
]
