from django.urls import path, re_path

from assistant_core.views import (
    chat_view,
    change_password_view,
    conversation_history_view,
    health_view,
    login_view,
    logout_view,
    me_view,
    signup_view,
    usage_view,
)
from .views import frontend_view


urlpatterns = [
    path("api/health/", health_view),
    path("api/auth/signup/", signup_view),
    path("api/auth/login/", login_view),
    path("api/auth/logout/", logout_view),
    path("api/auth/me/", me_view),
    path("api/auth/change-password/", change_password_view),
    path("api/usage/", usage_view),
    path("api/conversations/", conversation_history_view),
    path("api/chat/", chat_view),
    re_path(r"^(?P<_path>.*)$", frontend_view),
]
