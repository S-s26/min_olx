from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import Prefetch
from django.core.paginator import Paginator

from activity.models import UserActivity

from .forms import ProductForm, ProductImageFormSet
from .models import ProductImage, product


PRODUCT_FEED_KEY = 'home_products_v1'
PRODUCT_FEED_TTL = 120  # seconds


def _bust_feed_cache():
    cache.delete(PRODUCT_FEED_KEY)


@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        formset = ProductImageFormSet(
            request.POST, request.FILES, queryset=ProductImage.objects.none()
        )
        if form.is_valid() and formset.is_valid():
            new_product = form.save(commit=False)
            new_product.seller = request.user
            new_product.save()
            for img_form in formset.cleaned_data:
                if img_form:
                    ProductImage.objects.create(product=new_product, image=img_form['image'])
            _bust_feed_cache()
            UserActivity.record(
                request.user, UserActivity.EVENT_POST,
                title=f'Posted “{new_product.title}”',
                detail=f'₹{new_product.price}',
            )
            return redirect('home')
    else:
        form = ProductForm()
        formset = ProductImageFormSet(queryset=ProductImage.objects.none())
    return render(request, 'add_product.html', {'form': form, 'formset': formset})


def product_detail(request, id):
    product_de = get_object_or_404(
        product.objects.select_related('seller').prefetch_related('images'),
        id=id,
    )
    return render(request, 'product_detail.html', {'product': product_de})


@login_required
def my_products(request):
    products = (
        product.objects
        .filter(seller=request.user)
        .prefetch_related('images')
        .order_by('-created_at')
    )
    return render(request, 'my_products.html', {'products': products})


@login_required
def delete_product(request, id):
    qs = product.objects.filter(id=id, seller=request.user)
    if qs.exists():
        title = qs.first().title
        qs.delete()
        _bust_feed_cache()
        UserActivity.record(
            request.user, UserActivity.EVENT_DELETE,
            title=f'Deleted “{title}”',
        )
    return redirect('my_products')
