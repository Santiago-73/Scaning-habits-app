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
            profile = user.get('profile', {})
            print(f"   ✅ User name: {user.get('name')}")
            print(f"   ✅ User email: {user.get('email')}")
            print(f"   ✅ Profile allergies: {profile.get('allergies', [])}")
            print(f"   ✅ Profile conditions: {profile.get('conditions', [])}")
            print(f"   ✅ Activity level: {profile.get('activity_level', 'N/A')}")
            print(f"   ✅ Goal: {profile.get('goal', 'N/A')}")
            print(f"   ✅ Strictness level: {profile.get('strictness_level', 'N/A')}")
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
        """Test profile update with new fields"""
        success, response = self.run_test(
            "Update Profile with New Fields",
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
                    "conditions": ["celiac", "hypertensive"],
                    "activity_level": "active",
                    "goal": "gain_muscle",
                    "strictness_level": "very_strict"
                }
            }
        )
        
        if success:
            profile = response.get('profile', {})
            print(f"   ✅ Updated name: {response.get('name')}")
            print(f"   ✅ Updated allergies: {profile.get('allergies', [])}")
            print(f"   ✅ Updated conditions: {profile.get('conditions', [])}")
            print(f"   ✅ Updated activity level: {profile.get('activity_level', 'N/A')}")
            print(f"   ✅ Updated goal: {profile.get('goal', 'N/A')}")
            print(f"   ✅ Updated strictness level: {profile.get('strictness_level', 'N/A')}")
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

    def test_chat_functionality(self):
        """Test chat functionality with analysis"""
        # First, we need an analysis ID from a previous analyze call
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        # Get analysis first
        success, analysis_response = self.run_test(
            "Get Analysis for Chat Test",
            "POST",
            "analyze",
            200,
            data={
                "image_base64": test_image_b64
            }
        )
        
        if not success:
            print("   ❌ Failed to get analysis for chat test")
            return False
            
        analysis_id = analysis_response.get('id')
        if not analysis_id:
            print("   ❌ No analysis ID returned")
            return False
            
        print(f"   ✅ Analysis ID for chat: {analysis_id}")
        
        # Test chat endpoint
        success, chat_response = self.run_test(
            "Chat with AI",
            "POST",
            "chat",
            200,
            data={
                "analysis_id": analysis_id,
                "message": "¿Es saludable para mí?",
                "image_base64": test_image_b64
            }
        )
        
        if success:
            response_text = chat_response.get('response', '')
            print(f"   ✅ Chat response received: {response_text[:100]}...")
            print(f"   ✅ Response length: {len(response_text)} characters")
            
            # Test getting chat history
            success_history, history_response = self.run_test(
                "Get Chat History",
                "GET",
                f"chat/{analysis_id}",
                200
            )
            
            if success_history:
                messages = history_response.get('messages', [])
                print(f"   ✅ Chat history retrieved: {len(messages)} messages")
                if messages:
                    print(f"   ✅ Last message: {messages[-1].get('content', '')[:50]}...")
            
            return success_history
        
        return success

    def test_test_user_login(self):
        """Test login with the specific test user mentioned in requirements"""
        success, response = self.run_test(
            "Test User Login (chat_test@test.com)",
            "POST",
            "auth/login",
            200,
            data={
                "email": "chat_test@test.com",
                "password": "test123"
            }
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
            user = response.get('user', {})
            profile = user.get('profile', {})
            print(f"   ✅ Test user login successful")
            print(f"   ✅ User name: {user.get('name', 'N/A')}")
            print(f"   ✅ Conditions: {profile.get('conditions', [])}")
            print(f"   ✅ Strictness level: {profile.get('strictness_level', 'N/A')}")
            return True
        else:
            print("   ℹ️ Test user doesn't exist or login failed - this is expected if user wasn't created yet")
            return False

    def test_general_chat(self):
        """Test the new general chat endpoint"""
        success, response = self.run_test(
            "General Chat Endpoint",
            "POST",
            "general-chat",
            200,
            data={
                "message": "¿Qué alimentos son buenos para perder peso?",
                "user_profile": {
                    "weight": 70.0,
                    "height": 175.0,
                    "sex": "male",
                    "allergies": ["gluten"],
                    "conditions": ["celiac"],
                    "activity_level": "moderate",
                    "goal": "lose_weight",
                    "strictness_level": "normal"
                }
            }
        )
        
        if success:
            response_text = response.get('response', '')
            print(f"   ✅ General chat response received: {response_text[:100]}...")
            print(f"   ✅ Response length: {len(response_text)} characters")
            
            # Test without user profile
            success2, response2 = self.run_test(
                "General Chat Without Profile",
                "POST",
                "general-chat",
                200,
                data={
                    "message": "¿Cuánta proteína necesito al día?"
                }
            )
            
            if success2:
                response_text2 = response2.get('response', '')
                print(f"   ✅ General chat without profile: {response_text2[:100]}...")
                return True
        
        return success

def main():
    print("=== NUTRISCAN AI BACKEND API TESTING ===")
    print(f"Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = NutriScanAPITester()
    
    # Test sequence
    tests = [
        ("API Root Endpoint", tester.test_root_endpoint),
        ("Test User Login (chat_test@test.com)", tester.test_test_user_login),
        ("User Registration", tester.test_register),
        ("Get Current User", tester.test_get_me),
        ("Analyze Label", tester.test_analyze_endpoint),
        ("Chat Functionality", tester.test_chat_functionality),
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