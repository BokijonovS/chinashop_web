from django.contrib import admin
from .models import Product, Category, Notification

# Register your models here.

admin.site.register(Notification)
admin.site.register(Product)
admin.site.register(Category)
