from rest_framework import status
from django.urls import reverse
from account.tests.base_test import BaseAPITestCase

class AuthTests(BaseAPITestCase):
    # def test_register_user_success(self):
    #     res = self.register_user()
    #     self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    # def test_register_duplicate_username(self):
    #     self.register_user(username="bob")
    #     res = self.register_user(username="bob")
    #     self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn("username", res.data)

    # def test_login_sucess(self):
    #     self.register_user(username="bob", password="Secure123")
    #     res = self.login_user(username_or_email="bob", password="Secure123")
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
    #     self.assertIn("access", res.data)

    # def test_login_invalid_password(self):
    #     self.register_user(username="bob", email="bob@eample", password="Secure123")
    #     res = self.login_user(username_or_email="bob@exmaple.com", password="Secure123")
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
    #     self.assertIn("access", res.data)
    pass