from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def frontend_view(_request, _path=""):
    index_path = settings.FRONTEND_DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path.open("rb"), content_type="text/html")

    return HttpResponse(
        "Frontend build is missing. Run npm run build before serving this page.",
        status=503,
    )
