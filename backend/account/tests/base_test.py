from django.urls import reverse
from rest_framework.test import APITestCase
import json

from account.models import UserModel

class AuthTestMixin:
    def register_user(self, username="bob", password="Secure123", email="bob@example.com"):
        data = {"username": username, "password": password, "email": email}
        url = reverse("register")
        return self.client.post(url, data, format="json")
    
    def login_user(self, username_or_email="bob", password="Secure123"):
        data = {"username_or_email": username_or_email, "raw_password": password}
        url = reverse("login")
        return self.client.post(url, data, format="json")
    
    def create_user(self, username, password, email, **extra):
        user = UserModel(username=username, email=email)
        user.set_password(password)
        user.save()
        return user
    
    def get_tokens(self, username_or_email, password):
        login_res = self.login_user(username_or_email, password)
        pretty = json.dumps(login_res.json(), indent = 2)
        print(f"Login response: {login_res.status_code}\n{pretty}")
        print()
        print()

        assert login_res.status_code == 200, "Login failed in get_tokens"
        return login_res.data.get("refresh"), login_res.data.get("access")
    

class BaseAPITestCase(APITestCase, AuthTestMixin):
    """Base test case with common helpers."""
    pass