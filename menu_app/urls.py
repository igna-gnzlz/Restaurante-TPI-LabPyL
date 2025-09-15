from django.urls import path, include
from menu_app.views import (
    MenuListView,
    ProductDetailView,
    AddToOrderView,
    MakeRatingView,
    AddComboToOrderView,
    RemoveComboFromCartView,
    DecrementFromCartView,

)

app_name = 'menu_app'

urlpatterns = [
    path("", MenuListView.as_view(), name="menu"),
    path("<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
    path('add-to-order/<int:pk>/', AddToOrderView.as_view(), name='add_to_order'),
    path("accounts/", include("accounts_app.urls", namespace="accounts_app")),
    path("make_rating/<int:product_id>/", MakeRatingView.as_view(), name="make_rating"),
    path('add-combo/<int:pk>/', AddComboToOrderView.as_view(), name='add_combo_to_order'),
    path('remove-combo/<int:pk>/', RemoveComboFromCartView.as_view(), name='remove_combo_from_cart'),
    path('decrement-from-cart/<int:pk>/', DecrementFromCartView.as_view(), name='decrement_from_cart'),
]
