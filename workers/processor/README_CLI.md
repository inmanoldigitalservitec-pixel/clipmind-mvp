# ClipMind Processor CLI

This is the first backend milestone for ClipMind.

It takes an SRT transcript and returns valid JSON with suggested cuts.

## Run locally

From the repository root:

```bash
cd workers/processor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=src python -m clipmind.cli analyze --srt examples/sample.srt --pretty
```

Write the result to a file:

```bash
PYTHONPATH=src python -m clipmind.cli analyze \
  --srt examples/sample.srt \
  --output outputs/cuts.json \
  --pretty
```

## Current behavior

The first version is rule-based. It detects:

- filler intros
- empty or low-information speech
- false starts
- self-corrections
- repeated adjacent ideas

Later this same CLI will call the AI editor prompt instead of using only rules.

## Output

The command returns a JSON object with:

```json
{
  "version": "0.1",
  "mode": "clean_cut",
  "remove": [],
  "keep": [],
  "warnings": [],
  "source": {
    "srt": "examples/sample.srt",
    "segments": 5
  }
}
```
