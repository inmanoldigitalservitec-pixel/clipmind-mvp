from __future__ import annotations

from dataclasses import dataclass
import re


_TIME_RE = re.compile(
    r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})(?P<sep>[,.])(?P<ms>\d{3})"
)


@dataclass(frozen=True)
class SrtSegment:
    index: int
    start_ms: int
    end_ms: int
    text: str

    @property
    def start(self) -> str:
        return ms_to_timestamp(self.start_ms)

    @property
    def end(self) -> str:
        return ms_to_timestamp(self.end_ms)

    @property
    def duration_ms(self) -> int:
        return max(0, self.end_ms - self.start_ms)


def timestamp_to_ms(value: str) -> int:
    match = _TIME_RE.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Invalid SRT timestamp: {value!r}")
    return (
        int(match.group("h")) * 3_600_000
        + int(match.group("m")) * 60_000
        + int(match.group("s")) * 1_000
        + int(match.group("ms"))
    )


def ms_to_timestamp(ms: int) -> str:
    if ms < 0:
        raise ValueError("Timestamp cannot be negative")
    hours, rem = divmod(ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


def parse_srt(content: str) -> list[SrtSegment]:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    blocks = re.split(r"\n\s*\n", normalized)
    segments: list[SrtSegment] = []

    for fallback_index, block in enumerate(blocks, start=1):
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if len(lines) < 2:
            continue

        index = fallback_index
        time_line_pos = 0
        if lines[0].isdigit():
            index = int(lines[0])
            time_line_pos = 1

        if time_line_pos >= len(lines) or "-->" not in lines[time_line_pos]:
            continue

        start_raw, end_raw = [part.strip() for part in lines[time_line_pos].split("-->", 1)]
        start_ms = timestamp_to_ms(start_raw)
        end_ms = timestamp_to_ms(end_raw)
        text = " ".join(lines[time_line_pos + 1 :]).strip()

        if end_ms <= start_ms:
            raise ValueError(f"Segment {index} has end before start")

        segments.append(SrtSegment(index=index, start_ms=start_ms, end_ms=end_ms, text=text))

    return segments
