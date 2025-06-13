from django.urls import path, include
from .views import HomeView, MenuListView, ProductDetailView, BookingListView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("menu/", MenuListView.as_view(), name="menu"),
    path("menu/<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
    path("accounts/", include("accounts_app.urls", namespace="accounts_app")),

]
