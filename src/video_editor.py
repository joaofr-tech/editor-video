import subprocess


def build_filter_complex(segments: list[tuple[float, float]]) -> str:
    """Build an FFmpeg filter_complex graph string to trim and concatenate segments.

    Args:
        segments: List of (start_time, end_time) tuples in seconds.

    Returns:
        Filter complex string for FFmpeg.

    Raises:
        ValueError: If segments list is empty.
    """
    if not segments:
        raise ValueError("No segments provided to build filter complex")

    filter_parts = []
    concat_inputs = ""

    for i, (start, end) in enumerate(segments):
        filter_parts.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}];")
        filter_parts.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}];")
        concat_inputs += f"[v{i}][a{i}]"

    filter_parts.append(f"{concat_inputs}concat=n={len(segments)}:v=1:a=1[outv][outa]")
    return "".join(filter_parts)


def cut_video(input_path: str, output_path: str, segments: list[tuple[float, float]]) -> None:
    """Cut and concatenate video segments using FFmpeg.

    Args:
        input_path: Path to the input video file.
        output_path: Path to write the rendered video file.
        segments: List of (start_time, end_time) tuples in seconds.

    Raises:
        ValueError: If segments list is empty.
        subprocess.CalledProcessError: If FFmpeg execution fails.
    """
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
