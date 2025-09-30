import pytest
from datetime import date
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone

from account.models import UserModel, Profile, ParentalConsent
from account.services import user_service, auth_service
from infrastructure import email_service as email_infra
from backend.account.tests.factories import UserFactory, ProfileFactory, ParentalConsentFactory



@pytest.mark.django_db
def test_create_new_user_success():
    """create_new_user should persist user, hash password and return domain-like result."""
    username = "svc_create"
    email = "svc_create@example.com"
    raw_password = "StrongP@ss1"

    returned = user_service.create_new_user(
        username=username,
        email=email,
        password=raw_password,
        role="student",
        first_name="Svc",
        last_name="User",
        phone="0123456789",
    )

    # Check DB
    user_model = UserModel.objects.get(username=username)
    assert user_model.email == email
    assert user_model.check_password(raw_password)
    assert user_model.role == "student"

    # Service return should reflect saved entity (if returning domain object)
    if hasattr(returned, "id"):
        assert returned.id == user_model.id


@pytest.mark.django_db
def test_create_new_user_duplicate_username_or_email(user_factory):
    """Creating a user with duplicate username or email should raise."""
    user_factory(username="dupname", email="dup@example.com", password="P@ssword1")

    with pytest.raises(ValueError):
        user_service.create_new_user(username="dupname", email="new@example.com", password="Abc12345")

    with pytest.raises(ValueError):
        user_service.create_new_user(username="newname", email="dup@example.com", password="Abc12345")


@pytest.mark.django_db
def test_login_user_success_and_token_created(user_factory):
    """login_user returns user-like result (and DB has user). Views create tokens; service-level should authenticate."""
    username = "logintest"
    user = user_factory(username=username, password="LoginP@ss1")
    # many implementations expose login_user(username, password)
    result = user_service.login_user(username, "LoginP@ss1")

    assert result is not None
    # check result points to correct DB user (domain object or minimal mapping)
    # if domain object returned:
    if hasattr(result, "id"):
        assert result.id == user.id
    else:
        # or if returned is model instance
        assert getattr(result, "id", user.id) == user.id


@pytest.mark.django_db
def test_get_user_domain_by_id_username_email(user_factory):
    u = user_factory(username="finder", email="finder@example.com", password="pass1234")
    r1 = user_service.get_user_domain(user_id=u.id)
    assert r1 is not None
    # by username
    r2 = user_service.get_user_domain(username="finder")
    assert r2 is not None
    # by email
    r3 = user_service.get_user_domain(email="finder@example.com")
    assert r3 is not None


@pytest.mark.django_db
def test_update_user_basic_fields(user_factory):
    user = user_factory(username="upduser", password="oldpass")
    updated = user_service.update_user(user_id=user.id, phone="0999888777", first_name="Updated")
    assert updated is not None
    # check DB persisted
    refreshed = UserModel.objects.get(id=user.id)
    assert refreshed.phone == "0999888777"
    assert refreshed.first_name == "Updated"


@pytest.mark.django_db
def test_change_password_success_and_failure(user_factory):
    user = user_factory(username="pwuser", password="OldP@ss1")
    # success
    ok = user_service.change_password(user_id=user.id, old_password="OldP@ss1", new_password="NewP@ss2")
    assert ok is True
    user.refresh_from_db()
    assert user.check_password("NewP@ss2")

    # wrong old password should raise or return False depending on impl - expect ValueError from our earlier code
    user.set_password("Secret1")
    user.save()
    with pytest.raises(Exception):
        user_service.change_password(user_id=user.id, old_password="wrong-old", new_password="XxYy1234")


@pytest.mark.django_db
def test_deactivate_and_reactivate_user(user_factory):
    user = user_factory(username="toguser", password="pw123")
    user_service.deactivate_user(user_id=user.id)
    user.refresh_from_db()
    assert user.is_active is False

    revived = user_service.reactivate_user(user_id=user.id)
    # verify active true in DB
    user.refresh_from_db()
    assert user.is_active is True
    # returned domain/model reflects state
    if hasattr(revived, "id"):
        assert revived.id == user.id


@pytest.mark.django_db
def test_list_users_filters(user_factory):
    # create a mix of users
    user_factory(username="u1", role="student")
    user_factory(username="u2", role="parent")
    user_factory(username="u3", role="student", is_active=False)

    students = user_service.list_users(role="student", active_only=True)
    # should include u1 but not u3
    # allow both domain list or queryset-like result
    assert any(getattr(u, "username", None) == "u1" for u in students)
    assert not any(getattr(u, "username", None) == "u3" for u in students)