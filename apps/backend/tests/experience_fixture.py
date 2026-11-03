"""Artificial experience lab; never an approximation of any private course unit."""

import hashlib
import json
import struct
import zlib
from copy import deepcopy

from test_course_packages import mutate, payload


def synthetic_image():
    """Original geometric test diagram, deliberately not authored course artwork."""
    width, height = 640, 360
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            color = (34, 65, 69) if y < 230 else (18, 39, 48)
            if abs(x - 480) < 24 and abs(y - 70) < 24:
                color = (235, 194, 99)
            if 90 < x < 370 and 150 < y < 290:
                color = (53, 77, 74)
            if 130 < x < 185 and 190 < y < 240:
                color = (240, 191, 105)
            if 240 < x < 265 and 220 < y < 300 or 300 < x < 325 and 220 < y < 300:
                color = (176, 200, 194)
            rows.extend(color)

    def chunk(kind, raw):
        return struct.pack(">I", len(raw)) + kind + raw + struct.pack(">I", zlib.crc32(kind + raw))

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(rows)))
        + chunk(b"IEND", b"")
    )


def experience_payload():
    files = payload()
    picture = synthetic_image()
    files["assets/images/fixture-garden.png"] = picture

    def course(d):
        d["title"] = "PUBLIC-SAFE Synthetic Experience Lab"
        d["metadata"]["synthetic_test_only"] = True
        image = next(a for a in d["assets"] if a["type"] == "image")
        image.update(
            width=640,
            height=360,
            checksum=hashlib.sha256(picture).hexdigest(),
            alt_text=(
                "Synthetic geometry: two pale markers outside a dark rectangle "
                "with one warm square."
            ),
        )

    mutate(files, "course.json", course)
    mutate(
        files,
        "activities/fixture.activity.choose.json",
        lambda d: d.update(stimulus_refs=["fixture.asset.garden"]),
    )

    def lesson(d):
        d["blocks"].insert(
            0,
            {
                "block_id": "synthetic.context",
                "type": "text",
                "order": 0,
                "text": (
                    "PUBLIC-SAFE SYNTHETIC TEST. Invented symbols below exercise presentation only."
                ),
                "language": "en",
            },
        )
        for i, b in enumerate(d["blocks"], 1):
            b["order"] = i
        d["blocks"].append(
            {
                "block_id": "synthetic.after-task",
                "type": "text",
                "order": 6,
                "text": (
                    "Synthetic context continues after the interaction. "
                    "No private lesson is represented."
                ),
                "language": "en",
            }
        )

    mutate(files, "lessons/fixture.lesson.signal.json", lesson)
    original = json.loads(files["lessons/fixture.lesson.signal.json"])
    reading = deepcopy(original)
    reading.update(
        lesson_id="synthetic.experience.reading",
        order=3,
        title="Synthetic continuous reading",
        prerequisites=["fixture.lesson.pattern"],
        activity_refs=[],
        completion=None,
        review=None,
    )
    reading["blocks"] = [
        {
            "block_id": "synthetic.reading.image",
            "type": "image",
            "order": 1,
            "asset_ref": "fixture.asset.garden",
            "alt_text": "Synthetic geometry: two pale markers and one warm square.",
        },
        {
            "block_id": "synthetic.reading.text",
            "type": "text",
            "order": 2,
            "language": "en",
            "text": "\n\n".join(
                (
                    f"Synthetic paragraph {i}. This deliberately artificial reading surface "
                    "tests continuous prose, generous reading measure and text scaling. "
                    "A square, a line and two markers form a public-safe diagram. "
                    "No story, vocabulary sequence or private source is represented."
                )
                for i in range(1, 9)
            ),
            "reference_text": (
                "Synthetic on-demand translation example; not a real course translation."
            ),
        },
        {
            "block_id": "synthetic.reading.audio",
            "type": "audio",
            "order": 3,
            "asset_ref": "fixture.asset.chime",
            "transcript": "Synthetic two-tone signal; not narration or a real voice.",
        },
    ]
    files["lessons/synthetic.experience.reading.json"] = json.dumps(reading).encode()
    mutate(
        files,
        "chapters/fixture.chapter.garden.json",
        lambda d: d["lesson_refs"].append(reading["lesson_id"]),
    )
    mutate(
        files,
        "manifest.json",
        lambda d: d["components"].append("lessons/synthetic.experience.reading.json"),
    )
    # Public fixture stays non-production. Existing guarded test seeding alone creates
    # in-memory eligible derivatives to exercise the normal release boundary.
    manifest = json.loads(files["manifest.json"])
    assert manifest["release_eligible"] is False
    manifest["checksums"] = {
        n: hashlib.sha256(b).hexdigest() for n, b in files.items() if n != "manifest.json"
    }
    files["manifest.json"] = json.dumps(manifest).encode()
    return files
