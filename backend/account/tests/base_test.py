from django.urls import reverse
from rest_framework.test import APITestCase

class AuthTestMixin:
    def register_user(self, username="bob", password="Secure123", email="bob@example.com"):
        data = {"username": username, "password": password, "email": email}
        url = reverse("register")
        return self.client.post(url, data, format="json")
    
    def login_user(self, username_or_email="bob", password="Secure123"):
        data = {"username_or_email": username_or_email, "password": password}
        url = reverse("login")
        return self.client.post(url, data, format="json")
    

class BaseAPITestCase(APITestCase, AuthTestMixin):
    """Base test case with common helpers."""
    pass