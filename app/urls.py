from django.urls import path, include
from rest_framework import routers

from app import views

router = routers.DefaultRouter()
router.register(r'category', views.CategoryViewSet)
router.register(r'product', views.ProductViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path('login/', views.UserLoginView.as_view(), name='user_login'),

    path('products/like/<int:product_id>/', views.LikeProductView.as_view(), name='like_product'),
    path('liked-products/', views.LikedProductsView.as_view(), name='liked-products'),

    path('order/add/', views.add_order_item, name='add_order_item'),
    path('order/remove/', views.remove_order_item, name='remove_order_item'),

    path('order/', views.get_order, name='get_order'),
    path('order/items/', views.get_order_items, name='get_order_items'),

    path('notifications/', views.NotificationListView.as_view(), name='notifications'),

]
