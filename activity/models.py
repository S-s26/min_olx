from django.db import models
from django.conf import settings
from django.db.models import Index


class UserActivity(models.Model):
    """A single event in a user's own activity timeline.

    Visible only to the user that owns it (no admin oversight, no
    security review). Designed for the "My activity" page where the
    user can see *what they've done* recently.
    """

    EVENT_SIGNUP     = 'signup'
    EVENT_LOGIN      = 'login'
    EVENT_POST       = 'post'
    EVENT_DELETE     = 'delete'
    EVENT_CHAT_OPEN  = 'chat_open'
    EVENT_CHAT_SEND  = 'chat_send'

    EVENT_CHOICES = [
        (EVENT_SIGNUP,    'Signed up'),
        (EVENT_LOGIN,     'Signed in'),
        (EVENT_POST,      'Posted a product'),
        (EVENT_DELETE,    'Deleted a listing'),
        (EVENT_CHAT_OPEN, 'Started a chat'),
        (EVENT_CHAT_SEND, 'Sent a message'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity',
    )
    event = models.CharField(max_length=20, choices=EVENT_CHOICES)
    title = models.CharField(max_length=255)
    detail = models.CharField(max_length=255, blank=True)
    icon = models.CharField(max_length=8, default='•')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Powers the "my activity, newest first" page query.
            Index(fields=['user', '-created_at'], name='activity_user_idx'),
        ]

    def __str__(self):
        return f'{self.user.username} • {self.event} • {self.title}'

    @classmethod
    def record(cls, user, event, title='', detail='', icon=''):
        """Tiny helper so callers don't repeat the boilerplate."""
        return cls.objects.create(
            user=user,
            event=event,
            title=title or dict(cls.EVENT_CHOICES).get(event, event),
            detail=detail,
            icon=icon or cls._default_icon(event),
        )

    @staticmethod
    def _default_icon(event):
        return {
            UserActivity.EVENT_SIGNUP:    '🎉',
            UserActivity.EVENT_LOGIN:     '🔓',
            UserActivity.EVENT_POST:      '📦',
            UserActivity.EVENT_DELETE:    '🗑️',
            UserActivity.EVENT_CHAT_OPEN: '💬',
            UserActivity.EVENT_CHAT_SEND: '✉️',
        }.get(event, '•')