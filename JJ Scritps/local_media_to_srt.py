import os
import sys
import re
import argparse
import traceback
import whisper


# ========= Subtitle splitting logic (same idea as your script) =========
def split_subtitles(word_dict, max_words=15):
    subtitles = []
    current_sentence = ""
    sentence_start = None
    last_end = None

    for (start, end), word in sorted(word_dict.items()):
        if sentence_start is None:
            sentence_start = start
        current_sentence += " " + word
        last_end = end

        strong_punct = r"[.?!]$"
        soft_punct = r"[,;:]$"
        words_count = len(current_sentence.split())
        end_sentence = False

        if re.search(strong_punct, word) and words_count >= 3:
            end_sentence = True
        elif re.search(soft_punct, word) and words_count >= max_words:
            end_sentence = True

        if end_sentence:
            subtitles.append({
                "start": sentence_start,
                "end": last_end,
                "text": current_sentence.strip(),
            })
            current_sentence = ""
            sentence_start = None

    if current_sentence:
        subtitles.append({
            "start": sentence_start,
            "end": last_end,
            "text": current_sentence.strip(),
        })

    return subtitles


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


# ========= Core function =========
def transcribe_local_media(
    media_path: str,
    model_size: str = "turbo",
    output_srt: str | None = None,
    max_words: int = 15,
):
    if not os.path.exists(media_path):
        raise FileNotFoundError(f"File not found: {media_path}")

    if output_srt is None:
        base, _ = os.path.splitext(media_path)
        output_srt = base + ".srt"

    try:
        print(f"🧠 Loading Whisper model: {model_size}")
        model = whisper.load_model(model_size)

        print("📄 Transcribing (word_timestamps=True)...")
        result = model.transcribe(
            media_path,
            word_timestamps=True,
            verbose=True,
        )

    except Exception as e:
        print("❌ Transcription failed:")
        print(str(e))
        print(traceback.format_exc())
        return

    # Collect words
    word_dict = {}
    for segment in result.get("segments", []):
        for word in segment.get("words", []):
            start = round(word["start"], 3)
            end = round(word["end"], 3)
            text = word["word"].strip()
            word_dict[(start, end)] = text

    subtitles = split_subtitles(word_dict, max_words)

    with open(output_srt, "w", encoding="utf-8") as f:
        for idx, sub in enumerate(subtitles, 1):
            f.write(
                f"{idx}\n"
                f"{format_timestamp(sub['start'])} --> {format_timestamp(sub['end'])}\n"
                f"{sub['text']}\n\n"
            )

    print(f"✅ SRT generated: {output_srt}")


# ========= CLI =========
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Transcribe a local audio/video file into SRT using Whisper"
    )
    parser.add_argument(
                    "media",
                    nargs="?",
                    default="video.mp4",
                    help="Local media file (mp4 / mp3 / wav / m4a)",
    )
    parser.add_argument(
        "--model",
        default="base",
        help="Whisper model (tiny, base, small, medium, large, turbo)",
    )
    parser.add_argument(
        "--max_words",
        type=int,
        default=15,
        help="Max words before soft punctuation split",
    )
    parser.add_argument(
        "--out",
        help="Output SRT path (default: same name as input)",
    )

    args = parser.parse_args()

    transcribe_local_media(
        media_path=args.media,
        model_size=args.model,
        output_srt=args.out,
        max_words=args.max_words,
    )
