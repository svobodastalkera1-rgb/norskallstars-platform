"""Future explicit migration port; no automatic mapping or progress rewrite exists."""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class ProgressMapping:
    source_release: UUID
    target_release: UUID
    mapping_version: str
    lesson_ids: dict[str, str]


class ProgressMigrationPlanner(Protocol):
    def mapping(self, source_release: UUID, target_release: UUID) -> ProgressMapping | None:
        """None means keep all progress on its source release; never guess identities."""
        ...
