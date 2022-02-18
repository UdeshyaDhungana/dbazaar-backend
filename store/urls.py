from django.urls import path
from rest_framework import routers
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

#url configuration
router = routers.DefaultRouter()
router.register('products', views.ProductsViewSet, basename='products')
router.register('collections', views.CollectionViewSet, basename='collections')
router.register('carts', views.CartViewSet, basename='carts')
router.register('customers', views.CustomerViewSet)

products_router = routers.NestedDefaultRouter(router, 'products', lookup='product')
products_router.register('reviews', views.SpeakViewSet, basename='product-reviews')
customers_router=routers.NestedDefaultRouter(router,'customers',lookup='customer')
customers_router.register('bids',views.BidViewSet,basename='customer-bids')


urlpatterns = router.urls + products_router.urls + customers_router.urls
