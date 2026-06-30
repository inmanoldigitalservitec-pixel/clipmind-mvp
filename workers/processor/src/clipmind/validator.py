from __future__ import annotations

from typing import Any

from .srt import timestamp_to_ms


REQUIRED_CUT_FIELDS = {"start", "end", "reason"}


def validate_cuts_json(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if not isinstance(payload, dict):
        return ["Payload must be a JSON object."]

    for key in ["version", "mode", "remove", "keep", "warnings"]:
        if key not in payload:
            errors.append(f"Missing top-level key: {key}")

    for group_name in ["remove", "keep"]:
        group = payload.get(group_name)
        if not isinstance(group, list):
            errors.append(f"{group_name} must be a list.")
            continue

        previous_end = -1
        for index, item in enumerate(group):
            if not isinstance(item, dict):
                errors.append(f"{group_name}[{index}] must be an object.")
                continue

            missing = REQUIRED_CUT_FIELDS - set(item.keys())
            if missing:
                errors.append(f"{group_name}[{index}] missing fields: {sorted(missing)}")
                continue

            try:
                start_ms = timestamp_to_ms(str(item["start"]))
                end_ms = timestamp_to_ms(str(item["end"]))
            except ValueError as exc:
                errors.append(f"{group_name}[{index}] has invalid timestamp: {exc}")
                continue

            if end_ms <= start_ms:
                errors.append(f"{group_name}[{index}] end must be after start.")

            if start_ms < previous_end:
                errors.append(f"{group_name}[{index}] overlaps or is out of order.")

            previous_end = max(previous_end, end_ms)

            if not str(item.get("reason", "")).strip():
                errors.append(f"{group_name}[{index}] reason cannot be empty.")

    warnings = payload.get("warnings")
    if not isinstance(warnings, list):
        errors.append("warnings must be a list.")

    return errors
