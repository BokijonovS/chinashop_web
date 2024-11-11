from django.contrib.auth.models import User
from django.db import models

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
    sizes = models.ManyToManyField(Size, related_name='products')
    description = models.TextField()
    image = models.ImageField(upload_to='products/', null=True)
    count = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Products'
        verbose_name = 'Product'


class LikeDislike(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.CharField(max_length=100)
    is_like = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.product} {self.is_like}'

    class Meta:
        unique_together = ('user', 'product')


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def calculate_total_price(self):
        # Recalculate total price by summing each OrderItem's total (product price * quantity)
        total = sum(item.product.price * item.count for item in self.items.all())
        self.total_price = total
        self.save()

    def __str__(self):
        return f'Order {self.id} by {self.user.username}'


# OrderItem Model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=10)
    count = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.quantity} of {self.product.name} (Size: {self.size})'


class Notification(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
