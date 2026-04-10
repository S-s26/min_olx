from django.db import models
from django.conf import settings
from PIL import Image
import os

# Create your models here.
class product(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=[
        ('electronics', 'Electronics'),
        ('furniture', 'Furniture'),
        ('clothing', 'Clothing'),
        ('books', 'Books'),
        ('toys', 'Toys'),
        ('other', 'Other')
    ])
    brand= models.CharField(max_length=50, blank=True, default='Unknown')
    subcategory = models.CharField(max_length=50)
    address= models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)




class ProductImage(models.Model):
    product = models.ForeignKey(product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')

    
    # updated_at = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return self.product.title
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img_path = self.image.url
        img = Image.open(img_path)

        # --- STEP 3: Resize JPG/PNG ---
        if img.height > 800 or img.width > 800:
            output_size = (800, 800)
            img.thumbnail(output_size)
            img.save(img_path, optimize=True, quality=70)  # JPG/PNG compression

        # --- STEP 4: Save as WebP also ---
        filename, ext = os.path.splitext(img_path)
        webp_path = f"{filename}.webp"
        img.save(webp_path, "WEBP", quality=70)



