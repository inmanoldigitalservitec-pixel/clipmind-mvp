from __future__ import annotations

import re
from typing import Any

from .srt import SrtSegment, ms_to_timestamp


FILLER_PATTERNS = [
    r"^e+h+[\.\s,]*$",
    r"^m+h+[\.\s,]*$",
    r"^um+[\.\s,]*$",
    r"^bueno[\.\s,]*$",
    r"^este[\.\s,]*$",
    r"^ok[\.\s,]*$",
    r"\b(eh|mmm|um|este|bueno)\b.*\bvamos a empezar\b",
    r"\bvamos a empezar[\.\s,]*$",
    r"déjame organizarme",
    r"dejame organizarme",
]

FALSE_START_PATTERNS = [
    r"no,? espera",
    r"espera,? no",
    r"déjame repetir",
    r"dejame repetir",
    r"déjame decirlo mejor",
    r"dejame decirlo mejor",
    r"lo digo otra vez",
]


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def is_filler(text: str) -> bool:
    compact = normalize_text(text)
    if not compact:
        return True
    if len(compact.split()) <= 2 and any(token in compact for token in ["eh", "mmm", "um", "este"]):
        return True
    return any(re.search(pattern, compact) for pattern in FILLER_PATTERNS)


def is_false_start(text: str) -> bool:
    compact = normalize_text(text)
    return any(re.search(pattern, compact) for pattern in FALSE_START_PATTERNS)


def is_near_duplicate(a: str, b: str) -> bool:
    a_words = set(normalize_text(a).split())
    b_words = set(normalize_text(b).split())
    if len(a_words) < 4 or len(b_words) < 4:
        return False
    overlap = len(a_words & b_words) / max(len(a_words | b_words), 1)
    return overlap >= 0.72


def _cut(start_ms: int, end_ms: int, reason: str, confidence: float) -> dict[str, Any]:
    return {
        "start": ms_to_timestamp(start_ms),
        "end": ms_to_timestamp(end_ms),
        "reason": reason,
        "confidence": round(confidence, 2),
    }


def merge_cuts(cuts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not cuts:
        return []

    def to_ms(ts: str) -> int:
        h, m, rest = ts.split(":")
        s, ms = rest.split(".")
        return int(h) * 3_600_000 + int(m) * 60_000 + int(s) * 1_000 + int(ms)

    ordered = sorted(cuts, key=lambda item: to_ms(item["start"]))
    merged = [ordered[0]]

    for cut in ordered[1:]:
        last = merged[-1]
        if to_ms(cut["start"]) <= to_ms(last["end"]) + 250:
            last["end"] = max(last["end"], cut["end"], key=to_ms)
            last["reason"] = f"{last['reason']}; {cut['reason']}"
            last["confidence"] = max(last["confidence"], cut["confidence"])
        else:
            merged.append(cut)

    return merged


def build_keep_ranges(segments: list[SrtSegment], remove: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not segments:
        return []

    def to_ms(ts: str) -> int:
        h, m, rest = ts.split(":")
        s, ms = rest.split(".")
        return int(h) * 3_600_000 + int(m) * 60_000 + int(s) * 1_000 + int(ms)

    video_start = segments[0].start_ms
    video_end = segments[-1].end_ms
    cursor = video_start
    keep: list[dict[str, Any]] = []

    for cut in remove:
        cut_start = to_ms(cut["start"])
        cut_end = to_ms(cut["end"])
        if cut_start > cursor:
            keep.append({
                "start": ms_to_timestamp(cursor),
                "end": ms_to_timestamp(cut_start),
                "reason": "content preserved after automatic cut analysis",
            })
        cursor = max(cursor, cut_end)

    if cursor < video_end:
        keep.append({
            "start": ms_to_timestamp(cursor),
            "end": ms_to_timestamp(video_end),
            "reason": "content preserved after automatic cut analysis",
        })

    return [item for item in keep if item["start"] != item["end"]]


def analyze_segments(segments: list[SrtSegment], mode: str = "clean_cut") -> dict[str, Any]:
    remove: list[dict[str, Any]] = []
    warnings: list[str] = []

    for i, segment in enumerate(segments):
        text = normalize_text(segment.text)

        if is_filler(text):
            remove.append(_cut(segment.start_ms, segment.end_ms, "filler or empty speech with no useful content", 0.86))
            continue

        if is_false_start(text):
            remove.append(_cut(segment.start_ms, segment.end_ms, "false start or self-correction", 0.84))
            continue

        if i > 0 and is_near_duplicate(segments[i - 1].text, segment.text):
            remove.append(_cut(segment.start_ms, segment.end_ms, "repeated idea from previous subtitle", 0.78))
            continue

        if segment.duration_ms >= 4_000 and len(text.split()) <= 2:
            remove.append(_cut(segment.start_ms, segment.end_ms, "long low-information subtitle", 0.72))

    remove = merge_cuts(remove)
    keep = build_keep_ranges(segments, remove)

    if not segments:
        warnings.append("No SRT segments were found.")
    if not remove:
        warnings.append("No automatic cuts detected by the rule-based analyzer.")

    return {
        "version": "0.1",
        "mode": mode,
        "remove": remove,
        "keep": keep,
        "warnings": warnings,
    }
