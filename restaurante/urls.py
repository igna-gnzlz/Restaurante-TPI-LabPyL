from django.contrib import admin
from django.urls import include, path
from menu_app.views import HomeView, MakeOrderView, ConfirmOrderView, DecrementFromCartView, DeleteFromCartView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    path("menu/", include(("menu_app.urls", "menu_app"), namespace="menu_app")),
    path('make_order/', MakeOrderView.as_view(), name='make_order'),
    path('decrement-from-cart/<int:pk>/', DecrementFromCartView.as_view(), name='decrement_from_cart'),
    path('delete-from-cart/<int:pk>/', DeleteFromCartView.as_view(), name='delete_from_cart'),
    path('confirm-order/', ConfirmOrderView.as_view(), name='confirm_order'),
    path("accounts/", include("accounts_app.urls", namespace="accounts_app")),
    path("bookings/", include("bookings_app.urls", namespace="bookings_app"))
]
