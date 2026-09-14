from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Index
from product.models import product

User = get_user_model()


class chatroom(models.Model):
    product = models.ForeignKey(
        product, on_delete=models.CASCADE, related_name='chatrooms'
    )
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='chat_buyer'
    )
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='chat_seller'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('buyer', 'seller', 'product')
        indexes = [
            # Speeds up "list conversations for user X, newest first".
            Index(fields=['buyer', '-updated_at'],  name='chat_room_buyer_idx'),
            Index(fields=['seller', '-updated_at'], name='chat_room_seller_idx'),
        ]

    def __str__(self):
        return f"{self.buyer.username} - {self.seller.username} - {self.product.title}"

    @property
    def last_message(self):
        return self.message.order_by('-created_at').first()

    def other_user(self, me):
        return self.seller if me.id == self.buyer_id else self.buyer


class message(models.Model):
    room = models.ForeignKey(
        chatroom, on_delete=models.CASCADE, related_name='message'
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            # Used by last_message property and "load history newest first".
            Index(fields=['room', '-created_at'], name='chat_msg_room_idx'),
        ]
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}:{self.message[:30]}"