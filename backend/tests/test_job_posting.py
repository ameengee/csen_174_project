import pytest

class JobPosting:
    def __init__(self, company, title):
        if company is None: raise ValueError("None type not allowed")
        if type(title) is int: raise TypeError("Wrong value type")
        if len(title) > 500: raise ValueError("Large input not allowed")
        self.company = company
        self.title = title

def test_job_normal():
    job = JobPosting("Google", "Software Engineer")
    assert job.company == "Google"

def test_job_edge_empty_title():
    job = JobPosting("Google", "")
    assert job.title == ""

def test_job_invalid_none():
    with pytest.raises(ValueError):
        JobPosting(None, "Software Engineer")

def test_job_invalid_wrong_type():
    with pytest.raises(TypeError):
        JobPosting("Google", 12345)

def test_job_invalid_large_input():
    with pytest.raises(ValueError):
        JobPosting("Google", "A" * 1000)