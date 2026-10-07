"""No anonymous media, operator operations or decoder/evaluator endpoints."""

from typing import cast
from uuid import UUID

from fastapi import APIRouter, Request
from starlette.responses import Response

from norskallstars_backend.identity.dto import Accepted
from norskallstars_backend.identity.routes import (
    ClientHeader,
    IdentityRoute,
    PrincipalDependency,
    identity,
)
from norskallstars_backend.learning.routes import LessonPath
from norskallstars_backend.media.dto import OfferInput, OfferView, RecordingView, UploadInput
from norskallstars_backend.media.service import Media


class MediaRoute(IdentityRoute):
    json_string_limit = 350000


router = APIRouter(prefix="/api/v1/media", tags=["media"], route_class=MediaRoute)


async def media(request: Request, actor: PrincipalDependency) -> Media:
    await identity(request).rate_limit_account("media", actor)
    return cast(Media, request.app.state.media)


@router.get("/recordings", response_model=list[RecordingView])
async def recordings(request: Request, actor: PrincipalDependency) -> list[RecordingView]:
    return await (await media(request, actor)).recordings(actor)


@router.get(
    "/enrollments/{enrollment_id}/lessons/{lesson_id}/assets/{asset_id}", response_class=Response
)
async def asset(
    enrollment_id: UUID,
    lesson_id: LessonPath,
    asset_id: LessonPath,
    request: Request,
    actor: PrincipalDependency,
) -> Response:
    raw, mime = await (await media(request, actor)).asset(actor, enrollment_id, lesson_id, asset_id)
    return Response(raw, media_type=mime, headers={"Content-Disposition": "inline"})


@router.post("/recording-offers", response_model=OfferView)
async def offer(
    client: ClientHeader, data: OfferInput, request: Request, actor: PrincipalDependency
) -> OfferView:
    return await (await media(request, actor)).offer(actor, data)


@router.post("/recordings/{recording_id}", response_model=Accepted)
async def upload(
    client: ClientHeader,
    recording_id: UUID,
    data: UploadInput,
    request: Request,
    actor: PrincipalDependency,
) -> dict[str, str]:
    await (await media(request, actor)).upload(actor, recording_id, data)
    return {"status": "accepted"}


@router.delete("/recordings/{recording_id}", response_model=Accepted)
async def erase(
    client: ClientHeader, recording_id: UUID, request: Request, actor: PrincipalDependency
) -> dict[str, str]:
    await (await media(request, actor)).erase(actor, recording_id)
    return {"status": "accepted"}
