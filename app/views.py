from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from .serializers import CategorySerializer, ProductSerializer, OrderItemSerializer, OrderSerializer, \
    NotificationSerializer
from .models import Product, LikeDislike, Category, Notification, Order, OrderItem

from rest_framework import status, viewsets, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

# Create your views here.


class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        userid = request.query_params.get('userid')

        if userid:
            user, created = User.objects.get_or_create(username=userid)

            if user:
                login(request, user)
                return Response({'message': f'Logged in as {userid}'}, status=200)

        # If userid is not provided or login fails
        return Response({'message': 'Login failed'}, status=400)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.order_by("?")
    serializer_class = ProductSerializer


class CategoryProductListView(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'id'


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class LikeProductView(APIView):
    def post(self, request, product_id):
        userid = request.user.username

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        like, created = LikeDislike.objects.get_or_create(product=product, user=userid)

        if not created:
            like.is_like = not like.is_like
            like.save()

            if like.is_like:
                return Response({"message": "Product liked!"}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Product unliked!"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Product liked!"}, status=status.HTTP_201_CREATED)


class LikedProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        user_id = self.request.user.username
        return Product.objects.filter(likedislike__user=user_id, likedislike__is_like=True)

# views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_order_item(request):
    user = request.user
    product_id = request.query_params.get('productid')
    size = request.query_params.get('product-size')

    product = Product.objects.get(id=product_id)

    order, created = Order.objects.get_or_create(user=user)

    order_item, item_created = OrderItem.objects.get_or_create(
        order=order, product=product, size=size,
        defaults={'count': 1}
    )

    if product.count < order_item.count:
        return Response({"error": "Not enough products in stock"}, status=status.HTTP_400_BAD_REQUEST)

    if not item_created:
        if product.count < order_item.count + order_item.count:
            return Response({"error": "Not enough products in stock"}, status=status.HTTP_400_BAD_REQUEST)
        order_item.count += order_item.count
        order_item.save()

    product.count -= order_item.count
    product.save()

    order.calculate_total_price()

    return Response({"message": "Order item added successfully"}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_order_item(request):
    user = request.user
    product_id = request.query_params.get('productid')
    size = request.query_params.get('product-size')

    product = get_object_or_404(Product, id=product_id)
    order = get_object_or_404(Order, user=user)

    order_item = get_object_or_404(OrderItem, order=order, product=product, size=size)

    product.count += 1
    product.save()

    order_item.count -= 1

    if order_item.count <= 0:
        order_item.delete()
    else:
        order_item.save()

    if not order.items.exists():
        order.delete()
    else:
        order.calculate_total_price()

    return Response({"message": "Removed 1 item from the order"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order_items(request):

    user = request.user
    if not user or user.is_anonymous:
        return Response({"detail": "Authentication credentials were not provided."},
                        status=status.HTTP_401_UNAUTHORIZED)

    # Fetch the user's order
    order = Order.objects.filter(user=user).first()

    if not order:
        return Response({"message": "No order found for this user"}, status=status.HTTP_404_NOT_FOUND)

    order_items = OrderItem.objects.filter(order=order)

    serializer = OrderItemSerializer(order_items, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)

# views.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order(request):

    user = request.user
    if not user:
        return Response({"detail": "Authentication credentials were not provided."}, status=401)

    order = Order.objects.filter(user=user).first()
    if not order:
        return Response({"message": "No order found for this user"}, status=404)

    serializer = OrderSerializer(order)
    return Response(serializer.data, status=200)


class NotificationListView(generics.ListAPIView):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]


