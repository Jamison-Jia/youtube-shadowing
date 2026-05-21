param(
    [Parameter(Mandatory = $true)]
    [string]$InputFile
)

# =========================================================
# Validate Input
# =========================================================

if (-not (Test-Path $InputFile)) {
    Write-Host "❌ File not found: $InputFile"
    exit 1
}

# =========================================================
# Ensure ffmpeg exists
# =========================================================

$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue

if (-not $ffmpeg) {
    Write-Host "❌ ffmpeg not found in PATH."
    Write-Host "💡 Install ffmpeg first:"
    Write-Host "   https://ffmpeg.org/download.html"
    exit 1
}

# =========================================================
# Output Path
# =========================================================

$inputPath = Resolve-Path $InputFile
$directory = Split-Path $inputPath
$filename = [System.IO.Path]::GetFileNameWithoutExtension($inputPath)

$outputFile = Join-Path $directory "$filename.mp4"

Write-Host ""
Write-Host "🎬 Input : $inputPath"
Write-Host "📦 Output: $outputFile"
Write-Host ""

# =========================================================
# Convert WEBM -> MP4
# =========================================================

ffmpeg `
    -i $inputPath `
    -c:v libx264 `
    -c:a aac `
    -movflags +faststart `
    -preset medium `
    -crf 23 `
    $outputFile

# =========================================================
# Result
# =========================================================

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Conversion completed successfully."
}
else {
    Write-Host ""
    Write-Host "❌ Conversion failed."
}