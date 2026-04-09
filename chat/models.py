from django.db import models
from django.contrib.auth import get_user_model
from product.models import product
User=get_user_model()


# Create your models here.
class chatroom(models.Model):
    product = models.ForeignKey(product, on_delete=models.CASCADE)
    buyer=models.ForeignKey(User, on_delete=models.CASCADE,related_name='chat_buyer')
    seller=models.ForeignKey(User, on_delete=models.CASCADE,related_name='chat_seller')
    created_at=models.DateTimeField(auto_now_add=True)


    class Meta:
        unique_together=('buyer','seller','product')

    def __str__(self):
        return f"{self.buyer.username} - {self.seller.username} - {self.product.title}"
    


class message(models.Model):
    room=models.ForeignKey(chatroom, on_delete=models.CASCADE , related_name='message')
    sender=models.ForeignKey(User,on_delete=models.CASCADE)
    message=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}:{self.message[:30]}"