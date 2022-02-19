from django.contrib import admin, messages
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from . import models

@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ['title', 'product_count']
    search_fields = ['title']

    def product_count(self, collection):
        return format_html('<a href={}>{}</a>',\
            reverse('admin:store_product_changelist')
            + '?'\
            + urlencode({
                'collection__id': str(collection.id)
            }), collection.product_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            product_count=Count('products'))


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_select_related = ['collection']
    list_display = [
        'title', 'unit_price', 'collection_name'
    ]
    list_editable = ['unit_price']
    list_per_page = 20
    list_filter = ['collection', 'last_update']
    search_fields = ['title']

    def collection_name(self, product):
        return product.collection.title

@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', ]
    list_per_page = 20
    search_fields = ['first_name__istartswith', 'last_name__istartswith']

    def full_name(self, customer):
        return customer.user.first_name + ' ' + customer.user.last_name