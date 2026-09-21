import os

FFMPEG_PATH = r"C:\Users\João\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin"

def setup_environment() -> None:
    path = os.environ.get("PATH", "")
    if FFMPEG_PATH not in path:
        os.environ["PATH"] = FFMPEG_PATH + ";" + path
