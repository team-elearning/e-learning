from rest_framework import status
from django.urls import reverse

from account.tests.base_test import BaseAPITestCase
from account.services import user_service
from account.mappers import user_mapper

class TokenTests(BaseAPITestCase):
    def setUp(self):
        # Student user
        self.student = self.create_user(username="student", password="Secure123", email="student@gmail.com")
        self.refresh, self.student_access = self.get_tokens(username_or_email="student", password="Secure123")

        # Admin
        self.admin = self.create_user("admin", "Secure123", "admin@gmail.com", is_staff=True)
        _, self.admin_access = self.get_tokens("admin", "Secure123")

        # # Register admin user
        # self.register_user(username="admin", password="Secure123", email="admin@gmail.com")
        # admin_domain = user_service.get_user_domain(username="admin")
        # admin_domain.role = "admin"
        # admin_model = to_existing_model(admin_domain)
        # admin_model.save()

        # login_admin = self.login_user(username_or_email="admin", password="Secure123")
        # self.assertEqual(login_admin.status_code, status.HTTP_200_OK)
        # self.admin_access = login_admin.data["access"]

    def test_refresh_token_success(self):
        url = reverse("token_refresh")
        res = self.client.post(url, {"refresh": self.refresh}, format="json")
        print(f"Refresh response: {res.data}")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)

    # def test_refresh_token_invalid(self):
    #     url = reverse("token_refresh")
    #     res = self.client.post(url, {"refresh": "not_a_real_token"}, format="json")
    #     self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
    #     self.assertIn("detail", res.data)

    # def test_access_token_allows_protected_endpoint(self):
    #     # protected API
    #     protected_url = reverse("user-profile")

    #     # With valid token
    #     res = self.client.get(protected_url, HTTP_AUTHORIZATION=f"Bearer {self.student_access}")
    #     self.assertNotEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    #     # With invalid token
    #     res_invalid = self.client.get(protected_url, HTTP_AUTHORIZATION="Bearer fake.token")
    #     self.assertEqual(res_invalid.status_code, status.HTTP_401_UNAUTHORIZED)

    # def test_student_view_own_profile(self):
    #     url = reverse("user-profile")
    #     res = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {self.student_access}")
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
    #     self.assertEqual(res.data["username"], "student")

    # def test_student_cannot_view_others_profile(self):
    #     url = reverse("user-profile") + f"?user_id=2"  # Assuming admin has ID 2
    #     res = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {self.student_access}")
    #     self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # def test_admin_can_view_any_profile(self):
    #     student_domain = user_service.get_user_domain(username="student")
    #     student_domain.role = "student"
    #     student_model = to_existing_model(student_domain)
    #     student_model.save()
    #     student_id = student_model.id

    #     url = reverse("user-profile") + f"?user_id={student_id}"
    #     res = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {self.admin_access}")
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
    #     self.assertEqual(res.data["username"], "student")


