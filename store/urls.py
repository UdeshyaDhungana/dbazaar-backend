from django.urls import path
from rest_framework import routers
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

#url configuration
router = routers.DefaultRouter()
router.register('products', views.ProductsViewSet, basename='products')
router.register('collections', views.CollectionViewSet, basename='collections')

products_router = routers.NestedDefaultRouter(router, 'products', lookup='product')
products_router.register('reviews', views.ReviewViewSet, basename='product-reviews')

urlpatterns = router.urls + products_router.urls