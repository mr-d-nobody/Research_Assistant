import mimetypes

from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def frontend_view(_request, _path=""):
    dist_dir = settings.FRONTEND_DIST_DIR

    # Serve real files from dist (favicon, manifest, images, etc.)
    if _path:
        file_path = dist_dir / _path
        if file_path.is_file() and dist_dir in file_path.resolve().parents:
            content_type, _ = mimetypes.guess_type(str(file_path))
            return FileResponse(
                file_path.open("rb"),
                content_type=content_type or "application/octet-stream",
            )

    # Fall back to index.html for SPA routing
    index_path = dist_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path.open("rb"), content_type="text/html")

    return HttpResponse(
        "Frontend build is missing. Run npm run build before serving this page.",
        status=503,
    )
