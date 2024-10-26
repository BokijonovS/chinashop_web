from rest_framework import serializers
from .models import Product, Category, LikeDislike, OrderItem, Order, Notification


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    liked_by_user = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'category', 'name', 'price', 'size', 'description', 'image', 'count', 'liked_by_user']
        read_only_fields = ['liked_by_user']

    def get_liked_by_user(self, obj):
        request = self.context.get('request')

        # Check if request exists and if the user is authenticated
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.username
            return LikeDislike.objects.filter(product=obj, user=user_id, is_like=True).exists()

        # If no authenticated user, return False (not liked by any user)
        return False


class LikeDislikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikeDislike
        fields = ['product', 'user', 'is_like']


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = OrderItem
        fields = ['product', 'size', 'count']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'created_at', 'updated_at', 'total_price', 'items']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'created_at']