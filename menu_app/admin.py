from django.contrib import admin
from .models import Product
#from models_copy import Booking, User


class MenuAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "price", "quantity")
    search_fields = ("name", "price")
    list_filter = ("price", "quantity")


admin.site.register(Product, MenuAdmin)
#admin.site.register(User)
#admin.site.register(Booking)
