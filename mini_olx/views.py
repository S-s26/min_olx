from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.core.cache import cache
from django.db.models import Q


from product.models import product, ProductImage


# def home(request):
#     """Home feed: cached first page, indexed query, eager-loaded images.

#     For a 1k-user target we keep the home render under ~30 ms by:
#       * Prefetching the cover image alongside the product.
#       * Reading from Redis when possible (write-through bust on
#         add/delete product).
#       * Paginating client-side via ?page= so the rendered page never
#         returns more than DEFAULT_PAGE_SIZE rows.
#     """
#     page_num = request.GET.get('page', 1)
#     cache_key = f'home_feed:p{page_num}'

#     products = cache.get(cache_key)
#     if products is None:
#         qs = (
#             product.objects
#             .select_related('seller')
#             .prefetch_related(
#                 Prefetch('images', queryset=ProductImage.objects.only('id', 'image', 'product_id'))
#             )
#             .order_by('-created_at')
#         )
#         paginator = Paginator(qs, 24)
#         products = paginator.get_page(page_num)
#         # Cache for 2 minutes — short enough to feel fresh, long
#         # enough to absorb bursts on the homepage.
#         cache.set(cache_key, products, 120)

#     return render(request, 'home.html', {'products': products})


def home(request):
    page_num = request.GET.get('page', 1)
    
    # 1. User ka search query yahan se get karenge
    query = request.GET.get('q', '').strip()
    
    # 2. Agar user kuch search kar raha hai, toh alag cache key banayenge
    if query:
        cache_key = f'home_feed:q={query}:p{page_num}'
    else:
        cache_key = f'home_feed:p{page_num}'

    products = cache.get(cache_key)
    if products is None:
        qs = (
            product.objects
            .select_related('seller')
            .prefetch_related(
                Prefetch('images', queryset=ProductImage.objects.only('id', 'image', 'product_id'))
            )
            .order_by('-created_at')
        )
        
        # 3. Agar search word hai, toh products ko filter karo
        if query:
            qs = qs.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) | 
                Q(category__icontains=query) |
                Q(brand__icontains=query) |
                Q(address__icontains=query)
            )

        paginator = Paginator(qs, 24)
        products = paginator.get_page(page_num)
        # Cache for 2 minutes
        cache.set(cache_key, products, 120)

    return render(request, 'home.html', {'products': products})