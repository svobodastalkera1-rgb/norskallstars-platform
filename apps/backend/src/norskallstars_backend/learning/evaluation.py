"""Deterministic evaluator and advisory placement seams without ML dependencies."""

import json
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal, Protocol

from pydantic import JsonValue

from norskallstars_backend.learning.policy import ActivityRule, PlacementRule

Status = Literal["scored", "self_assessed", "pending", "not_applicable"]


@dataclass(frozen=True)
class Evaluation:
    status: Status
    score: Decimal | None
    correct: bool | None
    normalized: JsonValue
    evaluator: str
    version: str = "1.0.0"


class Evaluator(Protocol):
    def evaluate(
        self,
        activity: dict[str, Any],
        rule: ActivityRule,
        response: JsonValue,
        self_assessment: bool | None,
    ) -> Evaluation: ...


def normalize(value: JsonValue, activity: dict[str, Any], rule: ActivityRule) -> JsonValue:
    if isinstance(value, str):
        for binding in rule.normalization:
            if activity.get("normalization", {}).get(binding.flag) is True:
                if binding.operation == "trim":
                    value = value.strip()
                elif binding.operation == "case_fold":
                    value = value.casefold()
                else:
                    value = unicodedata.normalize("NFC", value)
    elif isinstance(value, list):
        return [normalize(item, activity, rule) for item in value]
    elif isinstance(value, dict):
        # Keys are structural identifiers, never linguistic text.
        return {key: normalize(item, activity, rule) for key, item in value.items()}
    return value


def representation(value: JsonValue, unordered: bool = False) -> str:
    if unordered and isinstance(value, list):
        # Multiset preserves duplicate counts; JSON distinguishes false/0 and strings/numbers.
        return json.dumps(sorted(representation(item) for item in value))
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )


class LocalEvaluator:
    def evaluate(
        self,
        activity: dict[str, Any],
        rule: ActivityRule,
        response: JsonValue,
        self_assessment: bool | None,
    ) -> Evaluation:
        mode = activity["evaluation"]["type"]
        normalized = normalize(response, activity, rule)
        if mode == "deterministic":
            if self_assessment is not None:
                raise ValueError("Client cannot grade a deterministic response")
            accepted = (
                rule.accepted_responses
                if rule.accepted_responses is not None
                else activity.get("accepted_answers", [])
            )
            if not accepted:
                raise ValueError("Unsupported deterministic evaluation")
            actual = representation(normalized, rule.comparison == "unordered")
            correct = any(
                actual
                == representation(normalize(a, activity, rule), rule.comparison == "unordered")
                for a in accepted
            )
            return Evaluation("scored", Decimal(int(correct)), correct, normalized, "deterministic")
        if mode == "self_assessment":
            if self_assessment is None:
                raise ValueError("Explicit self assessment required")
            return Evaluation(
                "self_assessed",
                Decimal(int(self_assessment)),
                self_assessment,
                normalized,
                "self_assessment",
            )
        if self_assessment is not None:
            raise ValueError("Unexpected client assessment")
        return Evaluation(
            "not_applicable" if mode == "none" else "pending", None, None, normalized, mode
        )


class PlacementStrategy(Protocol):
    def recommend(self, rule: PlacementRule, score: Decimal) -> str: ...


class DeterministicPlacement:
    def recommend(self, rule: PlacementRule, score: Decimal) -> str:
        return next(b.lesson_id for b in reversed(rule.recommendations) if score >= b.minimum_score)
