# Video Silence Cut Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically eliminate silences and pauses from `gravacao-1.mp4` using WhisperX word-level timestamps to create a fast-paced jump-cut video.

**Architecture:** A Python pipeline consisting of transcription/alignment (`whisperx_extractor`), silence detection and segment merging (`silence_cutter`), ffmpeg re-encoding (`video_editor`), and an automated validator (`verifier`), all orchestrated by a central CLI (`main`).

**Tech Stack:** Python 3.11, WhisperX, FFmpeg, PyTest.

**Spec:** `docs/superpowers/specs/2026-09-21-video-silence-cut-design.md`

## Global Constraints

- Execution Device: CPU (CUDA unavailable, use `device="cpu"` and `compute_type="int8"`).
- FFmpeg Binary Path: `C:\Users\João\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin` (must be added to `os.environ["PATH"]`).
- Python Environment: `.\.venv\Scripts\python.exe`
- Test Framework: `pytest`

---

### Task 1: Environment & Config Setup

**Files:**
- Create: `src/config.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Consumes: None
- Produces: `setup_environment() -> None` (adds FFmpeg to PATH).

- [ ] **Step 1: Write the failing test**

```python
import os
import pytest
from src.config import setup_environment

def test_setup_environment():
    # Remove from path if it's there for a clean test
    target_path = r"C:\Users\João\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin"
    if target_path in os.environ.get("PATH", ""):
        os.environ["PATH"] = os.environ["PATH"].replace(target_path + ";", "")
        os.environ["PATH"] = os.environ["PATH"].replace(target_path, "")
    
    setup_environment()
    assert target_path in os.environ.get("PATH", "")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_config.py -v`
Expected: FAIL with ModuleNotFoundError for `src.config`

- [ ] **Step 3: Write minimal implementation**

```python
import os

FFMPEG_PATH = r"C:\Users\João\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin"

def setup_environment() -> None:
    path = os.environ.get("PATH", "")
    if FFMPEG_PATH not in path:
        os.environ["PATH"] = FFMPEG_PATH + ";" + path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_config.py src/config.py
git commit -m "feat: add environment config for FFmpeg path"
```

### Task 2: Silence Cutter Logic

**Files:**
- Create: `src/silence_cutter.py`
- Create: `tests/test_silence_cutter.py`

**Interfaces:**
- Consumes: Word list `[{ "word": str, "start": float, "end": float }]`
- Produces: `compute_keep_segments(words: list[dict], total_duration: float, padding: float = 0.08, min_silence: float = 0.25) -> list[tuple[float, float]]`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from src.silence_cutter import compute_keep_segments

def test_compute_keep_segments_merges_words():
    words = [
        {"word": "hello", "start": 1.0, "end": 1.2},
        {"word": "world", "start": 1.3, "end": 1.6},  # Gap 0.1s < 0.25s min_silence
        {"word": "test", "start": 2.0, "end": 2.2}    # Gap 0.4s >= 0.25s
    ]
    segments = compute_keep_segments(words, total_duration=3.0, padding=0.08, min_silence=0.25)
    # 1.0-0.08 = 0.92, 1.6+0.08 = 1.68 -> segment 1
    # 2.0-0.08 = 1.92, 2.2+0.08 = 2.28 -> segment 2
    assert len(segments) == 2
    assert pytest.approx(segments[0][0]) == 0.92
    assert pytest.approx(segments[0][1]) == 1.68
    assert pytest.approx(segments[1][0]) == 1.92
    assert pytest.approx(segments[1][1]) == 2.28

def test_compute_keep_segments_missing_timestamps():
    words = [
        {"word": "hello"}, # missing start/end
        {"word": "world", "start": 1.0, "end": 1.5}
    ]
    segments = compute_keep_segments(words, total_duration=2.0, padding=0.0)
    assert len(segments) == 1
    assert segments[0] == (1.0, 1.5)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_silence_cutter.py -v`
Expected: FAIL with ModuleNotFoundError or ImportError

- [ ] **Step 3: Write minimal implementation**

```python
def compute_keep_segments(words: list[dict], total_duration: float, padding: float = 0.08, min_silence: float = 0.25) -> list[tuple[float, float]]:
    valid_words = [w for w in words if "start" in w and "end" in w]
    if not valid_words:
        return []

    segments = []
    current_start = max(0.0, valid_words[0]["start"] - padding)
    current_end = min(total_duration, valid_words[0]["end"] + padding)

    for i in range(1, len(valid_words)):
        start_i = max(0.0, valid_words[i]["start"] - padding)
        end_i = min(total_duration, valid_words[i]["end"] + padding)

        if start_i - current_end < min_silence:
            current_end = max(current_end, end_i)
        else:
            segments.append((current_start, current_end))
            current_start = start_i
            current_end = end_i

    segments.append((current_start, current_end))
    return segments
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_silence_cutter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_silence_cutter.py src/silence_cutter.py
git commit -m "feat: implement silence cutter logic for segment merging"
```

### Task 3: WhisperX Extractor

**Files:**
- Create: `src/whisperx_extractor.py`
- Create: `tests/test_whisperx_extractor.py`

**Interfaces:**
- Consumes: Video path (`str`)
- Produces: `extract_word_timestamps(video_path: str, output_json: str = "timestamps.json", model_size: str = "small", language: str = "pt", device: str = "cpu", compute_type: str = "int8") -> list[dict]`

- [ ] **Step 1: Write the failing test**

```python
import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.whisperx_extractor import extract_word_timestamps

@patch("src.whisperx_extractor.whisperx")
def test_extract_word_timestamps(mock_whisperx, tmp_path):
    mock_audio = MagicMock()
    mock_whisperx.load_audio.return_value = mock_audio
    
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"segments": [{"text": "hello world"}]}
    mock_whisperx.load_model.return_value = mock_model
    
    mock_align_model = MagicMock()
    mock_whisperx.load_align_model.return_value = (mock_align_model, MagicMock())
    
    mock_whisperx.align.return_value = {
        "word_segments": [{"word": "hello", "start": 0.0, "end": 0.5}]
    }
    
    output_json = tmp_path / "timestamps.json"
    
    words = extract_word_timestamps("dummy.mp4", str(output_json))
    
    assert len(words) == 1
    assert words[0]["word"] == "hello"
    assert os.path.exists(output_json)
    
    with open(output_json, "r") as f:
        data = json.load(f)
        assert data["word_segments"][0]["word"] == "hello"

@patch("src.whisperx_extractor.whisperx")
def test_extract_word_timestamps_no_words(mock_whisperx, tmp_path):
    mock_whisperx.align.return_value = {"word_segments": []}
    mock_whisperx.load_model.return_value.transcribe.return_value = {"segments": []}
    mock_whisperx.load_align_model.return_value = (MagicMock(), MagicMock())
    
    output_json = tmp_path / "timestamps.json"
    with pytest.raises(ValueError, match="No words recognized"):
        extract_word_timestamps("dummy.mp4", str(output_json))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_whisperx_extractor.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
import json
import whisperx

def extract_word_timestamps(video_path: str, output_json: str = "timestamps.json", model_size: str = "small", language: str = "pt", device: str = "cpu", compute_type: str = "int8") -> list[dict]:
    audio = whisperx.load_audio(video_path)
    model = whisperx.load_model(model_size, device=device, compute_type=compute_type, language=language)
    result = model.transcribe(audio, batch_size=8)
    
    align_model, align_metadata = whisperx.load_align_model(language_code=language, device=device)
    result = whisperx.align(result["segments"], align_model, align_metadata, audio, device, return_char_alignments=False)
    
    word_segments = result.get("word_segments", [])
    if not word_segments:
        raise ValueError("No words recognized in audio")
        
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        
    return word_segments
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_whisperx_extractor.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_whisperx_extractor.py src/whisperx_extractor.py
git commit -m "feat: add WhisperX extraction and caching"
```

### Task 4: Video Editor (FFmpeg Rendering)

**Files:**
- Create: `src/video_editor.py`
- Create: `tests/test_video_editor.py`

**Interfaces:**
- Consumes: Segments `list[tuple[float, float]]`
- Produces: `build_filter_complex(segments: list[tuple[float, float]]) -> str`, `cut_video(input_path: str, output_path: str, segments: list[tuple[float, float]]) -> None`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from unittest.mock import patch, call
from src.video_editor import build_filter_complex, cut_video

def test_build_filter_complex():
    segments = [(0.0, 1.5), (2.0, 3.5)]
    fc = build_filter_complex(segments)
    assert "[0:v]trim=start=0.0:end=1.5,setpts=PTS-STARTPTS[v0];" in fc
    assert "[0:a]atrim=start=0.0:end=1.5,asetpts=PTS-STARTPTS[a0];" in fc
    assert "[v0][a0][v1][a1]concat=n=2:v=1:a=1[outv][outa]" in fc

@patch("src.video_editor.subprocess.run")
def test_cut_video(mock_run):
    segments = [(0.0, 1.5)]
    cut_video("in.mp4", "out.mp4", segments)
    
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "ffmpeg" in args
    assert "-i" in args and "in.mp4" in args
    assert "-filter_complex" in args
    assert "-y" in args and "out.mp4" in args
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_video_editor.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
import subprocess

def build_filter_complex(segments: list[tuple[float, float]]) -> str:
    filter_parts = []
    concat_inputs = ""
    
    for i, (start, end) in enumerate(segments):
        filter_parts.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}];")
        filter_parts.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}];")
        concat_inputs += f"[v{i}][a{i}]"
        
    filter_parts.append(f"{concat_inputs}concat=n={len(segments)}:v=1:a=1[outv][outa]")
    return "".join(filter_parts)

def cut_video(input_path: str, output_path: str, segments: list[tuple[float, float]]) -> None:
    filter_complex = build_filter_complex(segments)
    
    cmd = [
        "ffmpeg", "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-y", output_path
    ]
    
    subprocess.run(cmd, check=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_video_editor.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_video_editor.py src/video_editor.py
git commit -m "feat: add FFmpeg video editor logic"
```

### Task 5: Video Verification

**Files:**
- Create: `src/verifier.py`
- Create: `tests/test_verifier.py`

**Interfaces:**
- Consumes: Output path, expected duration
- Produces: `verify_video(output_path: str, expected_duration: float, tolerance: float = 0.1) -> dict`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from unittest.mock import patch, MagicMock
from src.verifier import verify_video

@patch("src.verifier.subprocess.check_output")
def test_verify_video(mock_check_output):
    mock_check_output.side_effect = [
        b'576\n1024\n30/1\n', # video probe
        b'aac\n',              # audio probe
        b'10.05\n'             # duration probe
    ]
    
    result = verify_video("out.mp4", 10.0)
    assert result["video_valid"] is True
    assert result["audio_valid"] is True
    assert result["duration_valid"] is True
    assert result["actual_duration"] == 10.05

@patch("src.verifier.subprocess.check_output")
def test_verify_video_invalid_duration(mock_check_output):
    mock_check_output.side_effect = [b'576\n1024\n30/1\n', b'aac\n', b'8.0\n']
    
    with pytest.raises(ValueError, match="Duration mismatch"):
        verify_video("out.mp4", 10.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_verifier.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
import subprocess

def verify_video(output_path: str, expected_duration: float, tolerance: float = 0.1) -> dict:
    vid_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate", "-of", "default=noprint_wrappers=1:nokey=1", output_path]
    vid_res = subprocess.check_output(vid_cmd, text=True).strip().split()
    video_valid = (len(vid_res) >= 3 and vid_res[0] == "576" and vid_res[1] == "1024" and vid_res[2] == "30/1")
    
    aud_cmd = ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1", output_path]
    aud_res = subprocess.check_output(aud_cmd, text=True).strip()
    audio_valid = (aud_res == "aac")
    
    dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", output_path]
    actual_duration = float(subprocess.check_output(dur_cmd, text=True).strip())
    
    if abs(actual_duration - expected_duration) > tolerance:
        raise ValueError(f"Duration mismatch: expected {expected_duration}, got {actual_duration}")
        
    return {
        "video_valid": video_valid,
        "audio_valid": audio_valid,
        "duration_valid": True,
        "actual_duration": actual_duration
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_verifier.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_verifier.py src/verifier.py
git commit -m "feat: add video output verification"
```

### Task 6: CLI Orchestration (Main)

**Files:**
- Create: `main.py`
- Modify: `tests/test_main.py` (Integration)

**Interfaces:**
- Consumes: All `src/` modules.
- Produces: Executable CLI script.

- [ ] **Step 1: Write the failing test**

```python
import pytest
from unittest.mock import patch, MagicMock
import main

@patch("main.setup_environment")
@patch("main.extract_word_timestamps")
@patch("main.compute_keep_segments")
@patch("main.cut_video")
@patch("main.verify_video")
@patch("main.subprocess.check_output")
def test_main(mock_check_output, mock_verify, mock_cut, mock_compute, mock_extract, mock_setup):
    mock_check_output.return_value = b'18.40\n'
    mock_extract.return_value = [{"word": "test", "start": 0.0, "end": 1.0}]
    mock_compute.return_value = [(0.0, 1.0)]
    mock_verify.return_value = {"actual_duration": 1.0}
    
    main.run_pipeline("gravacao-1.mp4", "editado.mp4")
    
    mock_setup.assert_called_once()
    mock_extract.assert_called_once_with("gravacao-1.mp4")
    mock_compute.assert_called_once()
    mock_cut.assert_called_once_with("gravacao-1.mp4", "editado.mp4", [(0.0, 1.0)])
    mock_verify.assert_called_once_with("editado.mp4", 1.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_main.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
import subprocess
from src.config import setup_environment
from src.whisperx_extractor import extract_word_timestamps
from src.silence_cutter import compute_keep_segments
from src.video_editor import cut_video
from src.verifier import verify_video

def run_pipeline(input_path: str = "gravacao-1.mp4", output_path: str = "editado.mp4"):
    setup_environment()
    
    dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", input_path]
    total_duration = float(subprocess.check_output(dur_cmd, text=True).strip())
    
    print("Extracting timestamps...")
    words = extract_word_timestamps(input_path)
    
    print("Computing keep segments...")
    segments = compute_keep_segments(words, total_duration)
    
    expected_duration = sum(end - start for start, end in segments)
    
    print("Cutting video...")
    cut_video(input_path, output_path, segments)
    
    print("Verifying output...")
    res = verify_video(output_path, expected_duration)
    
    print(f"Original duration: {total_duration:.2f}s")
    print(f"Edited duration: {res['actual_duration']:.2f}s")
    silence_cut = total_duration - res['actual_duration']
    print(f"Silence cut: {silence_cut:.2f}s ({silence_cut / total_duration * 100:.1f}%)")

if __name__ == "__main__":
    run_pipeline()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_main.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_main.py main.py
git commit -m "feat: assemble main orchestrator pipeline"
```
