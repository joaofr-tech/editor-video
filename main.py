"""Main entrypoint for video silence cut pipeline."""

import subprocess
from src.config import setup_environment
from src.silence_cutter import compute_keep_segments
from src.verifier import verify_video
from src.video_editor import cut_video
from src.whisperx_extractor import extract_word_timestamps


def run_pipeline(input_path: str = "gravacao-1.mp4", output_path: str = "editado.mp4") -> None:
    """Run the end-to-end silence removal pipeline on the given input video.

    Args:
        input_path: Path to the source video file.
        output_path: Path for the edited output video file.
    """
    setup_environment()

    dur_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_path
    ]
    raw_dur = subprocess.check_output(dur_cmd, text=True)
    if isinstance(raw_dur, bytes):
        raw_dur = raw_dur.decode("utf-8")
    total_duration = float(raw_dur.strip())

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
    silence_cut = total_duration - res["actual_duration"]
    pct = (silence_cut / total_duration * 100) if total_duration > 0 else 0.0
    print(f"Silence cut: {silence_cut:.2f}s ({pct:.1f}%)")


if __name__ == "__main__":
    run_pipeline()
