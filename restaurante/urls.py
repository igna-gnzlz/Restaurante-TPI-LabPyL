"""
URL configuration for restaurante project.

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
from django.urls import include, path
from menu_app.views import HomeView
from menu_app.views import OrderDetailView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    path("menu/", include(("menu_app.urls", "menu_app"), namespace="menu_app")),
    path("accounts/", include("accounts_app.urls", namespace="accounts_app")),
    path('bookings/', include('bookings_app.urls')),
    path('my-order/', OrderDetailView.as_view(), name='order_detail'),
    
]
