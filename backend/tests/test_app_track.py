import pytest

class AppTrack:
    def __init__(self, job_id, status):
        if job_id is None: raise ValueError("None type not allowed")
        if type(status) is int: raise TypeError("Wrong value type")
        if len(status) > 50: raise ValueError("Large input not allowed")
        self.job_id = job_id
        self.status = status

def test_track_normal():
    track = AppTrack(101, "Interviewing")
    assert track.status == "Interviewing"

def test_track_edge_single_char():
    track = AppTrack(101, "A")
    assert track.status == "A"

def test_job_invalid_none():
    with pytest.raises(ValueError):
        AppTrack(None, "Applied")

def test_job_invalid_wrong_type():
    with pytest.raises(TypeError):
        AppTrack(101, 123)

def test_track_invalid_large_input():
    with pytest.raises(ValueError):
        AppTrack(101, "A" * 1000)