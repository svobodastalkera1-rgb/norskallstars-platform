"""Experience projection and synthetic boundary regressions; no private material."""

from copy import deepcopy
from unittest.mock import Mock
from uuid import uuid4

import pytest
from experience_fixture import experience_payload
from test_course_packages import zipped
from test_learning import documents, synthetic_policy

from norskallstars_backend.course_packages.catalog import PublishedContent
from norskallstars_backend.course_packages.validation import validate_archive
from norskallstars_backend.learning.service import Learning, LearningError


def test_synthetic_experience_remains_release_ineligible():
    package = validate_archive(zipped(experience_payload()))
    assert package.manifest["release_eligible"] is False
    assert package.documents["course.json"]["metadata"]["fixture"] is True
    assert len([n for n in package.documents if n.startswith("lessons/")]) == 3


def test_safe_stimulus_projection_never_copies_authoring_metadata():
    docs = documents(experience_payload())
    docs["course.json"]["assets"][0].update(
        source_ref="private-sentinel", speaker_notes=["private-sentinel"]
    )
    content = PublishedContent(uuid4(), "fixture.course", "1.0.0", docs)
    service = Learning(Mock(), Mock())
    activity = service.activity_view(
        content, synthetic_policy(docs), "fixture.activity.choose", include_media=True
    )
    assert activity.stimuli[0].asset_id == "fixture.asset.garden"
    assert "private-sentinel" not in activity.model_dump_json()
    assert "accepted_answers" not in activity.model_dump_json()
    assert (
        service.activity_view(content, synthetic_policy(docs), "fixture.activity.choose").stimuli
        == []
    )
    bad = deepcopy(content.documents)
    bad["activities/fixture.activity.choose.json"]["stimulus_refs"] = ["foreign.asset"]
    with pytest.raises(LearningError):
        service.activity_view(
            PublishedContent(uuid4(), "other", "1", bad),
            synthetic_policy(docs),
            "fixture.activity.choose",
            include_media=True,
        )


def test_transcript_preserves_explicit_audio_association_and_block_precedence():
    docs = documents(experience_payload())
    audio = next(a for a in docs["course.json"]["assets"] if a["type"] == "audio")
    audio["transcript"] = "Synthetic approved asset transcript"
    audio["speaker_notes"] = ["private-sentinel"]
    content = PublishedContent(uuid4(), "fixture.course", "1.0.0", docs)
    service = Learning(Mock(), Mock())
    block = {"type": "audio", "asset_ref": audio["asset_id"]}
    assert service.block_transcript(content, block) == "Synthetic approved asset transcript"
    assert (
        service.block_transcript(content, {**block, "transcript": "Explicit block"})
        == "Explicit block"
    )
    assert service.block_transcript(content, {"type": "text"}) is None
    with pytest.raises(LearningError):
        service.block_transcript(content, {**block, "asset_ref": "foreign.asset"})
