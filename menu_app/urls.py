from django.urls import path, include
from .views import MenuListView, ProductDetailView, AddToOrderView

urlpatterns = [
    path("", MenuListView.as_view(), name="menu"),
    path("<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),
    path('add-to-order/<slug:slug>/', AddToOrderView.as_view(), name='add_to_order'),
    path("accounts/", include("accounts_app.urls", namespace="accounts_app")),
]
