import pytest
from src.silence_cutter import compute_keep_segments


def test_compute_keep_segments_merges_words():
    words = [
        {"word": "hello", "start": 1.0, "end": 1.2},
        {"word": "world", "start": 1.3, "end": 1.6},  # Gap 0.1s < 0.25s min_silence
        {"word": "test", "start": 2.0, "end": 2.2},  # Gap 0.4s >= 0.25s
    ]
    segments = compute_keep_segments(
        words, total_duration=3.0, padding=0.08, min_silence=0.25
    )
    # 1.0-0.08 = 0.92, 1.6+0.08 = 1.68 -> segment 1
    # 2.0-0.08 = 1.92, 2.2+0.08 = 2.28 -> segment 2
    assert len(segments) == 2
    assert pytest.approx(segments[0][0]) == 0.92
    assert pytest.approx(segments[0][1]) == 1.68
    assert pytest.approx(segments[1][0]) == 1.92
    assert pytest.approx(segments[1][1]) == 2.28


def test_compute_keep_segments_missing_timestamps():
    words = [
        {"word": "hello"},  # missing start/end
        {"word": "world", "start": 1.0, "end": 1.5},
    ]
    segments = compute_keep_segments(words, total_duration=2.0, padding=0.0)
    assert len(segments) == 1
    assert segments[0] == (1.0, 1.5)


def test_compute_keep_segments_empty():
    assert compute_keep_segments([], total_duration=5.0) == []
    assert compute_keep_segments([{"word": "no_time"}], total_duration=5.0) == []


def test_compute_keep_segments_single_word():
    words = [{"word": "solo", "start": 1.0, "end": 2.0}]
    segments = compute_keep_segments(words, total_duration=3.0, padding=0.08)
    assert len(segments) == 1
    assert pytest.approx(segments[0][0]) == 0.92
    assert pytest.approx(segments[0][1]) == 2.08


def test_compute_keep_segments_boundary_clamping():
    words = [
        {"word": "start", "start": 0.05, "end": 0.5},
        {"word": "end", "start": 2.5, "end": 2.98},
    ]
    # padding 0.1 -> 0.05 - 0.1 would be -0.05, clamped to 0.0
    # 2.98 + 0.1 would be 3.08, clamped to 3.0
    segments = compute_keep_segments(
        words, total_duration=3.0, padding=0.1, min_silence=0.25
    )
    assert len(segments) == 2
    assert segments[0][0] == 0.0
    assert pytest.approx(segments[0][1]) == 0.6
    assert pytest.approx(segments[1][0]) == 2.4
    assert segments[1][1] == 3.0


def test_compute_keep_segments_overlapping_words():
    words = [
        {"word": "overlap1", "start": 1.0, "end": 1.5},
        {"word": "overlap2", "start": 1.4, "end": 1.8},
    ]
    segments = compute_keep_segments(
        words, total_duration=3.0, padding=0.05, min_silence=0.25
    )
    assert len(segments) == 1
    assert pytest.approx(segments[0][0]) == 0.95
    assert pytest.approx(segments[0][1]) == 1.85


def test_compute_keep_segments_contained_word():
    words = [
        {"word": "outer", "start": 1.0, "end": 2.5},
        {"word": "inner", "start": 1.2, "end": 1.6},
        {"word": "after", "start": 2.6, "end": 2.8},  # gap 0.1 < 0.25
    ]
    segments = compute_keep_segments(
        words, total_duration=4.0, padding=0.05, min_silence=0.25
    )
    assert len(segments) == 1
    assert pytest.approx(segments[0][0]) == 0.95
    assert pytest.approx(segments[0][1]) == 2.85


def test_compute_keep_segments_padding_overlap():
    words = [
        {"word": "first", "start": 1.0, "end": 1.5},
        {"word": "second", "start": 1.76, "end": 2.2},  # gap 0.26 >= 0.25 min_silence
    ]
    # With large padding 0.2:
    # end_1 = 1.5 + 0.2 = 1.7
    # start_2 = 1.76 - 0.2 = 1.56 -> start_2 < end_1 (overlap!)
    # Should merge to avoid inverted/overlapping trim segments
    segments = compute_keep_segments(
        words, total_duration=3.0, padding=0.2, min_silence=0.25
    )
    assert len(segments) == 1
    assert pytest.approx(segments[0][0]) == 0.8
    assert pytest.approx(segments[0][1]) == 2.4
