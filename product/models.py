from django.db import models
from django.conf import settings
from django.db.models import Index, signals
from django.dispatch import receiver
from PIL import Image
import logging
import os

logger = logging.getLogger(__name__)


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
        ('other', 'Other'),
    ])
    brand = models.CharField(max_length=50, blank=True, default='Unknown')
    subcategory = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Indexes that back the homepage feed and category browse.
        # Composite (-created_at, id) gives an index-only scan for
        # LIMIT N pagination of the global feed.
        indexes = [
            Index(fields=['-created_at'], name='prod_created_idx'),
            Index(fields=['category', '-created_at'], name='prod_cat_created_idx'),
            Index(fields=['seller', '-created_at'], name='prod_seller_idx'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def cover_image(self):
        first = self.images.first()
        return first.image if first else None


class ProductImage(models.Model):
    product = models.ForeignKey(product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return self.product.title

    def _cloudinary_public_id(self):
        """Best-effort extraction of the Cloudinary public_id."""
        if not self.image:
            return None
        # django-cloudinary-storage stores the public_id in `.name`
        # (e.g. "media/products/abc123"). Fall back to URL parsing if a
        # different storage backend is ever wired in.
        name = getattr(self.image, 'name', None)
        if name:
            return name
        try:
            url = self.image.url
        except Exception:
            return None
        if 'cloudinary.com' not in url:
            return None
        # https://res.cloudinary.com/<cloud>/image/upload/<transforms>/<public_id>.<ext>
        tail = url.split('/upload/', 1)[-1]
        tail = tail.split('/', 1)[-1] if '/' in tail else tail
        return tail.rsplit('.', 1)[0]


# ----------------------------------------------------------------------
# Cloudinary cleanup signal
# ----------------------------------------------------------------------
# We hook post_delete on ProductImage because Django's queryset.delete()
# (which is what CASCADE uses internally) bypasses Model.delete().
# post_delete fires for *every* deletion path — single row, bulk, CASCADE.
#
# The instance passed to the signal is still in memory (the DB row is
# gone but the object lives on), so `instance._cloudinary_public_id()`
# works fine.
#
# Best-effort: if Cloudinary is unreachable the orphan file stays in
# our media bucket and we only log the warning. We never let a remote-
# API failure roll back the DB operation.
# ----------------------------------------------------------------------
@receiver(signals.post_delete, sender=ProductImage)
def _purge_cloudinary_file(sender, instance, **kwargs):
    pid = instance._cloudinary_public_id()
    if not pid:
        return
    try:
        import cloudinary.uploader
    except ImportError:
        logger.warning('cloudinary package not installed; skipping remote delete')
        return
    try:
        resp = cloudinary.uploader.destroy(pid, invalidate=True)
        if resp.get('result') not in ('ok', 'not found'):
            logger.warning('Cloudinary destroy returned: %s for %s', resp, pid)
    except Exception as exc:
        logger.warning('Cloudinary destroy failed for %s: %s', pid, exc)