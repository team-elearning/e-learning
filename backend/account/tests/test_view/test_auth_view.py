# account/tests/test_views_auth.py
import pytest
from rest_framework.authtoken.models import Token
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from infrastructure import email_service as email_infra
from account.models import UserModel

BASE = "/api/account/"

@pytest.mark.django_db
def test_register_success(api_client):
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "Password123!",
        "role": "student"
    }
    resp = api_client.post(f"{BASE}register/", payload, format="json")
    assert resp.status_code == 201
    assert resp.data["username"] == "alice"
    assert resp.data["email"] == "alice@example.com"
    # user exists in DB
    assert UserModel.objects.filter(username="alice").exists()


@pytest.mark.django_db
def test_login_success(api_client, user_factory):
    # create user with known password
    user = user_factory(username="bob", password="Secret123!")
    payload = {"username_or_email": "bob", "raw_password": "Secret123!"}
    resp = api_client.post(f"{BASE}login/", payload, format="json")
    assert resp.status_code == 200
    assert "token" in resp.data
    assert "user" in resp.data

    # check token exists in db and matches
    token_key = resp.data["token"]
    token = Token.objects.get(key=token_key)
    assert token.user_id == resp.data["user"]["id"]


@pytest.mark.django_db
def test_login_invalid_password(api_client, user_factory):
    user = user_factory(username="carol", password="RightPass1")
    payload = {"username_or_email": "carol", "raw_password": "WrongPass!"}
    resp = api_client.post(f"{BASE}login/", payload, format="json")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_logout(auth_client):
    client, user, token = auth_client
    # ensure token exists
    assert Token.objects.filter(key=token.key, user=user).exists()

    resp = client.post(f"{BASE}logout/")
    assert resp.status_code == 204
    # token removed (view deletes token)
    assert not Token.objects.filter(key=token.key).exists()


@pytest.mark.django_db
def test_reset_password_request_sends_email(api_client, user_factory, monkeypatch):
    user = user_factory(email="parent@example.com")
    sent = []

    class DummyService:
        def send(self, to, subject, body, from_email=None):
            sent.append({"to": to, "subject": subject, "body": body})

    # Patch the get_email_service factory to return our dummy
    monkeypatch.setattr(email_infra, "get_email_service", lambda: DummyService())

    resp = api_client.post(f"{BASE}password/reset/", {"email": user.email}, format="json")
    assert resp.status_code == 204
    assert len(sent) == 1
    assert sent[0]["to"] == user.email
    assert "reset-password" in sent[0]["body"] or "reset-password" in sent[0]["body"].lower()


@pytest.mark.django_db
def test_reset_password_confirm(api_client, user_factory):
    user = user_factory(email="kid@ex.com", password="OldPass123")
    token = PasswordResetTokenGenerator().make_token(user)

    payload = {
        "email": user.email,
        "reset_token": token,
        "new_password": "NewSecure123!"
    }
    resp = api_client.post(f"{BASE}password/reset/confirm/", payload, format="json")
    assert resp.status_code == 200

    # refresh and check password updated
    user.refresh_from_db()
    assert user.check_password("NewSecure123!")


@pytest.mark.django_db
def test_reset_password_confirm_invalid_token(api_client, user_factory):
    user = user_factory(email="kid2@ex.com", password="OldPass123")
    payload = {
        "email": user.email,
        "reset_token": "invalid-token",
        "new_password": "Whatever123!"
    }
    resp = api_client.post(f"{BASE}password/reset/confirm/", payload, format="json")
    assert resp.status_code == 400
