from django.urls import path, include
from .views import (
    MenuListView,
    ProductDetailView,
    AddToOrderView,
)

app_name = 'menu_app'

urlpatterns = [
    path("", MenuListView.as_view(), name="menu"),
    path("<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
    path('add-to-order/<int:pk>/', AddToOrderView.as_view(), name='add_to_order'),
    path("accounts/", include("accounts_app.urls", namespace="accounts_app")),
]
