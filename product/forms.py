from django import forms
from django.forms import modelformset_factory
from .models import ProductImage, product

class ProductForm(forms.ModelForm):
    class Meta:
        model = product
        fields = ['title','price', 'category', 'subcategory','phone_number', 'address', 'description']

ProductImageFormSet = modelformset_factory(
    ProductImage,
    fields=('image',),
    extra=3,  # Change number as needed
    max_num=5
)
