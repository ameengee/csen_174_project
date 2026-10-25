import pytest

class Resume:
    def __init__(self, user_id, parsed_text):
        if user_id is None: raise ValueError("None type not allowed")
        if type(parsed_text) is int: raise TypeError("Wrong value type")
        if len(parsed_text) > 10000: raise ValueError("Large input not allowed")
        self.user_id = user_id
        self.parsed_text = parsed_text

def test_resume_normal():
    r = Resume(1, "Python Developer")
    assert r.user_id == 1

def test_resume_edge_empty_text():
    r = Resume(1, "")
    assert r.parsed_text == ""

def test_resume_invalid_none():
    with pytest.raises(ValueError):
        Resume(None, "Python Developer")

def test_resume_invalid_wrong_type():
    with pytest.raises(TypeError):
        Resume(1, 12345)

def test_resume_invalid_large_input():
    with pytest.raises(ValueError):
        Resume(1, "A" * 15000)