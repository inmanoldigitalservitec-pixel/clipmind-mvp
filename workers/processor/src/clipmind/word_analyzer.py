from __future__ import annotations

from typing import Any

from .srt import ms_to_timestamp
from .words import WordToken


FILLER_WORDS = {
    "eh",
    "ehh",
    "ehhh",
    "em",
    "emm",
    "umm",
    "um",
    "ummm",
    "mmm",
    "mmmm",
    "este",
}

SOFT_FILLER_WORDS = {
    "bueno",
    "ok",
    "okay",
}

FALSE_START_PHRASES = [
    ("no", "espera"),
    ("espera", "no"),
    ("dejame", "repetir"),
    ("déjame", "repetir"),
    ("dejame", "decirlo", "mejor"),
    ("déjame", "decirlo", "mejor"),
    ("lo", "digo", "otra", "vez"),
    ("toma", "salio", "mal"),
    ("toma", "salió", "mal"),
]

FILLER_PHRASES = [
    ("o", "sea"),
    ("eh", "bueno"),
    ("y", "bueno"),
]


def _candidate(
    candidate_type: str,
    start_ms: int,
    end_ms: int,
    text: str,
    reason: str,
    confidence: float,
    word_ids: list[int],
    suggested_action: str = "remove",
) -> dict[str, Any]:
    return {
        "type": candidate_type,
        "start": ms_to_timestamp(start_ms),
        "end": ms_to_timestamp(end_ms),
        "text": text,
        "reason": reason,
        "confidence": round(confidence, 2),
        "word_ids": word_ids,
        "suggested_action": suggested_action,
    }


def _match_phrase(words: list[WordToken], start_index: int, phrase: tuple[str, ...], max_gap_ms: int = 450) -> bool:
    if start_index + len(phrase) > len(words):
        return False

    for offset, expected in enumerate(phrase):
        if words[start_index + offset].normalized != expected:
            return False
        if offset > 0:
            previous = words[start_index + offset - 1]
            current = words[start_index + offset]
            if current.start_ms - previous.end_ms > max_gap_ms:
                return False

    return True


def _phrase_text(words: list[WordToken]) -> str:
    return " ".join(word.raw for word in words)


def merge_candidates(candidates: list[dict[str, Any]], max_gap_ms: int = 180) -> list[dict[str, Any]]:
    if not candidates:
        return []

    def to_ms(ts: str) -> int:
        h, m, rest = ts.split(":")
        s, ms = rest.split(".")
        return int(h) * 3_600_000 + int(m) * 60_000 + int(s) * 1_000 + int(ms)

    ordered = sorted(candidates, key=lambda item: to_ms(item["start"]))
    merged: list[dict[str, Any]] = [ordered[0]]

    for candidate in ordered[1:]:
        last = merged[-1]
        gap = to_ms(candidate["start"]) - to_ms(last["end"])
        same_action = candidate.get("suggested_action") == last.get("suggested_action")
        if 0 <= gap <= max_gap_ms and same_action:
            last["end"] = candidate["end"]
            last["text"] = f"{last['text']} {candidate['text']}".strip()
            last["reason"] = f"{last['reason']}; {candidate['reason']}"
            last["confidence"] = max(float(last["confidence"]), float(candidate["confidence"]))
            last["word_ids"] = [*last.get("word_ids", []), *candidate.get("word_ids", [])]
            if last["type"] != candidate["type"]:
                last["type"] = "merged_candidate"
        else:
            merged.append(candidate)

    return merged


def analyze_words(words: list[WordToken], mode: str = "clean_cut") -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    matched_word_ids: set[int] = set()

    for index, word in enumerate(words):
        if word.id in matched_word_ids:
            continue

        matched_phrase = False
        for phrase in FALSE_START_PHRASES:
            if _match_phrase(words, index, phrase):
                phrase_words = words[index : index + len(phrase)]
                candidates.append(
                    _candidate(
                        "false_start_phrase",
                        phrase_words[0].start_ms,
                        phrase_words[-1].end_ms,
                        _phrase_text(phrase_words),
                        "false start or self-correction phrase detected with word timestamps",
                        0.88,
                        [item.id for item in phrase_words],
                    )
                )
                matched_word_ids.update(item.id for item in phrase_words)
                matched_phrase = True
                break

        if matched_phrase:
            continue

        for phrase in FILLER_PHRASES:
            if _match_phrase(words, index, phrase):
                phrase_words = words[index : index + len(phrase)]
                candidates.append(
                    _candidate(
                        "filler_phrase",
                        phrase_words[0].start_ms,
                        phrase_words[-1].end_ms,
                        _phrase_text(phrase_words),
                        "filler phrase detected with word timestamps",
                        0.82,
                        [item.id for item in phrase_words],
                    )
                )
                matched_word_ids.update(item.id for item in phrase_words)
                matched_phrase = True
                break

        if matched_phrase:
            continue

        if word.normalized in FILLER_WORDS:
            candidates.append(
                _candidate(
                    "filler_word",
                    word.start_ms,
                    word.end_ms,
                    word.raw,
                    "single filler word detected with word timestamp",
                    0.9,
                    [word.id],
                )
            )
            matched_word_ids.add(word.id)
            continue

        if word.normalized in SOFT_FILLER_WORDS and word.duration_ms <= 850:
            candidates.append(
                _candidate(
                    "soft_filler_word",
                    word.start_ms,
                    word.end_ms,
                    word.raw,
                    "short soft filler word detected; should be reviewed if surrounded by useful speech",
                    0.66,
                    [word.id],
                    suggested_action="review",
                )
            )
            matched_word_ids.add(word.id)

    silence_candidates: list[dict[str, Any]] = []
    for previous, current in zip(words, words[1:]):
        gap_ms = current.start_ms - previous.end_ms
        if gap_ms >= 700:
            silence_candidates.append(
                _candidate(
                    "silence_gap",
                    previous.end_ms,
                    current.start_ms,
                    "",
                    f"silence gap between words ({gap_ms} ms)",
                    0.74,
                    [previous.id, current.id],
                    suggested_action="review" if gap_ms < 1200 else "remove",
                )
            )

    candidates = merge_candidates([*candidates, *silence_candidates])

    remove = [item for item in candidates if item.get("suggested_action") == "remove"]
    review = [item for item in candidates if item.get("suggested_action") == "review"]

    return {
        "version": "0.1",
        "mode": mode,
        "source_type": "word_timestamps",
        "summary": {
            "words": len(words),
            "candidates": len(candidates),
            "remove_candidates": len(remove),
            "review_candidates": len(review),
        },
        "candidates": candidates,
        "remove": remove,
        "review": review,
        "warnings": [] if words else ["No words were found in the input JSON."],
    }
