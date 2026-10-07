"""Project a domain API and its reachable schemas without changing other contracts."""

from copy import deepcopy
from typing import Any


def domain_schema(document: dict[str, Any], prefix: str) -> dict[str, Any]:
    result = deepcopy(document)
    result["paths"] = {p: v for p, v in document["paths"].items() if p.startswith(prefix)}
    refs: set[str] = set()

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            if "$ref" in value:
                refs.add(value["$ref"])
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    collect(result["paths"])
    selected: dict[str, Any] = {}
    while refs:
        ref = refs.pop()
        name = ref.rsplit("/", 1)[-1]
        if name not in selected:
            selected[name] = document["components"]["schemas"][name]
            collect(selected[name])
    result["components"]["schemas"] = selected
    return result
