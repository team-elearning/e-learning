from account.tests.base_test import BaseAPITestCase
from rest_framework import status
from django.urls import reverse

class TokenTests(BaseAPITestCase):
    def setUp(self):
        # Register & Login once to get valid tokens
        self.register_user(username="bob", password="Secure123", email="bob@example.com")
        login_res = self.login_user(username_or_email="bob", password="Secure123")
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.refresh = login_res.data["refresh"]
        self.access = login_res.data["access"]

    def test_refresh_token_success(self):
        url = reverse("token_refresh")
        res = self.client.post(url, {"refresh": self.refresh}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)

    def test_refresh_token_invalid(self):
        url = reverse("token_refresh")
        res = self.client.post(url, {"refresh": "not_a_real_token"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", res.data)

    def test_access_token_allows_protected_endpoint(self):
        # protected API
        protected_url = reverse("user-profile")

        # With valid token
        res = self.client.get(protected_url, HTTP_AUTHORIZATION=f"Bearer {self.access}")
        self.assertNotEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # With invalid token
        res_invalid = self.client.get(protected_url, HTTP_AUTHORIZATION="Bearer fake.token")
        self.assertEqual(res_invalid.status_code, status.HTTP_401_UNAUTHORIZED)


