"""
E-Menum URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # API v1 endpoints will be added here
    # path('api/v1/', include('apps.core.urls')),
    # path('api/v1/menus/', include('apps.menu.urls')),
    # path('api/v1/orders/', include('apps.orders.urls')),
    # path('api/v1/subscriptions/', include('apps.subscriptions.urls')),
]
