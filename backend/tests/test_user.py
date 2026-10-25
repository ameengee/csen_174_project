import pytest

class User:
    def __init__(self, email, full_name):
        if email is None: raise ValueError("None type not allowed")
        if type(full_name) is int: raise TypeError("Wrong value type")
        if len(full_name) > 500: raise ValueError("Large input not allowed")
        self.email = email
        self.full_name = full_name

def test_user_normal():
    u = User("rkumar3@scu.edu", "Rushil Kumar")
    assert u.email == "rkumar3@scu.edu"

def test_user_edge_empty_string():
    u = User("", "Rushil Kumar")
    assert u.email == ""

def test_user_invalid_none():
    with pytest.raises(ValueError):
        User(None, "Rushil Kumar")

def test_user_invalid_wrong_type():
    with pytest.raises(TypeError):
        User("rkumar3@scu.edu", 12345)


def test_user_invalid_large_input():
    with pytest.raises(ValueError):
        User("rkumar3@scu.edu", "A" * 1000)