from django.contrib import admin
from .models import Product, Category, Notification, Size, ProductSize, Order

# Register your models here.

admin.site.register(Notification)
admin.site.register(Category)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1  # Number of empty slots for new entries
    fields = ['id', 'size', 'count']  # Fields to display in the inline form


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", 'name']
    inlines = [ProductSizeInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'is_paid',)
    list_display_links = ("id", "user")
