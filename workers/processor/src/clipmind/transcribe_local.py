from __future__ import annotations

from pathlib import Path
from typing import Any

from .words import WordToken, normalize_word, write_words_json


def transcribe_with_faster_whisper(
    audio_path: str | Path,
    model_size: str = "base",
    language: str = "es",
    device: str = "auto",
    compute_type: str = "auto",
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Transcribe audio locally with faster-whisper and return word-level timestamps.

    This function imports faster_whisper lazily so the normal test suite can run
    without installing heavy Whisper dependencies.
    """

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is not installed. Install it with: "
            "pip install -r requirements-whisper.txt"
        ) from exc

    audio = Path(audio_path)
    if not audio.exists():
        raise FileNotFoundError(f"Audio file not found: {audio}")

    model_kwargs: dict[str, Any] = {}
    if device != "auto":
        model_kwargs["device"] = device
    if compute_type != "auto":
        model_kwargs["compute_type"] = compute_type

    model = WhisperModel(model_size, **model_kwargs)
    segments, info = model.transcribe(
        str(audio),
        language=language,
        word_timestamps=True,
        vad_filter=True,
    )

    words: list[WordToken] = []
    word_id = 1
    segment_payloads: list[dict[str, Any]] = []

    for segment in segments:
        segment_words: list[dict[str, Any]] = []
        for item in segment.words or []:
            raw = str(item.word).strip()
            if not raw:
                continue
            token = WordToken(
                id=word_id,
                raw=raw,
                normalized=normalize_word(raw),
                start_ms=int(round(float(item.start) * 1000)),
                end_ms=int(round(float(item.end) * 1000)),
                confidence=float(item.probability) if item.probability is not None else None,
            )
            words.append(token)
            segment_words.append(token.to_json())
            word_id += 1

        segment_payloads.append(
            {
                "id": len(segment_payloads) + 1,
                "start": float(segment.start),
                "end": float(segment.end),
                "text": segment.text.strip(),
                "words": segment_words,
            }
        )

    payload: dict[str, Any] = {
        "version": "0.1",
        "engine": "faster-whisper",
        "model": model_size,
        "language": getattr(info, "language", language),
        "language_probability": getattr(info, "language_probability", None),
        "duration": getattr(info, "duration", None),
        "source": str(audio),
        "words": [word.to_json() for word in words],
        "segments": segment_payloads,
    }

    if output_path:
        write_words_json(words, output_path, source=str(audio))

    return payload
