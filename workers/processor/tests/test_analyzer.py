import json
from pathlib import Path

from clipmind.analyzer import analyze_segments
from clipmind.srt import parse_srt, timestamp_to_ms
from clipmind.validator import validate_cuts_json


SAMPLE_SRT = """1
00:00:00,000 --> 00:00:02,000
Eh... bueno, vamos a empezar.

2
00:00:02,000 --> 00:00:06,000
Hoy te voy a enseñar cómo automatizar cortes de video.

3
00:00:06,000 --> 00:00:08,500
No, espera, déjame repetir eso.
"""


def test_parse_srt_segments():
    segments = parse_srt(SAMPLE_SRT)
    assert len(segments) == 3
    assert segments[0].start == "00:00:00.000"
    assert segments[0].end == "00:00:02.000"
    assert segments[1].text.startswith("Hoy te voy")


def test_timestamp_to_ms_accepts_comma_and_dot():
    assert timestamp_to_ms("00:00:02,500") == 2500
    assert timestamp_to_ms("00:00:02.500") == 2500


def test_analyze_returns_valid_json_shape():
    segments = parse_srt(SAMPLE_SRT)
    payload = analyze_segments(segments)
    errors = validate_cuts_json(payload)
    assert errors == []
    assert payload["remove"]
    assert payload["keep"]
    json.dumps(payload)


def test_analyzer_removes_filler_and_false_start():
    segments = parse_srt(SAMPLE_SRT)
    payload = analyze_segments(segments)
    reasons = " ".join(item["reason"] for item in payload["remove"])
    assert "filler" in reasons
    assert "false start" in reasons
