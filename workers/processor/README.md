# Processor Worker

This worker will handle the video pipeline:

1. Receive a video job.
2. Extract audio.
3. Generate SRT.
4. Extract key frames.
5. Send transcript and visual context to the AI editor.
6. Validate suggested cuts.
7. Export preview/final video with FFmpeg.

Initial implementation can be local and manual before becoming a hosted worker.
