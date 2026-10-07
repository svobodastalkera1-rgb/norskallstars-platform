"""Authenticated learner API; no operator/admin or media delivery endpoints."""

from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Path, Request
from fastapi.responses import JSONResponse

from norskallstars_backend.identity.dto import ErrorResponse
from norskallstars_backend.identity.routes import (
    ClientHeader,
    IdentityRoute,
    PrincipalDependency,
    identity,
    identity_error,
)
from norskallstars_backend.identity.service import IdentityError
from norskallstars_backend.learning import dto
from norskallstars_backend.learning.service import Learning, LearningError


class LearningRoute(IdentityRoute):
    json_nodes = 4096


router = APIRouter(
    prefix="/api/v1/learning",
    tags=["learning"],
    route_class=LearningRoute,
    responses={
        status: {"model": ErrorResponse}
        for status in (400, 401, 403, 404, 405, 409, 413, 415, 422, 429, 500, 503, 504)
    },
)
LessonPath = Annotated[str, Path(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,127}$", max_length=128)]


async def learning(request: Request, actor: PrincipalDependency) -> Learning:
    await identity(request).rate_limit_account("learning", actor)
    return cast(Learning, request.app.state.learning)


@router.get("/courses", response_model=list[dto.CourseView])
async def courses(request: Request, actor: PrincipalDependency) -> list[dto.CourseView]:
    return await (await learning(request, actor)).catalog(actor)


@router.post("/enrollments", response_model=dto.EnrollmentView)
async def enroll(
    client: ClientHeader, data: dto.EnrollInput, request: Request, actor: PrincipalDependency
) -> dto.EnrollmentView:
    return await (await learning(request, actor)).enroll(actor, data.course_id)


@router.get("/enrollments", response_model=list[dto.EnrollmentSummary])
async def enrollments(request: Request, actor: PrincipalDependency) -> list[dto.EnrollmentSummary]:
    return await (await learning(request, actor)).enrollments(actor)


@router.get("/enrollments/{enrollment_id}", response_model=dto.EnrollmentView)
async def enrollment(
    enrollment_id: UUID, request: Request, actor: PrincipalDependency
) -> dto.EnrollmentView:
    return await (await learning(request, actor)).view(actor, enrollment_id)


@router.get("/enrollments/{enrollment_id}/lessons/{lesson_id}", response_model=dto.LessonView)
async def lesson(
    enrollment_id: UUID, lesson_id: LessonPath, request: Request, actor: PrincipalDependency
) -> dto.LessonView:
    return await (await learning(request, actor)).lesson(actor, enrollment_id, lesson_id)


@router.post("/enrollments/{enrollment_id}/attempts", response_model=dto.AttemptView)
async def start(
    client: ClientHeader,
    enrollment_id: UUID,
    data: dto.StartInput,
    request: Request,
    actor: PrincipalDependency,
) -> dto.AttemptView:
    return await (await learning(request, actor)).start(actor, enrollment_id, data)


@router.post("/attempts/{attempt_id}/submit", response_model=dto.AttemptView)
async def submit(
    client: ClientHeader,
    attempt_id: UUID,
    data: dto.SubmitInput,
    request: Request,
    actor: PrincipalDependency,
) -> dto.AttemptView:
    return await (await learning(request, actor)).submit(actor, attempt_id, data)


@router.post("/enrollments/{enrollment_id}/history", response_model=dto.HistoryView)
async def history(
    client: ClientHeader,
    enrollment_id: UUID,
    data: dto.HistoryInput,
    request: Request,
    actor: PrincipalDependency,
) -> dto.HistoryView:
    return await (await learning(request, actor)).history(actor, enrollment_id, data)


@router.get("/enrollments/{enrollment_id}/review", response_model=list[dto.ReviewView])
async def review(
    enrollment_id: UUID, request: Request, actor: PrincipalDependency
) -> list[dto.ReviewView]:
    return await (await learning(request, actor)).review(actor, enrollment_id)


@router.get("/enrollments/{enrollment_id}/placement", response_model=dto.AssessmentView)
async def assessment(
    enrollment_id: UUID, request: Request, actor: PrincipalDependency
) -> dict[str, Any]:
    return await (await learning(request, actor)).assessment(actor, enrollment_id)


@router.post("/enrollments/{enrollment_id}/placement", response_model=dto.PlacementView)
async def place(
    client: ClientHeader,
    enrollment_id: UUID,
    data: dto.PlacementInput,
    request: Request,
    actor: PrincipalDependency,
) -> dto.PlacementView:
    return await (await learning(request, actor)).place(actor, enrollment_id, data)


@router.post(
    "/enrollments/{enrollment_id}/placement/{placement_id}/accept",
    response_model=dto.EnrollmentView,
)
async def accept(
    client: ClientHeader,
    enrollment_id: UUID,
    placement_id: UUID,
    request: Request,
    actor: PrincipalDependency,
) -> dto.EnrollmentView:
    return await (await learning(request, actor)).accept_placement(
        actor, enrollment_id, placement_id
    )


@router.post("/enrollments/{enrollment_id}/translations", response_model=dto.TranslationView)
async def translate(
    client: ClientHeader,
    enrollment_id: UUID,
    data: dto.TranslationInput,
    request: Request,
    actor: PrincipalDependency,
) -> dto.TranslationView:
    return await (await learning(request, actor)).translate(actor, enrollment_id, data)


async def learning_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, LearningError):
        raise TypeError("Invalid learning handler invocation")
    return await identity_error(request, IdentityError(exc.status, exc.code))
