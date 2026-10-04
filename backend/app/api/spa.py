"""Reloadable app routes without swallowing missing API/static-asset responses."""
import re
from starlette.staticfiles import StaticFiles
from starlette.exceptions import HTTPException


class FrontendFiles(StaticFiles):
    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            route=re.fullmatch(r"(?:login|signup|account|my-learning|history|pipeline|courses|subjects/[a-z0-9-]+|courses/[a-z0-9-]+(?:/lessons/lab_[a-z0-9_]+)?|learn/lab_[a-z0-9_]+)",path)
            if exc.status_code==404 and scope["method"] in {"GET","HEAD"} and route:
                return await super().get_response("index.html",scope)
            raise
