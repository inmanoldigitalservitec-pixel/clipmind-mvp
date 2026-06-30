from __future__ import annotations

from dataclasses import dataclass
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from .srt import ms_to_timestamp, timestamp_to_ms


_WORD_CLEAN_RE = re.compile(r"[^\wáéíóúüñÁÉÍÓÚÜÑ]+", re.UNICODE)


@dataclass(frozen=True)
class WordToken:
    id: int
    raw: str
    normalized: str
    start_ms: int
    end_ms: int
    confidence: float | None = None

    @property
    def start(self) -> str:
        return ms_to_timestamp(self.start_ms)

    @property
    def end(self) -> str:
        return ms_to_timestamp(self.end_ms)

    @property
    def duration_ms(self) -> int:
        return max(0, self.end_ms - self.start_ms)

    def to_json(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "raw": self.raw,
            "normalized": self.normalized,
            "start": self.start,
            "end": self.end,
            "duration_ms": self.duration_ms,
        }
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        return payload


def normalize_word(value: str) -> str:
    value = value.strip().lower()
    value = unicodedata.normalize("NFKC", value)
    value = _WORD_CLEAN_RE.sub("", value)
    return value.strip("_")


def seconds_to_ms(value: float | int | str) -> int:
    if isinstance(value, str) and ":" in value:
        return timestamp_to_ms(value)
    return int(round(float(value) * 1000))


def load_words_json(path: str | Path) -> list[WordToken]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_words_payload(payload)


def parse_words_payload(payload: Any) -> list[WordToken]:
    if isinstance(payload, list):
        raw_words = payload
    elif isinstance(payload, dict) and isinstance(payload.get("words"), list):
        raw_words = payload["words"]
    elif isinstance(payload, dict) and isinstance(payload.get("segments"), list):
        raw_words = []
        for segment in payload["segments"]:
            raw_words.extend(segment.get("words", []))
    else:
        raise ValueError("Expected a JSON list, a {words: []} object, or a {segments: [{words: []}]} object.")

    words: list[WordToken] = []
    for index, item in enumerate(raw_words, start=1):
        raw = str(item.get("raw") or item.get("word") or item.get("text") or "").strip()
        if not raw:
            continue

        if "start" not in item or "end" not in item:
            raise ValueError(f"Word {index} is missing start/end timestamps.")

        start_ms = seconds_to_ms(item["start"])
        end_ms = seconds_to_ms(item["end"])
        if end_ms <= start_ms:
            raise ValueError(f"Word {index} has end before start.")

        confidence = item.get("confidence") or item.get("probability")
        words.append(
            WordToken(
                id=int(item.get("id") or index),
                raw=raw,
                normalized=str(item.get("normalized") or normalize_word(raw)),
                start_ms=start_ms,
                end_ms=end_ms,
                confidence=float(confidence) if confidence is not None else None,
            )
        )

    return words


def words_to_json(words: list[WordToken], source: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "version": "0.1",
        "words": [word.to_json() for word in words],
    }
    if source:
        payload["source"] = source
    return payload


def write_words_json(words: list[WordToken], output_path: str | Path, source: str | None = None) -> None:
    output = words_to_json(words, source=source)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
