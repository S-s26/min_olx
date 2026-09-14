from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import customUser


class customUserForm(UserCreationForm):
    class Meta:
        model = customUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'address', 'password1', 'password2']
        widgets = {
            'username':   forms.TextInput(attrs={'class': 'molx-input'}),
            'first_name': forms.TextInput(attrs={'class': 'molx-input'}),
            'last_name':  forms.TextInput(attrs={'class': 'molx-input'}),
            'email':      forms.EmailInput(attrs={'class': 'molx-input'}),
            'phone':      forms.TextInput(attrs={'class': 'molx-input'}),
            'address':    forms.TextInput(attrs={'class': 'molx-input'}),
        }