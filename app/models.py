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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    @property
    def total_price(self):
        return sum(item.quantity * item.product.price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    size = models.ForeignKey('ProductSize', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.size.size.name})"

    def clean(self):
        """
        Validate that there's enough stock for the specified size and quantity.
        """
        if self.quantity > self.size.count:
            raise ValueError(
                f"Not enough stock for {self.size.size.name} of {self.product.name}. "
                f"Only {self.size.count} items available."
            )

    def save(self, *args, **kwargs):
        """
        Validate stock but don't modify it yet.
        """
        self.clean()  # Ensure stock validation
        super().save(*args, **kwargs)

    @staticmethod
    def deduct_stock(order):
        """
        Deduct stock for all items in the given order. Call this after payment is successful.
        """
        if order.is_paid:
            raise ValueError("Stock already deducted for this order.")

        for item in order.items.all():
            if item.quantity > item.size.count:
                raise ValueError(
                    f"Not enough stock for {item.size.size.name} of {item.product.name}."
                )
            item.size.count -= item.quantity
            item.size.save()
        order.is_paid = True  # Mark the order as paid
        order.save()

    @staticmethod
    def restore_stock(order):
        """
        Restore stock for all items in the given order. Call this if payment is canceled.
        """
        # if not order.is_paid:
        #     raise ValueError("Stock has not been deducted for this order.")

        for item in order.items.all():
            # Restore stock for each item
            item.size.count += item.quantity
            item.size.save()
        order.is_paid = False  # Mark the order as unpaid
        order.save()


class Notification(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

