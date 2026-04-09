from django.contrib import admin
from product.models import product, ProductImage

# Register your models here.

class ProductImageAdmin(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image',)
    readonly_fields = ('image',)

    def has_add_permission(self, request, obj=None):

        return True
    

    def has_delete_permission(self, request, obj=None):
        return True





@admin.register(product)
class ProductAdmin(admin.ModelAdmin):
     inlines = [ProductImageAdmin]
     model = product
     list_display = ('title', 'seller', 'price', 'category','brand', 'subcategory','phone_number', 'created_at', 'address','description')
     search_fields = ('title', 'description', 'category', 'subcategory','brand')
     list_filter = ('category', 'created_at','brand')
     ordering = ('-created_at',)
    
     def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('seller')

