from django.urls import path, include
from rest_framework import routers

from app import views

router = routers.DefaultRouter()
router.register(r'products', views.ProductViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path('login/', views.UserLoginView.as_view(), name='user_login'),

    path('categories/<int:id>', views.CategoryProductListView.as_view(), name='category-products'),
    path('categories/', views.CategoryListView.as_view(), name='all-categories'),

    path('products/like/<int:product_id>/', views.LikeProductView.as_view(), name='like_product'),
    path('liked-products/', views.LikedProductsView.as_view(), name='liked-products'),

    path('order/add/', views.AddOrderItemView.as_view(), name='add_order_item'),
    path('order/remove/', views.RemoveOrderItemView.as_view(), name='remove_order_item'),
    path('order/update/', views.UpdateOrderItemView.as_view(), name='update_order_item'),

    path('order/active/', views.GetActiveOrderView.as_view(), name='get_active_order'),

    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notification/<int:notification_id>/', views.get_notification_and_mark_read, name='get_notification_and_mark_read'),

    # payment
    path("payme/", views.PaymeCallBackAPIView.as_view(), name='payment_callback'),
    path("payme/check-status", views.CheckPaymentStatusView.as_view(), name='update_payment_callback'),

]
