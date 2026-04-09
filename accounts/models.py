from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class customUser(AbstractUser):
    email=models.EmailField(unique=True, max_length=254)
    phone=models.CharField(max_length=15,unique=True)
    address=models.CharField(max_length=254,blank=True)
    def __str__(self):
        return self.username