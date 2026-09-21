from unittest.mock import patch
import pytest
import main


@patch("main.setup_environment")
@patch("main.extract_word_timestamps")
@patch("main.compute_keep_segments")
@patch("main.cut_video")
@patch("main.verify_video")
@patch("main.subprocess.check_output")
def test_main(mock_check_output, mock_verify, mock_cut, mock_compute, mock_extract, mock_setup):
    mock_check_output.return_value = b"18.40\n"
    mock_extract.return_value = [{"word": "test", "start": 0.0, "end": 1.0}]
    mock_compute.return_value = [(0.0, 1.0)]
    mock_verify.return_value = {"actual_duration": 1.0}

    main.run_pipeline("gravacao-1.mp4", "editado.mp4")

    mock_setup.assert_called_once()
    mock_extract.assert_called_once_with("gravacao-1.mp4")
    mock_compute.assert_called_once()
    mock_cut.assert_called_once_with("gravacao-1.mp4", "editado.mp4", [(0.0, 1.0)])
    mock_verify.assert_called_once_with("editado.mp4", 1.0)


@patch("main.setup_environment")
@patch("main.extract_word_timestamps")
@patch("main.compute_keep_segments")
@patch("main.cut_video")
@patch("main.verify_video")
@patch("main.subprocess.check_output")
def test_main_default_arguments(mock_check_output, mock_verify, mock_cut, mock_compute, mock_extract, mock_setup):
    mock_check_output.return_value = "10.0\n"
    mock_extract.return_value = [{"word": "hello", "start": 0.0, "end": 2.0}]
    mock_compute.return_value = [(0.0, 2.0)]
    mock_verify.return_value = {"actual_duration": 2.0}

    main.run_pipeline()

    mock_setup.assert_called_once()
    mock_extract.assert_called_once_with("gravacao-1.mp4")
    mock_compute.assert_called_once_with([{"word": "hello", "start": 0.0, "end": 2.0}], 10.0)
    mock_cut.assert_called_once_with("gravacao-1.mp4", "editado.mp4", [(0.0, 2.0)])
    mock_verify.assert_called_once_with("editado.mp4", 2.0)


@patch("main.setup_environment")
@patch("main.extract_word_timestamps")
@patch("main.compute_keep_segments")
@patch("main.cut_video")
@patch("main.verify_video")
@patch("main.subprocess.check_output")
def test_main_output_summary(mock_check_output, mock_verify, mock_cut, mock_compute, mock_extract, mock_setup, capsys):
    mock_check_output.return_value = "20.00\n"
    mock_extract.return_value = [{"word": "test", "start": 0.0, "end": 10.0}]
    mock_compute.return_value = [(0.0, 10.0), (12.0, 17.0)]
    mock_verify.return_value = {"actual_duration": 15.0}

    main.run_pipeline("in.mp4", "out.mp4")

    captured = capsys.readouterr().out
    assert "Original duration: 20.00s" in captured
    assert "Edited duration: 15.00s" in captured
    assert "Silence cut: 5.00s (25.0%)" in captured
    mock_verify.assert_called_once_with("out.mp4", 15.0)


@patch("main.setup_environment")
@patch("main.extract_word_timestamps")
@patch("main.compute_keep_segments")
@patch("main.cut_video")
@patch("main.verify_video")
@patch("main.subprocess.check_output")
def test_main_ffprobe_command(mock_check_output, mock_verify, mock_cut, mock_compute, mock_extract, mock_setup):
    mock_check_output.return_value = "18.40\n"
    mock_extract.return_value = []
    mock_compute.return_value = []
    mock_verify.return_value = {"actual_duration": 0.0}

    main.run_pipeline("custom_input.mp4", "custom_output.mp4")

    dur_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        "custom_input.mp4"
    ]
    mock_check_output.assert_called_once_with(dur_cmd, text=True)


@patch("main.setup_environment")
@patch("main.extract_word_timestamps")
@patch("main.compute_keep_segments")
@patch("main.cut_video")
@patch("main.verify_video")
@patch("main.subprocess.check_output")
def test_main_zero_duration(mock_check_output, mock_verify, mock_cut, mock_compute, mock_extract, mock_setup, capsys):
    mock_check_output.return_value = "0.0\n"
    mock_extract.return_value = []
    mock_compute.return_value = []
    mock_verify.return_value = {"actual_duration": 0.0}

    main.run_pipeline("in.mp4", "out.mp4")

    captured = capsys.readouterr().out
    assert "Silence cut: 0.00s (0.0%)" in captured


@patch("main.setup_environment")
@patch("main.extract_word_timestamps")
@patch("main.subprocess.check_output")
def test_main_extraction_error_propagates(mock_check_output, mock_extract, mock_setup):
    mock_check_output.return_value = "10.0\n"
    mock_extract.side_effect = ValueError("No words recognized in audio")

    with pytest.raises(ValueError, match="No words recognized in audio"):
        main.run_pipeline("in.mp4", "out.mp4")
