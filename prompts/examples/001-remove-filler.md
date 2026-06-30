# Example: Remove Filler

## Input SRT

```srt
1
00:00:00,000 --> 00:00:02,000
Eh... bueno, vamos a empezar.

2
00:00:02,000 --> 00:00:06,000
Hoy te voy a enseñar cómo automatizar cortes de video.
```

## Expected Output

```json
{
  "remove": [
    {
      "start": "00:00:00.000",
      "end": "00:00:02.000",
      "reason": "filler intro before the actual topic starts"
    }
  ],
  "keep": [
    {
      "start": "00:00:02.000",
      "end": "00:00:06.000",
      "reason": "clear start of useful content"
    }
  ]
}
```
