"""Read-only published-content domain port, distinct from privileged release transitions."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from norskallstars_backend.course_packages.models import CourseRelease


@dataclass(frozen=True)
class PublishedContent:
    id: UUID
    course_id: str
    version: str
    documents: dict[str, Any]


async def published_content(db: AsyncSession, release_id: UUID) -> PublishedContent | None:
    release = await db.scalar(
        select(CourseRelease).where(
            CourseRelease.id == release_id,
            CourseRelease.state == "published",
            CourseRelease.release_eligible.is_(True),
        )
    )
    if release is None or release.documents["course.json"].get("metadata", {}).get("fixture"):
        return None
    return PublishedContent(
        release.id, release.course_id, release.course_version, release.documents
    )


@dataclass(frozen=True)
class PublishedSummary:
    id: UUID
    course_id: str
    version: str
    title: str
    language: str


async def published_summary(db: AsyncSession, release_id: UUID) -> PublishedSummary | None:
    # JSONB projections avoid loading every large immutable snapshot for catalog/list APIs.
    row = (
        await db.execute(
            select(
                CourseRelease.id,
                CourseRelease.course_id,
                CourseRelease.course_version,
                CourseRelease.documents["course.json"]["title"].astext,
                CourseRelease.documents["course.json"]["language"].astext,
                CourseRelease.documents["course.json"]["metadata"]["fixture"],
            ).where(
                CourseRelease.id == release_id,
                CourseRelease.state == "published",
                CourseRelease.release_eligible.is_(True),
            )
        )
    ).one_or_none()
    if row is None or row[5]:
        return None
    return PublishedSummary(row[0], row[1], row[2], row[3], row[4])
