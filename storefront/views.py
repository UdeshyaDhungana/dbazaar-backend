from django.shortcuts import render
from django.db.models import Value
from django.db.models.functions import Concat
from store.models import Product, Customer
# Create your views here.

def say_hello(request):

    qs = Customer.objects.annotate(full_name=Concat('first_name', Value(' '), 'last_name'))

    return render(request, 'hello.html', {'name': 'Udeshya', 'products': list(qs)})