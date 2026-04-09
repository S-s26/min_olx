from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import customUser


class customUserForm(UserCreationForm):
    class Meta:
        model=customUser
        fields=['username','first_name','last_name','email','phone','address','password1','password2']
    
