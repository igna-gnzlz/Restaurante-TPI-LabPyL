from django.urls import path
from .views import MenuListView, ProductDetailView

urlpatterns = [
    path("", MenuListView.as_view(), name="menu"),
    path("<slug:slug>/", ProductDetailView.as_view(), name="product_detail")
]