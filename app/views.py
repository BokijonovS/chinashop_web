from decimal import Decimal

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .serializers import CategorySerializer, ProductSerializer, \
    NotificationSerializer, AddOrderItemSerializer, RemoveOrderItemSerializer, UpdateOrderItemSerializer, \
    OrderSerializer, OrderItemSerializer
from .models import Product, LikeDislike, Category, Notification, Order, OrderItem, ProductSize

from rest_framework import status, viewsets, generics, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from payme.views import PaymeWebHookAPIView
from payme.models import PaymeTransactions
from payme import Payme

from webproject import settings


class UserLoginView(APIView):
    permission_classes = [AllowAny]

    #to use id: http://127.0.0.1:8000/api/login/?tg-id=123456&name=sanatbek&p-n=+998882041004&p-n2=+998330640131

    def get(self, request):
        telegram_id = request.GET.get('tg-id')


        if telegram_id:
            try:
                user = User.objects.get(username=telegram_id)
                status = True
            except:
                status = False

            if status:
                login(request, user)

                # Generate or retrieve the token for the user
                token, created = Token.objects.get_or_create(user=user)

                # Send the token in the response header
                response = Response({'message': f'Logged in as {telegram_id}'}, status=200)
                response['Authorization'] = f'Token {token.key}'  # Add the token to the headers
                print(token)
                return response

        return Response({'message': 'Login failed'}, status=400)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.order_by("?")
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class CategoryProductListView(generics.RetrieveAPIView):
    queryset = Category.objects.prefetch_related('products')  # Use prefetch_related for performance
    serializer_class = CategorySerializer  # Use an updated serializer
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
                return Response({"liked": True}, status=status.HTTP_200_OK)
            else:
                return Response({"liked": False}, status=status.HTTP_200_OK)
        else:
            return Response({"liked": True}, status=status.HTTP_201_CREATED)


class LikedProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        user_id = self.request.user.username
        return Product.objects.filter(likedislike__user=user_id, likedislike__is_like=True)


class AddOrderItemView(APIView):
    def post(self, request):
        user = request.user
        product_id = request.data.get('product_id')
        size_id = request.data.get('size_id')
        quantity = int(request.data.get('quantity', 1))  # Default to 1 if not provided

        try:
            # Get the product and size
            product = Product.objects.get(id=product_id)
            size = ProductSize.objects.get(id=size_id)

            # Check if the requested quantity is available in stock
            if quantity > size.count:
                print(quantity)
                print(size.size, size.count)
                return Response(
                    {"message": "Not enough stock to add this quantity.MF"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get or create an active (unpaid) order for the user
            order, created = Order.objects.get_or_create(user=user, is_paid=False)

            # Check if the item already exists in the order
            existing_item = OrderItem.objects.filter(order=order, product=product, size=size).first()

            if existing_item:
                # Update the quantity for the existing item
                existing_item.quantity += quantity
                existing_item.clean()  # Validate stock availability
                existing_item.save()

                return Response(OrderItemSerializer(existing_item).data, status=status.HTTP_200_OK)

            else:
                # Create a new OrderItem if it doesn't exist
                new_order_item = OrderItem.objects.create(
                    order=order, product=product, size=size, quantity=quantity
                )

                return Response(OrderItemSerializer(new_order_item).data, status=status.HTTP_201_CREATED)


        except Product.DoesNotExist:
            return Response({"message": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except ProductSize.DoesNotExist:
            return Response({"message": "Size not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RemoveOrderItemView(APIView):
    def delete(self, request):
        serializer = RemoveOrderItemSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.delete(serializer.validated_data)
            return Response({"message": "OrderItem removed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateOrderItemView(APIView):
    def patch(self, request):
        serializer = UpdateOrderItemSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            order_item = serializer.update(serializer.validated_data)
            return Response({
                "message": "OrderItem updated successfully.",
                "order_item": {
                    "product": order_item.product.name,
                    "size": order_item.size.size.name,
                    "quantity": order_item.quantity
                }
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


payme = Payme(payme_id=settings.PAYME_ID)


class GetActiveOrderView(APIView):
    def get(self, request):
        user = request.user
        user_id = user.username

        # Fetch the active (not paid) order for the user
        try:
            order = Order.objects.get(user=user, is_paid=False)
        except Order.DoesNotExist:
            return Response({"message": "No active order found."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the order data
        serializer = OrderSerializer(order)
        result = {
            'order': serializer.data,
        }
        # price_in_tiyins = Decimal(serializer.data['total_price']) * Decimal('100')
        payment_link = payme.initializer.generate_pay_link(
            id=serializer.data['id'],
            amount=serializer.data['total_price'],
            return_url=f'https://darkslied.pythonanywhere.com/api/login?tg-id={user_id}&name={user.first_name}&p-n={user.last_name}&p-n2={user.email}'  #should be changed after hosting
        )
        result['payment_link'] = payment_link
        return Response(result, status=status.HTTP_200_OK)


class NotificationListView(generics.ListAPIView):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]


class PaymeCallBackAPIView(PaymeWebHookAPIView):
    permission_classes = [AllowAny]

    def handle_created_payment(self, params, result, *args, **kwargs):
        """
        Handle the successful payment. You can override this method
        """
        print(f"Transaction created for this params: {params} and cr_result: {result}")

    def handle_successfully_payment(self, params, result, *args, **kwargs):
        """
        Handle the successful payment. You can override this method
        """
        transaction = PaymeTransactions.get_by_transaction_id(
            transaction_id=params['id']
        )
        order = Order.objects.get(id=transaction.account.id)
        OrderItem.deduct_stock(order)  #this funtion deducts the stock and removes paid items and also marks the order as paid

        print(f"Transaction successfully performed for this params: {params} and performed_result: {result}")

    def handle_cancelled_payment(self, params, result, *args, **kwargs):
        """
        Handle the cancelled payment. You can override this method
        """
        transaction = PaymeTransactions.get_by_transaction_id(
            transaction_id=params['id']
        )
        order = Order.objects.get(id=transaction.account.id)
        OrderItem.restore_stock(order)  #this function will undo all the works deduct_stock() did

        print(f"Transaction cancelled for this params: {params} and cancelled_result: {result}")
