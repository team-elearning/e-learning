# account/tests/test_views_profile_consent.py
import pytest
from rest_framework.authtoken.models import Token
from account.tests.factories import ProfileFactory, UserFactory
from account.models import ParentalConsent

BASE = "/api/account/"

@pytest.mark.django_db
def test_profile_get_and_patch(api_client):
    # create user and profile
    user = UserFactory(username="puser", password="abc123")
    ProfileFactory(user=user, display_name="Before")
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    # GET profile
    resp = api_client.get(f"{BASE}profile/")
    assert resp.status_code == 200
    assert resp.data["display_name"] == "Before"

    # PATCH profile
    resp2 = api_client.patch(f"{BASE}profile/", {"display_name": "After"}, format="json")
    assert resp2.status_code == 200 or resp2.status_code == 200 or resp2.status_code == 200
    # fetch again
    resp3 = api_client.get(f"{BASE}profile/")
    assert resp3.data["display_name"] == "After"


@pytest.mark.django_db
def test_parental_consent_flow(api_client):
    parent = UserFactory(role="parent", username="the_parent", password="p123")
    child = UserFactory(role="student", username="the_child", password="c123")
    token, _ = Token.objects.get_or_create(user=parent)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    # grant consent
    resp = api_client.post(f"{BASE}consents/grant/", {"child_id": child.id, "scopes": ["progress_view"]}, format="json")
    assert resp.status_code == 201
    data = resp.data
    assert data["parent_id"] == parent.id or data.get("parent") == parent.id

    # list consents
    resp2 = api_client.get(f"{BASE}consents/")
    assert resp2.status_code == 200
    # there should be at least one active consent
    found = any(c.get("child_id") == child.id or c.get("child") == child.id for c in resp2.data)
    assert found

    # revoke consent
    resp3 = api_client.post(f"{BASE}consents/revoke/", {"child_id": child.id}, format="json")
    assert resp3.status_code == 204

    # DB check
    assert not ParentalConsent.objects.filter(parent=parent, child=child, revoked_at__isnull=True).exists()
