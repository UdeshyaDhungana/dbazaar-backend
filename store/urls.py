from django.urls import path
from rest_framework import routers
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

#url configuration
router = routers.DefaultRouter()
router.register('collections', views.CollectionViewSet, basename='collections')
router.register('products', views.ProductsViewSet, basename='products')
router.register('customers', views.CustomerViewSet)


# router.register('carts', views.CartViewSet, basename='carts')

# products_router = routers.NestedDefaultRouter(router, 'products', lookup='product')
# products_router.register('reviews', views.SpeakViewSet, basename='product-reviews')

urlpatterns = router.urls # + products_router.urls