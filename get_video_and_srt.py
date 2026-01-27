import sys

if getattr(sys, "frozen", False):
    import tqdm.std

    def noop(*args, **kwargs):
        pass

    tqdm.std.tqdm.__init__ = noop
    tqdm.std.tqdm.__enter__ = lambda self: self
    tqdm.std.tqdm.__exit__ = noop
    tqdm.std.tqdm.update = noop
    tqdm.std.tqdm.close = noop

import os
import re
import yt_dlp
import traceback
import whisper


# === Handle PyInstaller Frozen Mode ===
if getattr(sys, "frozen", False):
    exe_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    exe_dir = os.path.dirname(__file__)

# 🛠️ Add VLC and ffmpeg to PATH
os.environ["PATH"] = exe_dir + os.pathsep + os.environ.get("PATH", "")

# 🎛️ Set VLC plugin path
vlc_plugin_path = os.path.join(exe_dir, "plugins")
if os.path.exists(vlc_plugin_path):
    os.environ["VLC_PLUGIN_PATH"] = vlc_plugin_path

# 🧠 Whisper asset path
os.environ["WHISPER_ASSETS_DIR"] = os.path.join(exe_dir, "whisper", "assets")

VIDEO_FORMAT = "mp4"
AUDIO_FORMAT = "m4a"


# === Real-time logger ===
class StreamLogger:
    def __init__(self, write_callback=None, total_duration=0):
        self.write_callback = write_callback or (
            lambda x: sys.__stdout__.write(x + "\n")
        )
        self.total_duration = total_duration

    def _format_time(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02}:{m:02}:{s:02}"

    def write(self, text):
        if not text.strip():
            return
        text = text.strip()
        if self.total_duration and text.startswith("[") and "-->" in text:
            match = re.search(r"-->\s*(\d+:\d+\.\d+|\d+:\d+:\d+\.\d+)", text)
            if match:
                ts = match.group(1)
                ts_parts = ts.split(":")
                if len(ts_parts) == 3:
                    h, m, s = ts_parts
                    end_sec = int(h) * 3600 + int(m) * 60 + float(s)
                elif len(ts_parts) == 2:
                    m, s = ts_parts
                    end_sec = int(m) * 60 + float(s)
                else:
                    end_sec = float(ts_parts[0])
                progress = min(end_sec, self.total_duration)
                percent = progress / self.total_duration * 100
                progress_msg = (
                    f"⏳ {self._format_time(progress)} / {self._format_time(self.total_duration)} "
                    f"({percent:.1f}%)"
                )
                try:
                    self.write_callback(progress_msg)
                except Exception:
                    pass
        try:
            self.write_callback(text)
        except Exception:
            pass

    def flush(self):
        pass


# === Subtitle-splitting logic ===
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
            subtitles.append(
                {"start": sentence_start, "end": last_end, "text": current_sentence.strip()}
            )
            current_sentence = ""
            sentence_start = None

    if current_sentence:
        subtitles.append(
            {"start": sentence_start, "end": last_end, "text": current_sentence.strip()}
        )

    return subtitles


# === YouTube transcription ===
def run_transcription(youtube_url, model_size, output_folder, log_callback=print, max_words=15):
    def log(msg):
        log_callback(msg)

    info = yt_dlp.YoutubeDL({"quiet": True}).extract_info(youtube_url, download=False)
    title_safe = re.sub(r"[\\/*?\"<>|:]", "_", info["title"])
    folder_path = os.path.join(output_folder, title_safe)
    os.makedirs(folder_path, exist_ok=True)
    total_duration = info.get("duration") or 0
    log("⏱️ Video length: " + StreamLogger()._format_time(total_duration))

    video_path = os.path.join(folder_path, f"video.{VIDEO_FORMAT}")
    log("📥 Downloading video...")
    with yt_dlp.YoutubeDL(
        {
            "format": "bv*+ba/best",
            "outtmpl": video_path,
            "merge_output_format": "mp4",
            "quiet": True,
            "noplaylist": True,
        }
    ) as ydl:
        ydl.download([youtube_url])

    audio_template = os.path.join(folder_path, "audio.%(ext)s")
    log("🔊 Extracting audio...")
    with yt_dlp.YoutubeDL(
        {
            "format": "bestaudio/best",
            "outtmpl": audio_template,
            "quiet": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": AUDIO_FORMAT,
                }
            ],
        }
    ) as ydl:
        ydl.download([youtube_url])

    audio_file = audio_template.replace("%(ext)s", AUDIO_FORMAT)
    return _transcribe_media(
        audio_file, folder_path, model_size, log_callback, max_words, total_duration
    )


# === Local file transcription ===
def run_local_transcription(media_path, model_size, output_folder, log_callback=print, max_words=15):
    title_safe = re.sub(
        r"[\\/*?\"<>|:]", "_", os.path.splitext(os.path.basename(media_path))[0]
    )
    folder_path = os.path.join(output_folder, title_safe)
    os.makedirs(folder_path, exist_ok=True)

    return _transcribe_media(
        media_path, folder_path, model_size, log_callback, max_words, total_duration=0
    )


# === Shared transcription pipeline ===
def _transcribe_media(media_path, folder_path, model_size, log_callback, max_words, total_duration):
    def log(msg):
        log_callback(msg)

    try:
        log(f"🧠 Loading Whisper model ({model_size})...")
        model = whisper.load_model(model_size)
    except Exception as e:
        log(str(e))
        log(traceback.format_exc())
        return

    log("📄 Transcribing...")
    original_stdout = sys.stdout
    sys.stdout = StreamLogger(log_callback, total_duration)
    try:
        result = model.transcribe(media_path, word_timestamps=True, verbose=True)
    finally:
        sys.stdout = original_stdout

    word_dict = {}
    for seg in result["segments"]:
        for w in seg.get("words", []):
            word_dict[(round(w["start"], 3), round(w["end"], 3))] = w["word"].strip()

    subtitles = split_subtitles(word_dict, max_words)

    def ts(sec):
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        ms = int((sec % 1) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    srt_path = os.path.join(folder_path, "subtitle.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, sub in enumerate(subtitles, 1):
            f.write(f"{i}\n{ts(sub['start'])} --> {ts(sub['end'])}\n{sub['text']}\n\n")

    log("✅ Subtitles saved.")
    return folder_path


# === CLI ===
if __name__ == "__main__":
    import argparse

    def print_line(text):
        sys.__stdout__.write(text + "\n")
        sys.__stdout__.flush()

    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="YouTube URL")
    parser.add_argument("--file", help="Local media file path")
    parser.add_argument("--model_size", default="turbo")
    parser.add_argument("--output_folder", default="outputs")

    args = parser.parse_args()

    if args.url:
        run_transcription(args.url, args.model_size, args.output_folder, print_line)
    elif args.file:
        run_local_transcription(args.file, args.model_size, args.output_folder, print_line)
    else:
        print_line("❌ Please specify --url or --file")
