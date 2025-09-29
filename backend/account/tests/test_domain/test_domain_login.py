# account/tests/test_domain_login.py
import pytest
from account.domains.login_domain import LoginDomain

def test_logindomain_valid_data():
    l = LoginDomain(username_or_email="alice", raw_password="abc123")
    assert l.to_dict()["username_or_email"] == "alice"

def test_logindomain_missing_username_or_email():
    with pytest.raises(ValueError, match="Username or email is required"):
        LoginDomain(username_or_email="", raw_password="abc123")

def test_logindomain_missing_password():
    with pytest.raises(ValueError, match="Password is required"):
        LoginDomain(username_or_email="alice", raw_password="")
