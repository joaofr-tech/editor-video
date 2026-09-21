import os
import pytest
from src.config import setup_environment

def test_setup_environment(monkeypatch):
    # Remove from path if it's there for a clean test
    target_path = r"C:\Users\João\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin"
    if target_path in os.environ.get("PATH", ""):
        new_path = os.environ["PATH"].replace(target_path + ";", "").replace(target_path, "")
        monkeypatch.setenv("PATH", new_path)
    
    setup_environment()
    assert target_path in os.environ.get("PATH", "")
