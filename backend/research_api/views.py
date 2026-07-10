import mimetypes

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def dist_file_view(request, filename):
    """Serve a specific file from the frontend dist directory (e.g. favicon)."""
    file_path = settings.FRONTEND_DIST_DIR / filename
    if file_path.is_file():
        content_type, _ = mimetypes.guess_type(str(file_path))
        return FileResponse(
            file_path.open("rb"),
            content_type=content_type or "application/octet-stream",
        )
    raise Http404


@require_GET
def frontend_view(_request, _path=""):
    index_path = settings.FRONTEND_DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path.open("rb"), content_type="text/html")

    return HttpResponse(
        "Frontend build is missing. Run npm run build before serving this page.",
        status=503,
    )
