# account/tests/test_views_user.py
import pytest
from rest_framework.authtoken.models import Token

BASE = "/api/account/"

@pytest.mark.django_db
def test_user_detail_owner_can_get(auth_client):
    client, user, token = auth_client
    resp = client.get(f"{BASE}users/{user.id}/")
    assert resp.status_code == 200
    assert resp.data["id"] == user.id


@pytest.mark.django_db
def test_user_detail_other_forbidden(api_client, user_factory):
    a = user_factory(username="u1")
    b = user_factory(username="u2")
    # auth as b
    token, _ = Token.objects.get_or_create(user=b)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    resp = api_client.get(f"{BASE}users/{a.id}/")
    assert resp.status_code == 403  # IsOwnerOrAdmin denies


@pytest.mark.django_db
def test_user_update_owner(api_client, user_factory):
    user = user_factory(username="mike", password="P@ssword1")
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    resp = api_client.patch(f"{BASE}users/{user.id}/", {"phone": "0123456789"}, format="json")
    assert resp.status_code == 200
    assert resp.data["phone"] == "0123456789"


@pytest.mark.django_db
def test_user_list_admin(admin_auth_client, user_factory):
    client, admin, token = admin_auth_client
    # create some users
    user_factory(username="u_a")
    user_factory(username="u_b")
    resp = client.get(f"{BASE}users/")
    assert resp.status_code == 200
    # it's a list view; at least 2 users plus admin present
    assert isinstance(resp.data, list) or isinstance(resp.data, dict)  # depends on pagination
    # if list returned directly:
    if isinstance(resp.data, list):
        assert len(resp.data) >= 2


@pytest.mark.django_db
def test_change_password_wrong_old(auth_client):
    client, user, token = auth_client
    payload = {"old_password": "wrong", "new_password": "NewP@ss1"}
    resp = client.post(f"{BASE}password/change/", payload, format="json")
    assert resp.status_code == 400
