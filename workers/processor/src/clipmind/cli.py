from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .analyzer import analyze_segments
from .srt import parse_srt
from .validator import validate_cuts_json
from .word_analyzer import analyze_words
from .words import load_words_json


def _write_or_print(payload: dict, output_path: str | None, pretty: bool = False, label: str = "output") -> None:
    output = json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None)
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output + "\n", encoding="utf-8")
        print(f"{label} written to {path}")
    else:
        print(output)


def analyze_command(args: argparse.Namespace) -> int:
    srt_path = Path(args.srt)
    if not srt_path.exists():
        print(f"SRT file not found: {srt_path}", file=sys.stderr)
        return 2

    content = srt_path.read_text(encoding="utf-8")
    segments = parse_srt(content)
    payload = analyze_segments(segments, mode=args.mode)
    payload["source"] = {
        "srt": str(srt_path),
        "segments": len(segments),
    }

    errors = validate_cuts_json(payload)
    if errors:
        print("Invalid cuts JSON:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    _write_or_print(payload, args.output, pretty=args.pretty, label="cuts.json")
    return 0


def analyze_words_command(args: argparse.Namespace) -> int:
    words_path = Path(args.words)
    if not words_path.exists():
        print(f"Words JSON file not found: {words_path}", file=sys.stderr)
        return 2

    words = load_words_json(words_path)
    payload = analyze_words(words, mode=args.mode)
    payload["source"] = {
        "words_json": str(words_path),
        "words": len(words),
    }

    _write_or_print(payload, args.output, pretty=args.pretty, label="candidate_cuts.json")
    return 0


def extract_audio_command(args: argparse.Namespace) -> int:
    try:
        from .media import extract_audio

        output_path = extract_audio(args.video, args.output, sample_rate=args.sample_rate)
    except Exception as exc:
        print(f"Audio extraction failed: {exc}", file=sys.stderr)
        return 1

    print(f"audio.wav written to {output_path}")
    return 0


def transcribe_command(args: argparse.Namespace) -> int:
    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"Audio file not found: {audio_path}", file=sys.stderr)
        return 2

    try:
        from .transcribe_local import transcribe_with_faster_whisper

        payload = transcribe_with_faster_whisper(
            audio_path=audio_path,
            model_size=args.model,
            language=args.language,
            device=args.device,
            compute_type=args.compute_type,
        )
    except Exception as exc:
        print(f"Local transcription failed: {exc}", file=sys.stderr)
        return 1

    _write_or_print(payload, args.output, pretty=args.pretty, label="transcript_words.json")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="clipmind", description="ClipMind processor CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze an SRT file and return valid cut JSON")
    analyze.add_argument("--srt", required=True, help="Path to the input .srt file")
    analyze.add_argument("--output", help="Optional path to write cuts.json")
    analyze.add_argument("--mode", default="clean_cut", choices=["clean_cut", "clip_finder", "tighten_pacing"])
    analyze.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    analyze.set_defaults(func=analyze_command)

    analyze_words_parser = subparsers.add_parser(
        "analyze-words",
        help="Analyze word-level timestamps and return candidate cuts JSON",
    )
    analyze_words_parser.add_argument("--words", required=True, help="Path to transcript_words.json")
    analyze_words_parser.add_argument("--output", help="Optional path to write candidate_cuts.json")
    analyze_words_parser.add_argument("--mode", default="clean_cut", choices=["clean_cut", "clip_finder", "tighten_pacing"])
    analyze_words_parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    analyze_words_parser.set_defaults(func=analyze_words_command)

    extract_audio_parser = subparsers.add_parser(
        "extract-audio",
        help="Extract mono 16 kHz audio from a video using FFmpeg",
    )
    extract_audio_parser.add_argument("--video", required=True, help="Path to input video file")
    extract_audio_parser.add_argument("--output", default="outputs/audio.wav", help="Path to write audio.wav")
    extract_audio_parser.add_argument("--sample-rate", type=int, default=16000, help="Audio sample rate")
    extract_audio_parser.set_defaults(func=extract_audio_command)

    transcribe = subparsers.add_parser(
        "transcribe",
        help="Transcribe audio locally with faster-whisper and write word-level timestamps",
    )
    transcribe.add_argument("--audio", required=True, help="Path to audio file, for example outputs/audio.wav")
    transcribe.add_argument("--output", default="outputs/transcript_words.json", help="Path to write transcript_words.json")
    transcribe.add_argument("--model", default="base", help="faster-whisper model size, for example base, small, medium, large-v3")
    transcribe.add_argument("--language", default="es", help="Speech language code")
    transcribe.add_argument("--device", default="auto", help="Device override, for example cpu or cuda")
    transcribe.add_argument("--compute-type", default="auto", help="Compute type override, for example int8 or float16")
    transcribe.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    transcribe.set_defaults(func=transcribe_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
