from django.urls import path
from rest_framework import routers
from . import views
from rest_framework_nested import routers

#url configuration
router = routers.DefaultRouter()
router.register('collections', views.CollectionViewSet, basename='collections')
router.register('products', views.ProductsViewSet, basename='products')
router.register('customers', views.CustomerViewSet)


# router.register('carts', views.CartViewSet, basename='carts')

products_router = routers.NestedDefaultRouter(router, 'products', lookup='product')
products_router.register('comments', views.CommentViewSet, basename='product-comment')
products_router.register('bids', views.BidViewSet, basename='product-bid')

urlpatterns = router.urls + products_router.urls