import requests

BASE_URL = "http://127.0.0.1:8000"

def register_user():
    data = {
        "username": "student_test",
        "email": "student_test@example.com",
        "password": "123456",
        "role": "student",
    }
    r = requests.post(f"{BASE_URL}/auth/register/", json=data)
    print("REGISTER STATUS:", r.status_code)
    print("REGISTER RESPONSE:", r.json())
    return r

def login_user():
    data = {
        "email": "student_test@example.com",
        "password": "123456"
    }
    r = requests.post(f"{BASE_URL}/auth/login/", json=data)
    print("LOGIN STATUS:", r.status_code)
    print("LOGIN RESPONSE:", r.json())
    return r

def get_profile(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"{BASE_URL}/auth/me/", headers=headers)
    print("PROFILE STATUS:", r.status_code)
    print("PROFILE RESPONSE:", r.json())
    return r

if __name__ == "__main__":
    # Step 1: Register (might fail if already exists)
    register_user()

    # Step 2: Login
    login_response = login_user()
    tokens = login_response.json()
    access_token = tokens.get("access")

    # Step 3: Get profile
    if access_token:
        get_profile(access_token)
