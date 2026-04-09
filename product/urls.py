from django.urls import path
from product import views



urlpatterns = [
    path('add/', views.add_product, name='add_product'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('my-products/', views.my_products, name='my_products'),
    path('delete/<int:id>', views.delete_product, name='delete_product'),

    # Add more paths as needed for other product-related views
]
