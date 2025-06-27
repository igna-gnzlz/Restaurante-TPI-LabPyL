from django.urls import path, include
from .views import OrderDetailView
from .views import (
    MenuListView,
    ProductDetailView,
    AddToOrderView,
    AddOneView,
    RemoveOneView,
    DeleteItemView,
    CancelOrderView,
    
)

app_name = 'menu_app'

urlpatterns = [
    path("", MenuListView.as_view(), name="menu"),
    path('my-order/', OrderDetailView.as_view(), name='order_detail'),
    path("<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),
    path('add-to-order/<slug:slug>/', AddToOrderView.as_view(), name='add_to_order'),
    path("accounts/", include("accounts_app.urls", namespace="accounts_app")),
    path('add_one/', AddOneView.as_view(), name='add_one'),
    path('remove_one/', RemoveOneView.as_view(), name='remove_one'),
    path('delete_item/', DeleteItemView.as_view(), name='delete_item'),
    path('cancel_order/', CancelOrderView.as_view(), name='cancel_order')
]