#!/usr/bin/env python3

import requests
import sys
import json
import base64
from datetime import datetime

class NutriScanAPITester:
    def __init__(self, base_url="https://etiqueta-app.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    return success, response_data
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test API root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        if success and "NutriScan AI API" in response.get("message", ""):
            print("   ✅ Root endpoint message correct")
        return success

    def test_register(self):
        """Test user registration with extended profile"""
        # First try to delete existing user (ignore if fails)
        try:
            requests.delete(f"{self.base_url}/auth/user/newuser@test.com")
        except:
            pass

        success, response = self.run_test(
            "User Registration with Extended Profile",
            "POST",
            "auth/register",
            200,
            data={
                "name": "Test User",
                "email": "newuser@test.com",
                "password": "test123",
                "profile": {
                    "weight": 70.0,
                    "height": 175.0,
                    "sex": "male",
                    "allergies": ["gluten"],
                    "conditions": ["celiac"],
                    "activity_level": "moderate",
                    "goal": "lose_weight",
                    "strictness_level": "strict"
                }
            }
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
            print(f"   ✅ Token received: {self.token[:20]}...")
            print(f"   ✅ User ID: {self.user_id}")
            return True
        return False

    def test_login(self):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": "newuser@test.com",
                "password": "test123"
            }
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
            print(f"   ✅ Login token received: {self.token[:20]}...")
            return True
        return False

    def test_get_me(self):
        """Test get current user"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        
        if success:
            user = response
            print(f"   ✅ User name: {user.get('name')}")
            print(f"   ✅ User email: {user.get('email')}")
            print(f"   ✅ Profile allergies: {user.get('profile', {}).get('allergies', [])}")
            print(f"   ✅ Profile conditions: {user.get('profile', {}).get('conditions', [])}")
        return success

    def test_analyze_endpoint(self):
        """Test the analyze endpoint with a sample image"""
        # Create a simple base64 encoded test image (1x1 pixel PNG)
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        success, response = self.run_test(
            "Analyze Label Endpoint",
            "POST",
            "analyze",
            200,
            data={
                "image_base64": test_image_b64
            }
        )
        
        if success:
            print(f"   ✅ Product name: {response.get('product_name', 'N/A')}")
            print(f"   ✅ Health score: {response.get('health_score', 'N/A')}")
            print(f"   ✅ Nutrients count: {len(response.get('nutrients', []))}")
            print(f"   ✅ Personalized alerts: {len(response.get('personalized_alerts', []))}")
            
            # Check if personalized alerts are generated for our user profile
            alerts = response.get('personalized_alerts', [])
            if alerts:
                print(f"   ✅ Personalized alerts generated based on user profile:")
                for alert in alerts:
                    print(f"      - {alert.get('type', 'unknown')}: {alert.get('message', 'N/A')}")
            else:
                print(f"   ℹ️ No personalized alerts generated (may be normal for test image)")
        
        return success

    def test_profile_update(self):
        """Test profile update"""
        success, response = self.run_test(
            "Update Profile",
            "PUT",
            "auth/profile",
            200,
            data={
                "name": "Updated Test User",
                "profile": {
                    "weight": 75.0,
                    "height": 180.0,
                    "sex": "male",
                    "allergies": ["gluten", "lactose"],
                    "conditions": ["diabetic", "hypertensive"]
                }
            }
        )
        
        if success:
            print(f"   ✅ Updated name: {response.get('name')}")
            print(f"   ✅ Updated allergies: {response.get('profile', {}).get('allergies', [])}")
            print(f"   ✅ Updated conditions: {response.get('profile', {}).get('conditions', [])}")
        return success

    def test_logout(self):
        """Test logout"""
        success, response = self.run_test(
            "User Logout",
            "POST",
            "auth/logout",
            200
        )
        
        if success:
            print(f"   ✅ Logout message: {response.get('message', 'N/A')}")
            self.token = None  # Clear token
        return success

def main():
    print("=== NUTRISCAN AI BACKEND API TESTING ===")
    print(f"Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = NutriScanAPITester()
    
    # Test sequence
    tests = [
        ("API Root Endpoint", tester.test_root_endpoint),
        ("User Registration", tester.test_register),
        ("Get Current User", tester.test_get_me),
        ("Analyze Label", tester.test_analyze_endpoint),
        ("Update Profile", tester.test_profile_update),
        ("User Logout", tester.test_logout),
        ("User Login", tester.test_login),
        ("Get User After Login", tester.test_get_me),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if not result:
                print(f"\n⚠️ Test '{test_name}' failed, but continuing...")
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {str(e)}")
    
    # Print final results
    print(f"\n{'='*50}")
    print(f"📊 FINAL RESULTS:")
    print(f"   Tests run: {tester.tests_run}")
    print(f"   Tests passed: {tester.tests_passed}")
    print(f"   Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())