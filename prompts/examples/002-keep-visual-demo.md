# Example: Keep Visual Demo

## Input SRT

```srt
1
00:00:10,000 --> 00:00:13,000
Aquí puedes ver el resultado en pantalla.

2
00:00:13,000 --> 00:00:15,500
...

3
00:00:15,500 --> 00:00:20,000
Fíjate cómo cambia cuando aplicamos el filtro.
```

## Visual Context

```json
[
  {
    "time": "00:00:13.000",
    "description": "Screen recording showing the result of the edit."
  }
]
```

## Expected Output

```json
{
  "remove": [],
  "keep": [
    {
      "start": "00:00:10.000",
      "end": "00:00:20.000",
      "reason": "pause is part of a visual demonstration and should be preserved"
    }
  ]
}
```
