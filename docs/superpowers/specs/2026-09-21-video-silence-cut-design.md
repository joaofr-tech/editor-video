# Design: WhisperX Word-Level Video Silence Removal Pipeline

**Date:** 2026-09-21  
**Status:** Approved  
**Target Video:** `gravacao-1.mp4` (Duration: ~18.40s, Resolution: 576x1024, FPS: 30, Video: H.264, Audio: AAC)  
**Output Video:** `editado.mp4`  

---

## 1. Overview & Objective

The goal is to automatically eliminate dead air, pauses, and breaths from a video recording (`gravacao-1.mp4`) using word-level alignment timestamps extracted by WhisperX. The result is a fast-paced, seamless "Jump Cut" video (`editado.mp4`) without audio/video desynchronization, abrupt acoustic clipping, or disk clutter from intermediate video segments.

---

## 2. Environment & Tooling

- **Python Environment:** `.venv` (Python 3.11.9, WhisperX 3.8.6, PyTorch 2.8.0, faster-whisper 1.2.1, CTranslate2).
- **Execution Device:** CPU (CUDA unavailable). Inferences will use `device="cpu"` and `compute_type="int8"` for optimal CTranslate2 throughput.
- **FFmpeg Binary:** Installed via WinGet at `C:\Users\João\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin`.
  - The script dynamically registers this path in `os.environ["PATH"]` to ensure WhisperX and subprocess calls find `ffmpeg.exe` and `ffprobe.exe`.

---

## 3. Architecture & Data Flow

```
[gravacao-1.mp4]
       │
       ▼
[WhisperX Transcription & Phonetic Alignment]
       │
       ▼ (word timestamps: word, start, end)
[timestamps.json] ◄─── (Cached metadata for inspection and re-runs)
       │
       ▼
[Jump Cut Segment Merger]
  - Padding: +80ms before & after each word
  - Min Silence Threshold: 250ms (silences >= 0.25s are removed)
  - Clamping: [0.0, total_duration]
       │
       ▼ (list of keep intervals: [(s0, e0), (s1, e1), ...])
[FFmpeg filter_complex Builder]
  - Video trims: [0:v]trim=start=...:end=...,setpts=PTS-STARTPTS
  - Audio trims: [0:a]atrim=start=...:end=...,asetpts=PTS-STARTPTS
  - Concat filter: concat=n=N:v=1:a=1
       │
       ▼ (single-pass re-encode: libx264 crf 18, aac 192k)
[editado.mp4]
       │
       ▼
[FFprobe Verification]
  - Validate stream presence (video, audio)
  - Verify total duration against expected duration
```

---

## 4. Detailed Component Design

### 4.1 WhisperX Word-Level Alignment (`whisperx_extractor.py`)
- Load audio via `whisperx.load_audio(video_path)`.
- Transcribe audio using faster-whisper backend (`model_size="small"`, `language="pt"`, `compute_type="int8"`, `device="cpu"`).
- Load alignment model for detected/specified language via `whisperx.load_align_model(language_code="pt", device="cpu")`.
- Execute forced alignment: `whisperx.align(segments, align_model, align_metadata, audio, device="cpu")`.
- Save full transcription and word-level timing structure to `timestamps.json`.

### 4.2 Silence Detection & Segment Consolidation (`silence_cutter.py`)
- **Parameters:**
  - `padding = 0.08` seconds (80ms).
  - `min_silence = 0.25` seconds (250ms).
- **Algorithm:**
  1. Extract list of valid words: `[{ "word": w, "start": s, "end": e }]`. Words missing timestamps are filtered.
  2. For each word $i$, apply padding:
     $$S_i = \max(0, \text{start}_i - \text{padding})$$
     $$E_i = \min(\text{total\_duration}, \text{end}_i + \text{padding})$$
  3. Merge consecutive words:
     - If $S_{i+1} - E_i < \text{min\_silence}$, extend current segment: $E_{\text{current}} = \max(E_{\text{current}}, E_{i+1})$.
     - Else, commit $[S_{\text{current}}, E_{\text{current}}]$ as a speech interval to keep. The gap $[E_{\text{current}}, S_{i+1}]$ is logged as a removed silence.
  4. Return final ordered speech segments $[(S_0, E_0), (S_1, E_1), \dots, (S_{k}, E_{k})]$.

### 4.3 FFmpeg Rendering (`video_editor.py`)
- Assemble FFmpeg filter graph:
  - For each segment index $j$:
    `[0:v]trim=start=S_j:end=E_j,setpts=PTS-STARTPTS[v{j}];`
    `[0:a]atrim=start=S_j:end=E_j,asetpts=PTS-STARTPTS[a{j}];`
  - Concat line:
    `[v0][a0][v1][a1]...[v{k}][a{k}]concat=n={k+1}:v=1:a=1[outv][outa]`
- Command parameters:
  - `-i gravacao-1.mp4`
  - `-filter_complex "<graph>"`
  - `-map "[outv]" -map "[outa]"`
  - `-c:v libx264 -crf 18 -preset fast -pix_fmt yuv420p`
  - `-c:a aac -b:a 192k`
  - `-movflags +faststart`
  - `-y editado.mp4`

### 4.4 Automated Post-Verification
- Call `ffprobe` on `editado.mp4`.
- Validate that:
  - Video stream exists and has resolution `576x1024` with framerate `30`.
  - Audio stream exists with codec `aac`.
  - Final video duration matches $\sum (E_j - S_j)$ within a tolerance of $\pm 0.1$s.
- Print human-readable summary: original duration, edited duration, silence cut (in seconds and percentage).

---

## 5. Edge Cases & Robustness
1. **Audio with no detected words:** Raise clear error indicating no speech was recognized.
2. **First word doesn't start at 0s:** Initial silence before first word is properly dropped if $\ge \text{min\_silence}$.
3. **Trailing silence:** Silence between last spoken word and end of video is properly dropped.
4. **Overlapping words / speech overlap:** Merging logic resolves overlaps naturally without creating negative duration segments.
5. **Very long command line on Windows:** If filter_complex string exceeds command-line length limits (not applicable for an 18s video, but good practice), filter can be written to a temporary script file (`-filter_complex_script`).
