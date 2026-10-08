"""Read-only built Web delivery, no package/private asset directory serving."""

from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope


class WebFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        if path.startswith(("api/", "health/")):
            raise HTTPException(404)
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or "." in path or ".." in path:
                raise
            return await super().get_response("index.html", scope)
