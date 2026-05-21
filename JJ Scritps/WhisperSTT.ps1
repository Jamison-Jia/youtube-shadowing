# Requirements:
# pip install faster-whisper
# ffmpeg must exist in PATH

param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile
)

# ============================================
# Faster Whisper Direct M4A Transcriber
# ============================================

if (!(Test-Path $InputFile)) {

    Write-Host ""
    Write-Host "File not found." -ForegroundColor Red
    exit 1
}

# --------------------------------------------
# Resolve Path
# --------------------------------------------

$InputFile = (Resolve-Path $InputFile).Path

$InputDir = Split-Path $InputFile
$BaseName = [System.IO.Path]::GetFileNameWithoutExtension($InputFile)

# --------------------------------------------
# GPU Detection
# --------------------------------------------

$device = "cpu"
$computeType = "int8"

try {

    $cudaCheck = python -c "import torch; print(torch.cuda.is_available())"

    if ($cudaCheck -match "True") {

        $device = "cuda"
        $computeType = "float16"
    }
}
catch {
}

Write-Host ""
Write-Host "=================================="
Write-Host " Faster Whisper Transcription"
Write-Host "=================================="
Write-Host "Input   : $InputFile"
Write-Host "Model   : small"
Write-Host "Device  : $device"
Write-Host "Compute : $computeType"
Write-Host ""

# --------------------------------------------
# Create Temp Python Script
# --------------------------------------------

$tempPy = Join-Path $env:TEMP "fw_transcribe.py"

@"
import os
import sys

from faster_whisper import WhisperModel

input_file = sys.argv[1]
device = sys.argv[2]
compute_type = sys.argv[3]

base = os.path.splitext(input_file)[0]

model = WhisperModel(
    "small",
    device=device,
    compute_type=compute_type
)

segments, info = model.transcribe(
    input_file,
    beam_size=5,
    vad_filter=True
)

print(f"Detected language: {info.language}")

srt_path = base + ".srt"
txt_path = base + ".txt"

def format_time(seconds):

    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)

    return f"{hrs:02}:{mins:02}:{secs:02},{ms:03}"

with open(srt_path, "w", encoding="utf-8") as srt:
    with open(txt_path, "w", encoding="utf-8") as txt:

        for idx, seg in enumerate(segments, start=1):

            text = seg.text.strip()

            txt.write(text + "\n")

            srt.write(f"{idx}\n")
            srt.write(
                f"{format_time(seg.start)} --> "
                f"{format_time(seg.end)}\n"
            )
            srt.write(text + "\n\n")

print("DONE")
"@ | Set-Content $tempPy -Encoding UTF8

# --------------------------------------------
# Run Transcription
# --------------------------------------------

Write-Host "Starting transcription..."
Write-Host ""

python `
    "$tempPy" `
    "$InputFile" `
    "$device" `
    "$computeType"

# --------------------------------------------
# Completed
# --------------------------------------------

Write-Host ""
Write-Host "=================================="
Write-Host " Completed"
Write-Host "=================================="
Write-Host "SRT : $InputDir\$BaseName.srt"
Write-Host "TXT : $InputDir\$BaseName.txt"
Write-Host ""