import json
import os
import whisperx

def extract_word_timestamps(
    video_path: str,
    output_json: str = "timestamps.json",
    model_size: str = "small",
    language: str = "pt",
    device: str = "cpu",
    compute_type: str = "int8",
) -> list[dict]:
    """Extract word-level timestamps using WhisperX and save alignment metadata.
    
    Args:
        video_path: Path to the input video or audio file.
        output_json: Path to write the alignment result JSON.
        model_size: Model size for Whisper (e.g. 'small', 'base').
        language: Language code (e.g. 'pt', 'en').
        device: Device to run models on ('cpu' or 'cuda').
        compute_type: Quantization/compute type ('int8', 'float16').
        
    Returns:
        List of word segment dictionaries with 'word', 'start', 'end' keys.
        
    Raises:
        ValueError: If no words are recognized in the audio.
    """
    audio = whisperx.load_audio(video_path)
    model = whisperx.load_model(model_size, device=device, compute_type=compute_type, language=language)
    result = model.transcribe(audio, batch_size=8)
    
    align_model, align_metadata = whisperx.load_align_model(language_code=language, device=device)
    result = whisperx.align(
        result["segments"],
        align_model,
        align_metadata,
        audio,
        device,
        return_char_alignments=False,
    )
    
    word_segments = result.get("word_segments", [])
    if not word_segments:
        raise ValueError("No words recognized in audio")
        
    os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        
    return word_segments
