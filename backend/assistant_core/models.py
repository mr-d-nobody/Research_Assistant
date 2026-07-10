import hashlib
import hmac
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


class AuthOtpChallenge(models.Model):
    LOGIN = "login"
    SIGNUP = "signup"
    PURPOSE_CHOICES = [
        (LOGIN, "Login"),
        (SIGNUP, "Signup"),
    ]

    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    email = models.EmailField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    code_hash = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    @staticmethod
    def generate_code():
        return f"{secrets.randbelow(1_000_000):06d}"

    @staticmethod
    def hash_code(code):
        secret = settings.SECRET_KEY.encode("utf-8")
        return hmac.new(secret, code.encode("utf-8"), hashlib.sha256).hexdigest()

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def code_matches(self, code):
        return hmac.compare_digest(self.code_hash, self.hash_code(code))
