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
    
    with open(output_json, "r", encoding="utf-8") as f:
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

@patch("src.whisperx_extractor.whisperx")
def test_extract_word_timestamps_custom_parameters(mock_whisperx, tmp_path):
    mock_audio = MagicMock()
    mock_whisperx.load_audio.return_value = mock_audio
    
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"segments": [{"text": "bonjour"}]}
    mock_whisperx.load_model.return_value = mock_model
    
    mock_align_model = MagicMock()
    mock_align_meta = MagicMock()
    mock_whisperx.load_align_model.return_value = (mock_align_model, mock_align_meta)
    
    mock_whisperx.align.return_value = {
        "word_segments": [{"word": "bonjour", "start": 0.1, "end": 0.6}]
    }
    
    output_json = tmp_path / "custom_timestamps.json"
    words = extract_word_timestamps(
        "video.mp4",
        output_json=str(output_json),
        model_size="base",
        language="fr",
        device="cpu",
        compute_type="int8",
    )
    
    mock_whisperx.load_audio.assert_called_once_with("video.mp4")
    vad_opts = {"vad_onset": 0.100, "vad_offset": 0.363}
    mock_whisperx.load_model.assert_called_once_with("base", device="cpu", compute_type="int8", language="fr", vad_options=vad_opts)
    mock_model.transcribe.assert_called_once_with(mock_audio, batch_size=8)
    mock_whisperx.load_align_model.assert_called_once_with(language_code="fr", device="cpu")
    mock_whisperx.align.assert_called_once_with(
        mock_model.transcribe.return_value["segments"],
        mock_align_model,
        mock_align_meta,
        mock_audio,
        "cpu",
        return_char_alignments=False
    )
    assert len(words) == 1
    assert words[0]["word"] == "bonjour"

@patch("src.whisperx_extractor.whisperx")
def test_extract_word_timestamps_missing_word_segments_key(mock_whisperx, tmp_path):
    mock_whisperx.align.return_value = {}
    mock_whisperx.load_model.return_value.transcribe.return_value = {"segments": []}
    mock_whisperx.load_align_model.return_value = (MagicMock(), MagicMock())
    
    output_json = tmp_path / "timestamps.json"
    with pytest.raises(ValueError, match="No words recognized"):
        extract_word_timestamps("dummy.mp4", str(output_json))
