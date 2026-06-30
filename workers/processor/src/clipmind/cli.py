from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .analyzer import analyze_segments
from .srt import parse_srt
from .validator import validate_cuts_json


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

    output = json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output + "\n", encoding="utf-8")
        print(f"cuts.json written to {output_path}")
    else:
        print(output)

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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
