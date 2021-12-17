from django.contrib import admin, messages
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from . import models


#Custom filter
#inventory filter for products
class InventoryFilter(admin.SimpleListFilter):
    title = 'inventory'
    parameter_name = 'inventory'

    def lookups(self, request, model_admin):
        return [('<10', 'Low')]

    def queryset(self, request, queryset):
        if self.value() == '<10':
            return queryset.filter(inventory__lt=10)


@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ['name', 'product_count']
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
            product_count=Count('product'))


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    actions = ['clear_inventory']
    list_select_related = ['collection']
    list_display = [
        'title', 'unit_price', 'inventory_status', 'collection_name'
    ]
    list_editable = ['unit_price']
    list_per_page = 20
    list_filter = ['collection', 'last_update', InventoryFilter]
    search_fields = ['title']

    @admin.display(ordering='inventory')
    def inventory_status(self, product):
        return 'Low' if (product.inventory < 10) else 'OK'

    def collection_name(self, product):
        return product.collection.name

    @admin.action(description='Clear Inventory')
    def clear_inventory(self, request, queryset):
        updated_count = queryset.update(inventory=0)
        self.message_user(
            request, f'{updated_count} products were successfully updated',
            'success')

    # forms customization
    # fields = ['title', 'slug'] #bad
    prepopulated_fields = {
        'slug': ['title']
    }
    autocomplete_fields = ['collection']

@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'membership']
    list_editable = ['membership']
    list_per_page = 20
    search_fields = ['first_name__istartswith', 'last_name__istartswith']

    def full_name(self, customer):
        return customer.first_name + ' ' + customer.last_name


class OrderItemInline(admin.TabularInline):
    model = models.OrderItem
    autocomplete_fields = ['product']
    extra = 0
    min_num = 1
    max_num = 10

@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer', 'placed_at', 'payment_status']
    autocomplete_fields = ['customer']
    inlines = [OrderItemInline]
    search_fields = ['customer__first_name__istartswith', 'customer__last_name__istartswith']