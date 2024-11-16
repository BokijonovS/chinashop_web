from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.conf import settings

# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
        verbose_name = 'Category'


class Size(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price = models.FloatField()
    sizes = models.ManyToManyField(Size, through='ProductSize')
    description = models.TextField()
    image = models.ImageField(upload_to='products/', null=True)

    def total_count(self):
        total = self.productsize_set.aggregate(total=Sum('count'))['total']
        return total if total else 0

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Products'
        verbose_name = 'Product'


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    count = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} - {self.size.name}"


class LikeDislike(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.CharField(max_length=100)
    is_like = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.product} {self.is_like}'

    class Meta:
        unique_together = ('user', 'product')


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    size = models.ForeignKey('ProductSize', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.size.size.name})"

    def save(self, *args, **kwargs):
        # Deduct stock when adding a new OrderItem
        if self.pk is None:
            self.size.count -= self.quantity
            if self.size.count < 0:
                raise ValueError(f"Insufficient stock for {self.size.size.name} of {self.product.name}.")
            self.size.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Restore stock when an OrderItem is deleted
        self.size.count += self.quantity
        self.size.save()
        super().delete(*args, **kwargs)


class Notification(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

