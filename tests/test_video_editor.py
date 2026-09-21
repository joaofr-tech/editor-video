import subprocess
import pytest
from unittest.mock import patch, MagicMock
from src.video_editor import build_filter_complex, cut_video


def test_build_filter_complex():
    segments = [(0.0, 1.5), (2.0, 3.5)]
    fc = build_filter_complex(segments)
    assert "[0:v]trim=start=0.0:end=1.5,setpts=PTS-STARTPTS[v0];" in fc
    assert "[0:a]atrim=start=0.0:end=1.5,asetpts=PTS-STARTPTS[a0];" in fc
    assert "[0:v]trim=start=2.0:end=3.5,setpts=PTS-STARTPTS[v1];" in fc
    assert "[0:a]atrim=start=2.0:end=3.5,asetpts=PTS-STARTPTS[a1];" in fc
    assert "[v0][a0][v1][a1]concat=n=2:v=1:a=1[outv][outa]" in fc


def test_build_filter_complex_empty():
    with pytest.raises(ValueError, match="No segments provided"):
        build_filter_complex([])


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


@patch("src.video_editor.subprocess.run")
def test_cut_video_full_command_structure(mock_run):
    segments = [(0.0, 1.5), (2.0, 3.5)]
    cut_video("input_video.mp4", "output_video.mp4", segments)

    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    kwargs = mock_run.call_args[1]

    expected_fc = build_filter_complex(segments)
    expected_cmd = [
        "ffmpeg", "-i", "input_video.mp4",
        "-filter_complex", expected_fc,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-y", "output_video.mp4"
    ]

    assert args == expected_cmd
    assert kwargs.get("check") is True


def test_cut_video_empty_segments():
    with pytest.raises(ValueError, match="No segments provided"):
        cut_video("in.mp4", "out.mp4", [])


@patch("src.video_editor.subprocess.run")
def test_cut_video_subprocess_failure(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd=["ffmpeg"])
    with pytest.raises(subprocess.CalledProcessError):
        cut_video("in.mp4", "out.mp4", [(0.0, 1.0)])
