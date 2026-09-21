import subprocess
from typing import Any


def _run_probe(cmd: list[str]) -> str:
    """Run an ffprobe command and return decoded stripped stdout string."""
    raw = subprocess.check_output(cmd, text=True)
    if isinstance(raw, bytes):
        return raw.decode("utf-8").strip()
    return str(raw).strip()


def verify_video(output_path: str, expected_duration: float, tolerance: float = 0.1) -> dict[str, Any]:
    """Verify video properties, audio codec, and duration using ffprobe.

    Args:
        output_path: Path to the video file to verify.
        expected_duration: Expected duration of the video in seconds.
        tolerance: Allowed duration deviation in seconds (default 0.1s).

    Returns:
        Dictionary containing verification results:
            - video_valid: True if resolution is 576x1024 and framerate is 30 fps.
            - audio_valid: True if audio codec is aac.
            - duration_valid: True if duration is within tolerance.
            - actual_duration: Probed duration as a float.

    Raises:
        ValueError: If actual duration deviates from expected_duration by more than tolerance.
        subprocess.CalledProcessError: If ffprobe command execution fails.
    """
    vid_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        output_path
    ]
    vid_res = _run_probe(vid_cmd).split()
    video_valid = (len(vid_res) >= 3 and vid_res[0] == "576" and vid_res[1] == "1024" and vid_res[2] == "30/1")

    aud_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_name",
        "-of", "default=noprint_wrappers=1:nokey=1",
        output_path
    ]
    aud_res = _run_probe(aud_cmd)
    audio_valid = (aud_res == "aac")

    dur_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        output_path
    ]
    actual_duration = float(_run_probe(dur_cmd))

    if abs(actual_duration - expected_duration) > tolerance:
        raise ValueError(f"Duration mismatch: expected {expected_duration}, got {actual_duration}")

    return {
        "video_valid": video_valid,
        "audio_valid": audio_valid,
        "duration_valid": True,
        "actual_duration": actual_duration
    }
