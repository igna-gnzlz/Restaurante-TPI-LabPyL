from django.contrib import admin
from django.urls import include, path
from menu_app.views import HomeView
from menu_app.views import TemplateView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    path("menu/", include(("menu_app.urls", "menu_app"), namespace="menu_app")),
    path("accounts/", include("accounts_app.urls", namespace="accounts_app")),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path("bookings/", include("bookings_app.urls", namespace="bookings_app"))
]
