# Architecture

## Pipeline

```text
video upload
  -> ffmpeg extract audio
  -> whisper transcribe SRT
  -> ffmpeg extract key frames
  -> vision model describes frames
  -> editor model proposes cuts
  -> validator checks JSON/timestamps
  -> ffmpeg creates preview
  -> reviewer model checks preview transcript/cuts
  -> final ffmpeg export
```

## Components

### Web App

Responsibilities:

- Upload video.
- Show job status.
- Show suggested cuts.
- Let user accept/reject edits.
- Preview final result.

### Processor Worker

Responsibilities:

- Run FFmpeg.
- Run transcription.
- Extract frames.
- Call AI editor/reviewer.
- Validate output.
- Export video.

### AI Editor

Input:

- SRT transcript.
- Optional frame descriptions.
- Editing mode.

Output:

- JSON cut suggestions.
- Reasons for each cut.

### AI Reviewer

Input:

- Original SRT.
- Applied cuts.
- Preview transcript.

Output:

- Pass/fail.
- Issues.
- Suggested corrections.
