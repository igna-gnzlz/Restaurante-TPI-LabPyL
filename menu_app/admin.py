from django.contrib import admin
from .models import Product


class MenuAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "price", "quantity")
    search_fields = ("name", "price")
    list_filter = ("price", "quantity")


admin.site.register(Product, MenuAdmin)
