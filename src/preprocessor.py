def _remove_consecutive_duplicate_words(text: str) -> str:
    """
    Remove consecutively repeated words AND phrases (stutter correction).

    Uses a multi-pass approach: each pass finds and collapses the longest
    consecutive repeated phrase at every position, repeating until stable.

    Examples:
        "हाँ हाँ हाँ बोलो"     → "हाँ बोलो"
        "okay okay क्या बात"   → "okay क्या बात"
        "ठीक है ठीक है ठीक है" → "ठीक है"
        "yes yes yes"          → "yes"
    """
    def _norm(w: str) -> str:
        return w.lower().strip(".,!?")

    words = text.split()
    if not words:
        return text

    changed = True
    while changed:
        changed = False
        i = 0
        n = len(words)
        new_words: list = []
        while i < n:
            max_phrase = (n - i) // 2
            matched = 0
            for phrase_len in range(max_phrase, 0, -1):
                phrase = [_norm(w) for w in words[i: i + phrase_len]]
                nxt = [_norm(w) for w in words[i + phrase_len: i + 2 * phrase_len]]
                if phrase == nxt:
                    matched = phrase_len
                    break
            if matched:
                new_words.extend(words[i: i + matched])  # keep first occurrence
                i += matched * 2                          # skip the duplicate
                changed = True
            else:
                new_words.append(words[i])
                i += 1
        words = new_words

    return " ".join(words)


def preprocess(segments: list) -> str:
    """
    Clean raw transcript segments and return a formatted dialogue string.

    Speaker roles (Agent / Customer) are intentionally NOT assigned here.
    Gemini determines who is the agent based on conversational context.

    Args:
        segments: List of utterance dicts with keys:
                  speaker, start, stop, transcription

    Returns:
        Clean dialogue string, e.g.:
            SPEAKER_00: हेलो सर मैं अभिषेक बोल रहा हूँ व्यापार से
            SPEAKER_01: हाँ बोलो क्या बात है
    """
    if not segments:
        return ""

    # Step 1: Sort by start time
    utterances = sorted(segments, key=lambda x: x.get("start", 0))

    # Step 2: Apply stutter correction to each utterance
    cleaned = []
    for u in utterances:
        text = u.get("transcription", "").strip()
        text = _remove_consecutive_duplicate_words(text)
        if text:
            cleaned.append({**u, "transcription": text})

    if not cleaned:
        return ""

    merged = [cleaned[0].copy()]
    for current in cleaned[1:]:
        previous = merged[-1]
        gap = current.get("start", 0) - previous.get("stop", 0)
        same_speaker = current.get("speaker") == previous.get("speaker")

        if same_speaker and gap <= 1.5:
            merged[-1]["transcription"] = (
                previous["transcription"].rstrip() + " " + current["transcription"].strip()
            )
            merged[-1]["stop"] = current.get("stop", previous.get("stop"))
        else:
            merged.append(current.copy())

    # Step 4: Build dialogue string using original speaker IDs
    lines = []
    for u in merged:
        speaker_id = u.get("speaker", "UNKNOWN").strip()
        text = u.get("transcription", "").strip()
        if text:
            lines.append(f"{speaker_id}: {text}")

    return "\n".join(lines)


def get_call_duration(segments: list) -> float:
    """
    Return the total call duration in seconds from utterance timestamps.

    Args:
        segments: Raw list of utterance dicts

    Returns:
        Duration in seconds, rounded to 2 decimal places. 0.0 if empty.
    """
    if not segments:
        return 0.0

    earliest = min(u.get("start", 0) for u in segments)
    latest = max(u.get("stop", 0) for u in segments)
    return round(latest - earliest, 2)
