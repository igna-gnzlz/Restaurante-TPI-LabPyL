from django.contrib import admin
from .models import Product, Category, Order

class MenuAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "price", "quantity")
    search_fields = ("name", "price")
    list_filter = ("price", "quantity")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'isActive']
    list_filter = ['isActive']
    search_fields = ['name']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'category', 'price', 'quantity']
    list_filter = ['category']
    search_fields = ['name', 'description']
    
    # Campos adicionales para mejor organización
    fields = ['name', 'description', 'price', 'quantity', 'category', 'image']
    
    # Mostrar imagen en el admin
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 100px;" />'
        return "No image"
    image_preview.allow_tags = True
    image_preview.short_description = 'Preview'

