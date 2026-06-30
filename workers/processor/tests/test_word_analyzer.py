import json

from clipmind.word_analyzer import analyze_words
from clipmind.words import parse_words_payload


SAMPLE_WORDS = {
    "words": [
        {"word": "Eh", "start": 0.00, "end": 0.25},
        {"word": "bueno", "start": 0.25, "end": 0.70},
        {"word": "hoy", "start": 1.00, "end": 1.20},
        {"word": "vamos", "start": 1.20, "end": 1.55},
        {"word": "ummm", "start": 1.90, "end": 2.60},
        {"word": "a", "start": 2.70, "end": 2.80},
        {"word": "probar", "start": 2.80, "end": 3.20},
        {"word": "No", "start": 4.00, "end": 4.20},
        {"word": "espera", "start": 4.20, "end": 4.70},
    ]
}


def test_parse_words_payload_normalizes_words():
    words = parse_words_payload(SAMPLE_WORDS)
    assert len(words) == 9
    assert words[0].normalized == "eh"
    assert words[4].start == "00:00:01.900"


def test_analyze_words_returns_candidates():
    words = parse_words_payload(SAMPLE_WORDS)
    payload = analyze_words(words)
    assert payload["source_type"] == "word_timestamps"
    assert payload["summary"]["words"] == 9
    assert payload["remove"]
    assert any(item["type"] in {"filler_word", "filler_phrase", "merged_candidate"} for item in payload["remove"])
    assert any("false start" in item["reason"] for item in payload["remove"])
    json.dumps(payload)


def test_silence_gap_is_detected():
    words = parse_words_payload(SAMPLE_WORDS)
    payload = analyze_words(words)
    assert any(item["type"] == "silence_gap" for item in payload["candidates"])
