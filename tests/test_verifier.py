import subprocess
import pytest
from unittest.mock import patch
from src.verifier import verify_video


@patch("src.verifier.subprocess.check_output")
def test_verify_video(mock_check_output):
    mock_check_output.side_effect = [
        b'576\n1024\n30/1\n',  # video probe
        b'aac\n',               # audio probe
        b'10.05\n'              # duration probe
    ]

    result = verify_video("out.mp4", 10.0)
    assert result["video_valid"] is True
    assert result["audio_valid"] is True
    assert result["duration_valid"] is True
    assert result["actual_duration"] == 10.05


@patch("src.verifier.subprocess.check_output")
def test_verify_video_invalid_duration(mock_check_output):
    mock_check_output.side_effect = [b'576\n1024\n30/1\n', b'aac\n', b'8.0\n']

    with pytest.raises(ValueError, match="Duration mismatch: expected 10.0, got 8.0"):
        verify_video("out.mp4", 10.0)


@patch("src.verifier.subprocess.check_output")
def test_verify_video_string_output(mock_check_output):
    mock_check_output.side_effect = [
        "576\n1024\n30/1\n",
        "aac\n",
        "15.02\n"
    ]

    result = verify_video("test.mp4", 15.0)
    assert result["video_valid"] is True
    assert result["audio_valid"] is True
    assert result["duration_valid"] is True
    assert result["actual_duration"] == 15.02


@patch("src.verifier.subprocess.check_output")
def test_verify_video_invalid_video_properties(mock_check_output):
    # Invalid resolution: 1080x1920
    mock_check_output.side_effect = [
        b'1080\n1920\n30/1\n',
        b'aac\n',
        b'10.0\n'
    ]

    result = verify_video("out.mp4", 10.0)
    assert result["video_valid"] is False
    assert result["audio_valid"] is True
    assert result["duration_valid"] is True


@patch("src.verifier.subprocess.check_output")
def test_verify_video_incomplete_video_probe(mock_check_output):
    # Output missing parameters
    mock_check_output.side_effect = [
        b'576\n',
        b'aac\n',
        b'10.0\n'
    ]

    result = verify_video("out.mp4", 10.0)
    assert result["video_valid"] is False


@patch("src.verifier.subprocess.check_output")
def test_verify_video_invalid_audio_codec(mock_check_output):
    mock_check_output.side_effect = [
        b'576\n1024\n30/1\n',
        b'mp3\n',
        b'10.0\n'
    ]

    result = verify_video("out.mp4", 10.0)
    assert result["video_valid"] is True
    assert result["audio_valid"] is False
    assert result["duration_valid"] is True


@patch("src.verifier.subprocess.check_output")
def test_verify_video_tolerance_boundary(mock_check_output):
    # Exactly within tolerance
    mock_check_output.side_effect = [
        b'576\n1024\n30/1\n',
        b'aac\n',
        b'10.1\n'
    ]
    result = verify_video("out.mp4", 10.0, tolerance=0.1)
    assert result["duration_valid"] is True
    assert pytest.approx(result["actual_duration"]) == 10.1

    # Custom tolerance respected
    mock_check_output.side_effect = [
        b'576\n1024\n30/1\n',
        b'aac\n',
        b'10.35\n'
    ]
    result = verify_video("out.mp4", 10.0, tolerance=0.5)
    assert result["duration_valid"] is True
    assert pytest.approx(result["actual_duration"]) == 10.35


@patch("src.verifier.subprocess.check_output")
def test_verify_video_command_arguments(mock_check_output):
    mock_check_output.side_effect = [
        b'576\n1024\n30/1\n',
        b'aac\n',
        b'10.0\n'
    ]

    verify_video("target_video.mp4", 10.0)

    assert mock_check_output.call_count == 3
    calls = mock_check_output.call_args_list

    # Video probe command check
    assert calls[0][0][0] == [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        "target_video.mp4"
    ]

    # Audio probe command check
    assert calls[1][0][0] == [
        "ffprobe", "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_name",
        "-of", "default=noprint_wrappers=1:nokey=1",
        "target_video.mp4"
    ]

    # Duration probe command check
    assert calls[2][0][0] == [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        "target_video.mp4"
    ]


@patch("src.verifier.subprocess.check_output")
def test_verify_video_subprocess_error(mock_check_output):
    mock_check_output.side_effect = subprocess.CalledProcessError(returncode=1, cmd=["ffprobe"])

    with pytest.raises(subprocess.CalledProcessError):
        verify_video("nonexistent.mp4", 10.0)
