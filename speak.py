# speak.py
"""
Cross-platform text-to-speech using pyttsx3 (offline, Windows SAPI5).
Default voice: Microsoft Zira Desktop (female US English).
"""
import re
import threading
import time
import pyttsx3


# --- Configure your preferred voice here ---
VOICE_NAME = "Zira"  # e.g. "Zira" or "David"
DEFAULT_VOICE_NAME = f"Microsoft {VOICE_NAME} Desktop"
DEFAULT_RATE = 150          # words per minute (150-200 natural)
DEFAULT_VOLUME = 1.0        # 0.0 to 1.0


# ---------- Public API ----------

def speak(text: str, rate: int | None = None, volume: float | None = None,
          block: bool = True) -> None:
    """Speak text using the default voice (Zira)."""
    clean = _clean_text(text)
    if not clean:
        return
    rate = rate if rate is not None else DEFAULT_RATE
    volume = volume if volume is not None else DEFAULT_VOLUME
    voice_id = _resolve_default_voice_id()

    if block:
        _speak_sync(clean, voice_id, rate, volume)
    else:
        threading.Thread(
            target=_speak_sync, args=(clean, voice_id, rate, volume), daemon=False
        ).start()


def speak_with_voice(text: str, voice_id: str, rate: int = 175,
                     volume: float = 1.0, block: bool = True) -> None:
    """Speak using a specific voice ID."""
    clean = _clean_text(text)
    if not clean:
        return
    if block:
        _speak_sync(clean, voice_id, rate, volume)
    else:
        threading.Thread(
            target=_speak_sync, args=(clean, voice_id, rate, volume), daemon=False
        ).start()


def list_voices() -> list[dict]:
    """Return available voices."""
    try:
        engine = pyttsx3.init("sapi5")
        voices = engine.getProperty("voices")
        result = []
        for v in voices:
            result.append({
                "id": v.id,
                "name": v.name,
                "gender": getattr(v, "gender", "unknown"),
                "languages": [
                    l.decode() if isinstance(l, bytes) else str(l)
                    for l in getattr(v, "languages", [])
                ],
            })
        engine.stop()
        return result
    except Exception as e:
        print(f"[speak] failed to list voices: {e}")
        return []


# ---------- Internal ----------

def _resolve_default_voice_id() -> str | None:
    """Find voice ID matching DEFAULT_VOICE_NAME. Cache for speed."""
    global _CACHED_VOICE_ID
    if _CACHED_VOICE_ID is not None:
        return _CACHED_VOICE_ID
    try:
        engine = pyttsx3.init("sapi5")
        for v in engine.getProperty("voices"):
            if DEFAULT_VOICE_NAME.lower() in v.name.lower():
                _CACHED_VOICE_ID = v.id
                engine.stop()
                return v.id
        engine.stop()
    except Exception:
        pass
    _CACHED_VOICE_ID = None
    return None


_CACHED_VOICE_ID: str | None = None


def _speak_sync(text: str, voice_id: str | None, rate: int, volume: float) -> None:
    try:
        engine = pyttsx3.init("sapi5")
        if voice_id:
            engine.setProperty("voice", voice_id)
        engine.setProperty("rate", int(rate))
        engine.setProperty("volume", float(volume))
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        time.sleep(0.3)
    except Exception as e:
        print(f"[speak] error: {e}")


def _clean_text(text: str) -> str:
    """Strip markdown, citations, and URLs for natural-sounding speech."""
    if not text:
        return ""

    # Strip inline citations in any of these bracket styles:
    #   [file, p.1]        (ASCII square)
    #   【file, p.1】       (CJK / full-width)
    #   ［file, p.1］       (full-width square)
    #   （file, p.1）       (full-width round)
    #   (file, p.1)        (ASCII round — only if it looks like a citation)
    text = re.sub(r"【[^】]*】", "", text)
    text = re.sub(r"［[^］]*］", "", text)
    text = re.sub(r"（[^）]*）", "", text)
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"\([^)]*\.(?:md|py|sql|pdf|txt|ipynb|json|csv)[^)]*\)", "", text)

    # Remove markdown links [label](url) -> label
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove raw URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove markdown emphasis and code ticks
    text = re.sub(r"[*_`#]+", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------- CLI test ----------

if __name__ == "__main__":
    print("Configured default voice:", DEFAULT_VOICE_NAME)
    print("\nAll voices on this machine:\n")
    for v in list_voices():
        marker = "  ← DEFAULT" if DEFAULT_VOICE_NAME.lower() in v["name"].lower() else ""
        print(f"  {v['name']}{marker}")
        print(f"    id: {v['id']}")
        print()

    print("Speaking test with default voice...")
    speak("Hello. I am Zira, your document assistant.")
    print("Done.")