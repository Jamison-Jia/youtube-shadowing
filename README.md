# 🎧 English Shadowing Tool with YouTube Videos

https://github.com/user-attachments/assets/9ad33f2a-5754-485c-98d6-6fedfd32f06e


Practice your English listening, speaking, and shadowing skills using real YouTube videos with subtitles — powered by Whisper AI and VLC. This tool runs Whisper locally, so there's no need to use the OpenAI API, making it completely free to use!

If you don't want to install all the dependencies and just want a standalone application, simply download `shadowing.exe` from the [Releases page](https://github.com/blacksnail789521/youtube-shadowing/releases). It's ready to use for Windows, but note that GPU support is not available.

---

## 🛠️ Features

- 🎥 Download any YouTube video with subtitles
- 🧠 Auto-generate SRT subtitles using OpenAI Whisper
- ✂️ Split sentences using punctuation for effortless English shadowing
- 🗂 Organize videos in your local `youtube_videos/` folder
- ⏯ Interactive GUI for video playback and subtitle shadowing
- ⏪ Quick subtitle repeat, skip, and looping for focused practice
- 🔁 Loop individual subtitles to mimic pronunciation
- ⏱ Playback speed control (slow down or speed up)
- 🎹 Keyboard shortcuts for fast navigation
- 🎙 Record your voice while shadowing for self-assessment

---

## 📦 Installation

### 1. Clone the repo

```bash
git clone https://github.com/your-username/youtube-shadowing.git
cd youtube-shadowing
```

### 2. Install requirements

Make sure you’re using Python 3.9+ and install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Install VLC

Make sure VLC Media Player is installed on your system. You can download it from the [official VLC website](https://www.videolan.org/vlc/).

- On Windows: Download and run the installer.
- On macOS: Download the `.dmg` file and drag VLC to your Applications folder.
- On Linux: Use your package manager, e.g., `sudo apt install vlc` on Ubuntu.

VLC is required for video playback functionality.


### 4. Install FFmpeg

FFmpeg is required for processing audio and video files. Follow the steps below to install it:

- **On Windows**:
  1. Download the FFmpeg zip file from the [official FFmpeg website](https://ffmpeg.org/download.html).
  2. Extract the zip file to a folder.
  3. Copy the `ffmpeg.exe` file from the extracted `bin` folder and place it under this repository's directory.

- **On macOS**:
  Use Homebrew to install FFmpeg:
  ```bash
  brew install ffmpeg
  ```

- **On Linux**:
  Use your package manager to install FFmpeg, e.g., on Ubuntu:
  ```bash
  sudo apt install ffmpeg
  ```

Make sure FFmpeg is accessible from the command line by running:
```bash
ffmpeg -version
```

If the command outputs the FFmpeg version, the installation was successful.

### 5. (Optional) Run `build.py` for Standalone Build

If you prefer a simpler way to create a standalone executable, you can use the provided `build.py` script:

```bash
python build.py
```

This script automates the process of creating a standalone executable for your platform. After running the script, you will get:

| Platform | Output File                         |
| -------- | ----------------------------------- |
| Windows  | `.exe` file                       |
| macOS    | `.app` or Unix-style executable   |
| Linux    | Linux executable (e.g., ELF binary) |

The generated file will be located in the project directory, ready to use.

---

## 🚀 How to Use

### Step 1: Launch the App

After building the standalone executable, simply double-click the `shadowing.exe` file to launch the application.

Alternatively, if you want to leverage GPU support, you can run the app directly using Python:

```bash
python gui.py
```

### Step 2: Paste a YouTube URL

- In the GUI, paste a YouTube link and press **Enter**
- The video and its audio will be downloaded
- Subtitles will be auto-generated and stored in `youtube_videos/`

### Step 3: Start Shadowing!

- Select a video from the list
- Use shortcut keys to control playback and shadow efficiently:
  - `←/→`: Seek 5 seconds
  - `Space`: Play / Pause
  - `A`: Previous subtitle
  - `S`: Repeat subtitle
  - `D`: Next subtitle
  - `L`: Toggle subtitle looping

---

## 📁 Folder Structure

```
youtube_videos/
├── [video title]/
│   ├── video.mp4
│   ├── subtitle.srt
```

Each downloaded video gets its own folder.

---

## 🛠 Developer Notes

This project has two core files:

- `gui.py`: GUI app to play and interact with videos + subtitles
- `get_video_and_srt.py`: Backend script to download + transcribe videos (supports both CPU and GPU, but runs significantly faster on GPU)
  You can run the script directly if you just want to download a YouTube video and generate SRT subtitles from a URL:

```bash
python get_video_and_srt.py "https://www.youtube.com/watch?v=..."
```

This will download the video and save it along with the generated subtitles in the `youtube_videos/` folder.

---

## ❤️ Contributing

Pull requests and ideas are welcome!
Feel free to open an issue or share feedback.

If you find this project helpful, remember to ⭐ star the repository to show your support!

---

### Happy Shadowing! 🎤📺

## Python config
* Install Python
https://www.python.org/downloads/windows/
  ```powershell
  python -m venv .venv
  .venv\Scripts\activate

  ```
  确认版本
  ```powershell
  python --version
  # Python 3.10.x
  ```
* 安装 PyTorch（CPU 版即可）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu


  验证：

  ```powershell
  python -c "import torch; print(torch.__version__)"
  ```
* Install Whisper
  ```powershell
  pip install -U openai-whisper
  ```
  验证
  ```powershell
  python -c "import whisper; print('ok')"
  ```

## Extract srt from local media
### Default calling
  * Name the media file to ```video.mp4```
  * Use the CLI to call the script by ```Python local_media_to_srt.py```
### Explit convert arguments
  
  ```
  python local_media_to_srt.py "D:\videos\english.mp4" \
    --model small \
    --max_words 10 \
    --out "D:\videos\english.srt"
  ```