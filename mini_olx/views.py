from django.shortcuts import render
from product.models import product



def home(request):
    products = product.objects.all().prefetch_related('images')
    return render(request, 'home.html', {'products': products})
