import hashlib
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


class AuthToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    @classmethod
    def create_for_user(cls, user):
        token = secrets.token_urlsafe(40)
        cls.objects.create(user=user, token_hash=cls.hash_token(token))
        return token

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode("utf-8")).hexdigest()


class RateLimitBucket(models.Model):
    key = models.CharField(max_length=255, unique=True)
    count = models.PositiveIntegerField(default=0)
    window_start = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


class DeviceDailyUsage(models.Model):
    device_id = models.CharField(max_length=120)
    date = models.DateField()
    chat_count = models.PositiveIntegerField(default=0)
    research_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["device_id", "date"],
                name="unique_device_daily_usage",
            )
        ]


class ConversationEntry(models.Model):
    CHAT = "chat"
    RESEARCH = "research"
    MODE_CHOICES = [
        (CHAT, "Chat"),
        (RESEARCH, "Research"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    prompt = models.TextField()
    answer = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class DeviceSignup(models.Model):
    device_id = models.CharField(max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

