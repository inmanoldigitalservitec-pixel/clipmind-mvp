# Local Whisper word-timestamp test

This backend is prepared for local Whisper testing with word-level timestamps.

The important file is not SRT anymore. The important file is:

```text
outputs/transcript_words.json
```

That file contains every spoken word with `start` and `end` time.

## 1. Install local transcription dependency

From the repo root:

```bash
cd workers/processor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -r requirements-whisper.txt
```

## 2. Extract audio from a video

```bash
mkdir -p outputs
ffmpeg -i input.mp4 -vn -ac 1 -ar 16000 outputs/audio.wav
```

## 3. Transcribe locally with word timestamps

Fast first test:

```bash
PYTHONPATH=src python -m clipmind.cli transcribe \
  --audio outputs/audio.wav \
  --output outputs/transcript_words.json \
  --model base \
  --language es \
  --pretty
```

Better quality later:

```bash
PYTHONPATH=src python -m clipmind.cli transcribe \
  --audio outputs/audio.wav \
  --output outputs/transcript_words.json \
  --model medium \
  --language es \
  --pretty
```

For highest local quality, try:

```bash
PYTHONPATH=src python -m clipmind.cli transcribe \
  --audio outputs/audio.wav \
  --output outputs/transcript_words.json \
  --model large-v3 \
  --language es \
  --pretty
```

## 4. Generate candidate cuts from words

```bash
PYTHONPATH=src python -m clipmind.cli analyze-words \
  --words outputs/transcript_words.json \
  --output outputs/candidate_cuts.json \
  --pretty
```

## 5. Test without Whisper

Use the simulated word timestamp fixture:

```bash
PYTHONPATH=src python -m clipmind.cli analyze-words \
  --words examples/sample_words.json \
  --output outputs/candidate_cuts.json \
  --pretty
```

## Current behavior

The word analyzer detects:

- filler words: `eh`, `ummm`, `mmm`, `este`
- filler phrases: `o sea`, `eh bueno`, `y bueno`
- false starts: `no espera`, `déjame repetir`, `déjame decirlo mejor`, `lo digo otra vez`, `toma salió mal`
- silence gaps between words

The output has:

```json
{
  "candidates": [],
  "remove": [],
  "review": []
}
```

`remove` means the system thinks the cut can probably be applied.

`review` means the system detected something suspicious but should not auto-cut yet.
