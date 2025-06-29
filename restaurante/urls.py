from django.contrib import admin
from django.urls import include, path
from menu_app.views import HomeView, MyOrdersView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    path("menu/", include(("menu_app.urls", "menu_app"), namespace="menu_app")),
    path("accounts/", include("accounts_app.urls", namespace="accounts_app")),
    path('my-orders/', MyOrdersView.as_view(), name='my_orders'),
    path("bookings/", include("bookings_app.urls", namespace="bookings_app"))
]
