from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Product, Category, LikeDislike, OrderItem, Order, Notification, Size, ProductSize


class ProductSizeSerializer(serializers.ModelSerializer):
    size_name = serializers.CharField(source='size.name')  # Get size name from the related Size model
    is_available = serializers.SerializerMethodField()  # Add custom field for availability

    class Meta:
        model = ProductSize
        fields = ['size_name', 'count', 'is_available']

    def get_is_available(self, obj):
        return obj.count > 0  # True if count is greater than 0


class ProductSerializer(serializers.ModelSerializer):
    liked_by_user = serializers.SerializerMethodField()
    total_count = serializers.SerializerMethodField()
    sizes = ProductSizeSerializer(source='productsize_set', many=True)

    class Meta:
        model = Product
        fields = ['id', 'category', 'name', 'price', 'sizes', 'description', 'image', 'total_count', 'liked_by_user']
        read_only_fields = ['liked_by_user']

    def get_liked_by_user(self, obj):
        request = self.context.get('request')

        # Check if request exists and if the user is authenticated
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.username
            return LikeDislike.objects.filter(product=obj, user=user_id, is_like=True).exists()

        # If no authenticated user, return False (not liked by any user)
        return False

    def get_total_count(self, obj):
        return obj.total_count()


class CategorySerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)  # This will show products in each category

    class Meta:
        model = Category
        fields = ['id', 'name', 'products']


class LikeDislikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikeDislike
        fields = ['product', 'user', 'is_like']


class AddOrderItemSerializer(serializers.ModelSerializer):
    product = serializers.IntegerField()  # Product ID
    size = serializers.IntegerField()  # ProductSize ID
    quantity = serializers.IntegerField()

    class Meta:
        model = OrderItem
        fields = ['product', 'size', 'quantity']

    def validate(self, data):
        # Fetch the ProductSize object to validate stock
        try:
            size = ProductSize.objects.get(id=data['size'], product_id=data['product'])
        except ProductSize.DoesNotExist:
            raise serializers.ValidationError("Invalid size or product.")

        # **Fetch the latest stock value**
        if data['quantity'] > size.count:
            raise serializers.ValidationError(f"Only {size.count} items are available for this size.")
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        order, _ = Order.objects.get_or_create(user=user, is_paid=False)

        size = ProductSize.objects.get(id=validated_data['size'])

        # **Ensure you're working with the actual current stock**
        size.refresh_from_db()

        # Check if the order already has this product/size combination
        existing_item = OrderItem.objects.filter(order=order, product_id=validated_data['product'], size=size).first()

        if existing_item:
            # Update the quantity if the item already exists in the order
            existing_item.quantity += validated_data['quantity']

            # Validate stock again before saving
            if existing_item.quantity > size.count:
                raise serializers.ValidationError(f"Only {size.count} items are available for this size.")

            existing_item.save()
            return existing_item
        else:
            # Create a new OrderItem
            if validated_data['quantity'] > size.count:
                raise serializers.ValidationError(f"Only {size.count} items are available for this size.")

            return OrderItem.objects.create(
                order=order,
                product_id=validated_data['product'],
                size=size,
                quantity=validated_data['quantity']
            )




class RemoveOrderItemSerializer(serializers.Serializer):
    order_item_id = serializers.IntegerField()

    def validate_order_item_id(self, value):
        user = self.context['request'].user
        order_item = OrderItem.objects.filter(id=value, order__user=user, order__is_paid=False).first()

        if not order_item:
            raise serializers.ValidationError("OrderItem not found or not part of your active order.")
        return value

    def delete(self, validated_data):
        order_item_id = validated_data['order_item_id']
        order_item = OrderItem.objects.get(id=order_item_id)
        order_item.delete()
        return order_item


class UpdateOrderItemSerializer(serializers.Serializer):
    order_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField()

    def validate_order_item_id(self, value):
        user = self.context['request'].user
        order_item = OrderItem.objects.filter(id=value, order__user=user, order__is_paid=False).first()

        if not order_item:
            raise serializers.ValidationError("OrderItem not found or not part of your active order.")

        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def update(self, validated_data):
        order_item_id = validated_data['order_item_id']
        new_quantity = validated_data['quantity']

        order_item = OrderItem.objects.get(id=order_item_id)
        size = order_item.size

        # Validate stock availability
        if new_quantity > size.count + order_item.quantity:
            raise serializers.ValidationError(f"Only {size.count + order_item.quantity} items are available for this size.")

        # Update the OrderItem quantity
        order_item.quantity = new_quantity
        order_item.save()

        return order_item



class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    size_name = serializers.CharField(source='size.size.name')
    available_stock = serializers.IntegerField(source='size.count')
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['product_name', 'size_name', 'quantity', 'available_stock', 'total_price']

    def get_total_price(self, obj):
        # Assuming your OrderItem model has a `total_price` field based on quantity * product price
        return obj.quantity * obj.product.price


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'items', 'created_at', 'is_paid', 'total_price']



class NotificationSerializer(serializers.ModelSerializer):
    # Add the 'has_viewed' field which will be calculated dynamically
    has_viewed = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'created_at', 'viewed_by_user', 'has_viewed']

    # This method will return True if the current user has viewed the notification, else False
    def get_has_viewed(self, obj):
        user = self.context.get('request').user
        return user in obj.viewed_by_user.all()

