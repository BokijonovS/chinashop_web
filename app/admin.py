from django.contrib import admin
from .models import Product, Category, Notification, Size

# Register your models here.

admin.site.register(Notification)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Size)
