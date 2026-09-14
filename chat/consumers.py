"""
Async WebSocket consumer that powers real-time chat between a buyer
and a seller for a given product chatroom.

Wire-protocol (JSON over a single WebSocket connection):
    client -> server:
        {"type": "chat_message", "message": "<text>"}
        {"type": "typing",        "is_typing": true|false}
        {"type": "read",          "last_id": <int>}        # optional

    server -> group (broadcast):
        {"type": "chat_message", "id": ..., "message": ..., "sender": <username>,
         "sender_id": <int>, "created_at": "<iso>"}
        {"type": "typing",        "username": ..., "is_typing": ...}
        {"type": "presence",      "online_users": [usernames...]}

Designed to scale: every consumer only joins one channel group
("chat_<room_id>") which is kept small (2 participants), so a 1k-user
deployment only ever runs <= 1k concurrent sockets, not 1k groups.
"""

import json
from datetime import datetime

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import chatroom, message
from activity.models import UserActivity


class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            # Reject unauthenticated connections; UI redirects to login.
            await self.close(code=4401)
            return

        self.room_id = int(self.scope['url_route']['kwargs']['room_id'])
        self.room_group_name = f'chat_{self.room_id}'

        # Authorisation: only the buyer or the seller of this room
        # may connect. Without this check, any logged-in user could
        # eavesdrop via WebSocket.
        if not await self._user_is_participant():
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Notify peers that someone just came online.
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'presence_event', 'username': self.user.username, 'online': True},
        )

    async def disconnect(self, close_code):
        # Leave group & tell the other side we left.
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'presence_event', 'username': self.user.username, 'online': False},
            )

    # ------------------------------------------------------------------
    # Receive from client
    # ------------------------------------------------------------------
    async def receive_json(self, content, **kwargs):
        msg_type = content.get('type')

        if msg_type == 'chat_message':
            text = (content.get('message') or '').strip()
            if not text:
                return
            saved = await self._save_message(text)
            if saved is None:
                return
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_event',
                    'id': saved['id'],
                    'message': saved['message'],
                    'sender': self.user.username,
                    'sender_id': self.user.id,
                    'created_at': saved['created_at'],
                },
            )

        elif msg_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_event',
                    'username': self.user.username,
                    'is_typing': bool(content.get('is_typing')),
                },
            )

    # ------------------------------------------------------------------
    # Group events -> send to client
    # ------------------------------------------------------------------
    async def chat_message_event(self, event):
        await self.send_json({
            'type': 'chat_message',
            'id': event['id'],
            'message': event['message'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'created_at': event['created_at'],
        })

    async def typing_event(self, event):
        if event['username'] == self.user.username:
            return  # don't echo our own typing status
        await self.send_json({
            'type': 'typing',
            'username': event['username'],
            'is_typing': event['is_typing'],
        })

    async def presence_event(self, event):
        await self.send_json({
            'type': 'presence',
            'username': event['username'],
            'online': event['online'],
        })

    # ------------------------------------------------------------------
    # DB helpers (sync ORM wrapped for async)
    # ------------------------------------------------------------------
    @database_sync_to_async
    def _user_is_participant(self):
        try:
            room = chatroom.objects.only('buyer_id', 'seller_id').get(id=self.room_id)
        except chatroom.DoesNotExist:
            return False
        return self.user.id in (room.buyer_id, room.seller_id)

    @database_sync_to_async
    def _save_message(self, text):
        try:
            room = chatroom.objects.get(id=self.room_id)
        except chatroom.DoesNotExist:
            return None
        if self.user.id not in (room.buyer_id, room.seller_id):
            return None
        msg = message.objects.create(room=room, sender=self.user, message=text)
        
        # [OLD CODE - Yahan room.save() missing tha, jisse chat list mein sorting galat ho rahi thi]
        # Puraana code bas yahi tha, message banne ke baad room update nahi hota tha.
        
        # [NEW CODE - Added so that chatroom's updated_at timestamp changes on new message]
        room.save(update_fields=['updated_at'])
        # My-activity entry — fire-and-forget so the WS round-trip
        # stays cheap (one extra INSERT, indexed query).
        UserActivity.record(
            self.user, UserActivity.EVENT_CHAT_SEND,
            title=f'Messaged about “{room.product.title}”',
            detail=text[:80],
        )
        return {
            'id': msg.id,
            'message': msg.message,
            'created_at': msg.created_at.isoformat(),
        }
