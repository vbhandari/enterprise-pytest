"""Admin UI routes — serves the React SPA and provides a legacy /admin/login redirect."""

import pathlib

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter(prefix="/admin", tags=["admin"])

_APP_DIR = pathlib.Path(__file__).resolve().parent.parent
_SPA_DIR = _APP_DIR / "static" / "admin"


@router.get("/{full_path:path}", response_class=HTMLResponse)
async def admin_spa(request: Request, full_path: str) -> FileResponse:
    """
    Serve the React SPA.

    For asset files (JS, CSS, images) the corresponding file is returned.
    For all other paths, index.html is returned so React Router handles routing.
    """
    file_path = _SPA_DIR / full_path
    if full_path and file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(_SPA_DIR / "index.html")
