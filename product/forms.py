from django import forms
from django.forms import modelformset_factory
from .models import ProductImage, product


class ProductForm(forms.ModelForm):
    class Meta:
        model = product
        fields = [
            'title',
            'price',
            'category',
            'subcategory',
            'brand',
            'phone_number',
            'address',
            'description',
        ]
        widgets = {
            'title':        forms.TextInput(attrs={'class': 'molx-input', 'placeholder': 'e.g. iPhone 13, barely used'}),
            'price':        forms.NumberInput(attrs={'class': 'molx-input', 'min': '0', 'step': '0.01'}),
            'category':     forms.Select(attrs={'class': 'molx-select'}),
            'subcategory':  forms.TextInput(attrs={'class': 'molx-input', 'placeholder': 'e.g. smartphone'}),
            'brand':        forms.TextInput(attrs={'class': 'molx-input', 'placeholder': 'e.g. Apple'}),
            'phone_number': forms.TextInput(attrs={'class': 'molx-input', 'placeholder': 'optional, masked by default'}),
            'address':      forms.TextInput(attrs={'class': 'molx-input', 'placeholder': 'City, area'}),
            'description':  forms.Textarea(attrs={'class': 'molx-textarea', 'rows': 4, 'placeholder': 'Describe the condition, age, reason for selling…'}),
        }


ProductImageFormSet = modelformset_factory(
    ProductImage,
    fields=('image',),
    extra=3,
    max_num=5,
)