import pytest

class SupportTicket:
    def __init__(self, user_id, message):
        if user_id is None: raise ValueError("None type not allowed")
        if type(message) is int: raise TypeError("Wrong value type")
        if len(message) > 5000: raise ValueError("Large input not allowed")
        self.user_id = user_id
        self.message = message

def test_ticket_normal():
    ticket = SupportTicket(1, "Password reset help")
    assert ticket.user_id == 1

def test_ticket_edge_empty_message():
    ticket = SupportTicket(1, "")
    assert ticket.message == ""

def test_ticket_invalid_none():
    with pytest.raises(ValueError):
        SupportTicket(None, "Help")

def test_ticket_invalid_wrong_type():
    with pytest.raises(TypeError):
        SupportTicket(1, 12345)

def test_ticket_invalid_large_input():
    with pytest.raises(ValueError):
        SupportTicket(1, "A" * 6000)