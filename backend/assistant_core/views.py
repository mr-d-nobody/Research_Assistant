import json
import logging
import re
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .assistant import ResearchAssistant
from .models import AuthToken, ConversationEntry, DeviceDailyUsage, DeviceSignup, RateLimitBucket


logger = logging.getLogger(__name__)
assistant = None
CHAT_LIMIT = 10
RESEARCH_LIMIT = 1
CHAT_HISTORY_LIMIT = 20
RESEARCH_HISTORY_LIMIT = 2
PASSWORD_MIN_LENGTH = 8
MAX_PROMPT_LENGTH = 4000
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
DEVICE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{8,120}$")
LOGIN_LIMIT = 20
LOGIN_WINDOW_SECONDS = 10 * 60
SIGNUP_LIMIT = 5
SIGNUP_WINDOW_SECONDS = 60 * 60
SIGNUP_DEVICE_COOLDOWN_DAYS = 90
PASSWORD_CHANGE_LIMIT = 5
PASSWORD_CHANGE_WINDOW_SECONDS = 60 * 60


@require_GET
def health_view(_request):
    return JsonResponse({"status": "ok"})


def get_assistant():
    global assistant
    if assistant is None:
        assistant = ResearchAssistant()
    return assistant


def parse_json_body(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        return payload if isinstance(payload, dict) else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def user_payload(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "isSuperuser": is_limit_exempt(user),
    }


def is_limit_exempt(user):
    return bool(user and user.is_superuser)


def get_client_ip(request):
    return request.META.get("REMOTE_ADDR", "unknown")[:64]


def check_rate_limit(key, limit, window_seconds):
    now = timezone.now()
    window_cutoff = now - timedelta(seconds=window_seconds)

    with transaction.atomic():
        bucket, _created = RateLimitBucket.objects.select_for_update().get_or_create(
            key=key,
            defaults={"window_start": now, "count": 0},
        )

        if bucket.window_start < window_cutoff:
            bucket.window_start = now
            bucket.count = 0

        if bucket.count >= limit:
            return False

        bucket.count += 1
        bucket.save(update_fields=["count", "window_start", "updated_at"])
        return True


def rate_limit_response():
    return JsonResponse(
        {"error": "Too many attempts. Please wait a few minutes and try again."},
        status=429,
    )


def is_valid_username(username):
    return bool(USERNAME_PATTERN.fullmatch(username))


def is_valid_email(email):
    if not email:
        return True
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def is_valid_device_id(device_id):
    return bool(DEVICE_ID_PATTERN.fullmatch(device_id))


def get_authenticated_user(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None

    token = header.removeprefix("Bearer ").strip()
    if not token:
        return None

    cutoff = timezone.now() - timedelta(hours=settings.AUTH_TOKEN_TTL_HOURS)
    token_hash = AuthToken.hash_token(token)
    auth_token = AuthToken.objects.select_related("user").filter(token_hash=token_hash).first()
    if auth_token and auth_token.created_at < cutoff:
        auth_token.delete()
        return None

    return auth_token.user if auth_token else None


@csrf_exempt
@require_POST
def signup_view(request):
    if not check_rate_limit(f"signup:{get_client_ip(request)}", SIGNUP_LIMIT, SIGNUP_WINDOW_SECONDS):
        return rate_limit_response()

    device_id = get_device_id(request)
    if not is_valid_device_id(device_id):
        return JsonResponse({"error": "Please refresh and try again."}, status=400)

    # Enforce 1 signup per device per 90 days
    cutoff = timezone.now() - timedelta(days=SIGNUP_DEVICE_COOLDOWN_DAYS)
    recent_signup = DeviceSignup.objects.filter(device_id=device_id, updated_at__gte=cutoff).first()
    if recent_signup:
        return JsonResponse(
            {"error": "This device has already created an account. Please sign in instead."},
            status=429,
        )

    payload = parse_json_body(request)
    if payload is None:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""

    if not is_valid_username(username):
        return JsonResponse(
            {"error": "User ID must be 3-30 characters using letters, numbers, dot, dash, or underscore."},
            status=400,
        )
    if not is_valid_email(email):
        return JsonResponse({"error": "Enter a valid email address."}, status=400)
    if len(password) < PASSWORD_MIN_LENGTH:
        return JsonResponse({"error": "Password must be at least 8 characters."}, status=400)
    if User.objects.filter(username__iexact=username).exists():
        return JsonResponse({"error": "That user ID is already taken."}, status=400)
    if email and User.objects.filter(email__iexact=email).exists():
        return JsonResponse({"error": "That email is already registered."}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    token = AuthToken.create_for_user(user)

    # Record this device's signup
    DeviceSignup.objects.update_or_create(
        device_id=device_id,
        defaults={"updated_at": timezone.now()},
    )

    return JsonResponse({"token": token, "user": user_payload(user)}, status=201)


@csrf_exempt
@require_POST
def login_view(request):
    payload = parse_json_body(request)
    if payload is None:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    rate_key = f"login:{get_client_ip(request)}:{username.lower()[:80] or 'blank'}"
    if not check_rate_limit(rate_key, LOGIN_LIMIT, LOGIN_WINDOW_SECONDS):
        return rate_limit_response()

    user = authenticate(username=username, password=password)

    if user is None:
        return JsonResponse({"error": "Invalid user ID or password."}, status=400)

    token = AuthToken.create_for_user(user)
    return JsonResponse({"token": token, "user": user_payload(user)})


@csrf_exempt
@require_POST
def logout_view(request):
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        token_hash = AuthToken.hash_token(header.removeprefix("Bearer ").strip())
        AuthToken.objects.filter(token_hash=token_hash).delete()
    return JsonResponse({"status": "ok"})


@require_GET
def me_view(request):
    user = get_authenticated_user(request)
    if user is None:
        return JsonResponse({"error": "Unauthorized."}, status=401)
    return JsonResponse({"user": user_payload(user)})


@csrf_exempt
@require_POST
def change_password_view(request):
    user = get_authenticated_user(request)
    if user is None:
        return JsonResponse({"error": "Please sign in to update your profile."}, status=401)
    if not check_rate_limit(
        f"password-change:{user.id}",
        PASSWORD_CHANGE_LIMIT,
        PASSWORD_CHANGE_WINDOW_SECONDS,
    ):
        return rate_limit_response()

    payload = parse_json_body(request)
    if payload is None:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    current_password = payload.get("currentPassword") or ""
    new_password = payload.get("newPassword") or ""

    if not user.check_password(current_password):
        return JsonResponse({"error": "Current password is not correct."}, status=400)
    if len(new_password) < PASSWORD_MIN_LENGTH:
        return JsonResponse({"error": "New password must be at least 8 characters."}, status=400)
    if current_password == new_password:
        return JsonResponse({"error": "Choose a different new password."}, status=400)

    user.set_password(new_password)
    user.save(update_fields=["password"])
    AuthToken.objects.filter(user=user).delete()
    token = AuthToken.create_for_user(user)
    return JsonResponse(
        {
            "status": "ok",
            "message": "Password updated. Your session was refreshed.",
            "token": token,
            "user": user_payload(user),
        }
    )


def get_device_id(request):
    return (request.headers.get("X-Device-ID") or "").strip()


def check_and_increment_usage(device_id, mode):
    today = timezone.localdate()
    with transaction.atomic():
        usage, _created = DeviceDailyUsage.objects.select_for_update().get_or_create(
            device_id=device_id,
            date=today,
        )

        if mode == "research":
            if usage.research_count >= RESEARCH_LIMIT:
                return False, usage
            usage.research_count += 1
        else:
            if usage.chat_count >= CHAT_LIMIT:
                return False, usage
            usage.chat_count += 1

        usage.save(update_fields=["chat_count", "research_count", "updated_at"])
        return True, usage


def usage_payload(usage):
    return {
        "date": usage.date.isoformat(),
        "chatUsed": usage.chat_count,
        "chatLimit": CHAT_LIMIT,
        "researchUsed": usage.research_count,
        "researchLimit": RESEARCH_LIMIT,
    }


def unlimited_usage_payload():
    return {
        "date": timezone.localdate().isoformat(),
        "chatUsed": 0,
        "chatLimit": None,
        "researchUsed": 0,
        "researchLimit": None,
        "unlimited": True,
    }


@require_GET
def usage_view(request):
    user = get_authenticated_user(request)
    if user is None:
        return JsonResponse({"error": "Please sign in to view usage."}, status=401)

    if is_limit_exempt(user):
        return JsonResponse({"usage": unlimited_usage_payload()})

    device_id = get_device_id(request)
    if not is_valid_device_id(device_id):
        return JsonResponse({"error": "Please refresh and try again."}, status=400)

    usage, _created = DeviceDailyUsage.objects.get_or_create(
        device_id=device_id,
        date=timezone.localdate(),
    )
    return JsonResponse({"usage": usage_payload(usage)})


def limit_reached_message(mode, usage=None):
    if usage and usage.chat_count >= CHAT_LIMIT and usage.research_count >= RESEARCH_LIMIT:
        return (
            "Mission complete for today. Loid has logged today's chats and mission. "
            "Come back tomorrow for a fresh objective."
        )
    if mode == "research":
        return (
            "Loid has completed today's mission. Come back tomorrow with a fresh objective."
        )
    return (
        "Loid has wrapped today's chat allocation. Mission notes are saved - come back "
        "tomorrow and we will pick it up again."
    )


def rollback_usage(device_id, mode):
    today = timezone.localdate()
    with transaction.atomic():
        usage = DeviceDailyUsage.objects.select_for_update().filter(
            device_id=device_id,
            date=today,
        ).first()
        if usage is None:
            return

        if mode == "research" and usage.research_count:
            usage.research_count -= 1
        elif mode == "chat" and usage.chat_count:
            usage.chat_count -= 1

        usage.save(update_fields=["chat_count", "research_count", "updated_at"])


def conversation_entry_payload(entry):
    return [
        {
            "role": "user",
            "mode": entry.mode,
            "content": entry.prompt,
            "sources": [],
        },
        {
            "role": "assistant",
            "mode": entry.mode,
            "content": entry.answer,
            "sources": entry.sources or [],
            "email": {"sent": entry.email_sent, "error": None} if entry.email_sent else None,
        },
    ]


def get_limited_conversation_entries(user):
    entry_ids = []
    for mode, limit in [
        (ConversationEntry.CHAT, CHAT_HISTORY_LIMIT),
        (ConversationEntry.RESEARCH, RESEARCH_HISTORY_LIMIT),
    ]:
        mode_ids = list(
            ConversationEntry.objects.filter(user=user, mode=mode)
            .order_by("-created_at", "-id")
            .values_list("id", flat=True)[:limit]
        )
        entry_ids.extend(mode_ids)

    return ConversationEntry.objects.filter(id__in=entry_ids).order_by("created_at", "id")


def build_conversation_history(user):
    messages = []
    for entry in get_limited_conversation_entries(user):
        messages.extend(conversation_entry_payload(entry))
    return messages


def trim_conversation_history(user, mode):
    limit = RESEARCH_HISTORY_LIMIT if mode == ConversationEntry.RESEARCH else CHAT_HISTORY_LIMIT
    keep_ids = list(
        ConversationEntry.objects.filter(user=user, mode=mode)
        .order_by("-created_at", "-id")
        .values_list("id", flat=True)[:limit]
    )
    ConversationEntry.objects.filter(user=user, mode=mode).exclude(id__in=keep_ids).delete()


def save_conversation_entry(user, mode, prompt, result):
    entry = ConversationEntry.objects.create(
        user=user,
        mode=mode,
        prompt=prompt,
        answer=result.get("answer") or "",
        sources=result.get("sources") or [],
        email_sent=bool((result.get("email") or {}).get("sent")),
    )
    trim_conversation_history(user, mode)
    return entry


@require_GET
def conversation_history_view(request):
    user = get_authenticated_user(request)
    if user is None:
        return JsonResponse({"error": "Please sign in to view conversations."}, status=401)

    return JsonResponse({"messages": build_conversation_history(user)})


@csrf_exempt
@require_POST
def chat_view(request):
    user = get_authenticated_user(request)
    if user is None:
        return JsonResponse({"error": "Please sign in to work with Loid."}, status=401)

    payload = parse_json_body(request)
    if payload is None:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    prompt = (payload.get("message") or "").strip()
    mode = "research" if payload.get("mode") == "research" else "chat"
    wants_email = bool(payload.get("emailResult"))
    email_to = user.email if mode == "research" and wants_email else None
    device_id = get_device_id(request)

    if not prompt:
        return JsonResponse({"error": "Message is required."}, status=400)
    if len(prompt) > MAX_PROMPT_LENGTH:
        return JsonResponse({"error": "Message is too long. Keep it under 4,000 characters."}, status=400)
    if mode == "research" and wants_email and not user.email:
        return JsonResponse({"error": "Add an email to your profile before sending results."}, status=400)
    if not is_valid_device_id(device_id):
        return JsonResponse({"error": "Please refresh and try again."}, status=400)

    usage = None
    if not is_limit_exempt(user):
        allowed, usage = check_and_increment_usage(device_id, mode)
        if not allowed:
            return JsonResponse(
                {"error": limit_reached_message(mode, usage), "usage": usage_payload(usage)},
                status=429,
            )

    try:
        result = get_assistant().chat(prompt=prompt, mode=mode, email_to=email_to)
        save_conversation_entry(user, mode, prompt, result)
        result["usage"] = unlimited_usage_payload() if is_limit_exempt(user) else usage_payload(usage)
        result["history"] = build_conversation_history(user)
        return JsonResponse(result)
    except Exception:
        if not is_limit_exempt(user):
            rollback_usage(device_id, mode)
        logger.exception("Assistant request failed.")
        return JsonResponse(
            {"error": "Loid hit an issue while preparing the brief. Please try again in a moment."},
            status=500,
        )
