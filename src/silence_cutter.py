def compute_keep_segments(
    words: list[dict],
    total_duration: float,
    padding: float = 0.08,
    min_silence: float = 0.25,
) -> list[tuple[float, float]]:
    """Compute segments to keep by merging words and respecting padding and minimum silence."""
    valid_words = [w for w in words if w.get("start") is not None and w.get("end") is not None]
    valid_words.sort(key=lambda w: w["start"])
    if not valid_words:
        return []

    segments = []
    current_start = max(0.0, valid_words[0]["start"] - padding)
    current_end = min(total_duration, valid_words[0]["end"] + padding)
    last_speech_end = valid_words[0]["end"]

    for i in range(1, len(valid_words)):
        start_i = max(0.0, valid_words[i]["start"] - padding)
        end_i = min(total_duration, valid_words[i]["end"] + padding)

        silence_gap = valid_words[i]["start"] - last_speech_end

        if silence_gap < min_silence or start_i <= current_end:
            current_end = max(current_end, end_i)
            last_speech_end = max(last_speech_end, valid_words[i]["end"])
        else:
            segments.append((current_start, current_end))
            current_start = start_i
            current_end = end_i
            last_speech_end = valid_words[i]["end"]

    segments.append((current_start, current_end))
    return segments
