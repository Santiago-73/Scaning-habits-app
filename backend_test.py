import requests
import sys
import json
import base64
from datetime import datetime

class NutriScanAPITester:
    def __init__(self, base_url="https://etiqueta-app.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []
        self.token = None
        self.user_data = None

    def run_test(self, name, method, endpoint, expected_status, data=None, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authorization header if token exists and auth is required
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)

            success = response.status_code == expected_status
            
            result = {
                "test_name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "response_data": None,
                "error": None
            }

            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    result["response_data"] = response.json()
                    print(f"   Response keys: {list(result['response_data'].keys()) if isinstance(result['response_data'], dict) else 'Non-dict response'}")
                except:
                    result["response_data"] = response.text[:200]
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                result["error"] = response.text[:200]

            self.results.append(result)
            return success, result["response_data"]

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            result = {
                "test_name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": None,
                "success": False,
                "response_data": None,
                "error": str(e)
            }
            self.results.append(result)
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime("%H%M%S")
        test_user = {
            "name": f"Test User {timestamp}",
            "email": f"test{timestamp}@nutriscan.com",
            "password": "TestPass123!",
            "profile": {
                "weight": 70.5,
                "height": 175,
                "sex": "male",
                "allergies": ["gluten", "lactose"],
                "conditions": ["diabetic"]
            }
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user
        )
        
        if success and response:
            # Validate response structure
            required_fields = ["token", "user"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"⚠️  Missing required fields: {missing_fields}")
                return False
            
            # Store token and user data for subsequent tests
            self.token = response["token"]
            self.user_data = response["user"]
            
            print(f"   ✅ User registered: {self.user_data.get('name')}")
            print(f"   ✅ Token received: {self.token[:20]}...")
            print(f"   ✅ Profile data: {self.user_data.get('profile', {})}")
            
        return success

    def test_user_login(self):
        """Test user login with existing credentials"""
        if not self.user_data:
            print("⚠️  Skipping login test - no user data from registration")
            return True
            
        login_data = {
            "email": self.user_data["email"],
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and response:
            # Update token with login token
            self.token = response["token"]
            print(f"   ✅ Login successful, new token: {self.token[:20]}...")
            
        return success

    def test_get_current_user(self):
        """Test getting current user info"""
        if not self.token:
            print("⚠️  Skipping get user test - no token available")
            return True
            
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200,
            auth_required=True
        )
        
        if success and response:
            required_fields = ["id", "email", "name", "profile"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"⚠️  Missing required fields: {missing_fields}")
                return False
                
            print(f"   ✅ User info retrieved: {response.get('name')}")
            print(f"   ✅ Profile allergies: {response.get('profile', {}).get('allergies', [])}")
            
        return success

    def test_update_profile(self):
        """Test updating user profile"""
        if not self.token:
            print("⚠️  Skipping profile update test - no token available")
            return True
            
        update_data = {
            "name": "Updated Test User",
            "profile": {
                "weight": 75.0,
                "height": 180,
                "sex": "male",
                "allergies": ["gluten", "nuts", "soy"],
                "conditions": ["diabetic", "hypertensive"]
            }
        }
        
        success, response = self.run_test(
            "Update User Profile",
            "PUT",
            "auth/profile",
            200,
            data=update_data,
            auth_required=True
        )
        
        if success and response:
            print(f"   ✅ Profile updated: {response.get('name')}")
            print(f"   ✅ New allergies: {response.get('profile', {}).get('allergies', [])}")
            print(f"   ✅ New conditions: {response.get('profile', {}).get('conditions', [])}")
            
        return success

    def test_analyze_with_auth(self):
        """Test analyze endpoint with authentication for personalized alerts"""
        # Create a simple test image (1x1 pixel PNG in base64)
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        success, response = self.run_test(
            "Analyze with Authentication",
            "POST",
            "analyze",
            200,
            data={"image_base64": test_image_b64},
            auth_required=True
        )
        
        if success and response:
            # Validate response structure
            required_fields = ["product_name", "brand", "health_score", "nutrients", "warnings", "recommendations", "personalized_alerts"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"⚠️  Missing required fields: {missing_fields}")
                return False
            
            print(f"   ✅ Analysis completed for authenticated user")
            print(f"   ✅ Product: {response.get('product_name')} by {response.get('brand')}")
            print(f"   ✅ Health score: {response.get('health_score')}")
            print(f"   ✅ Personalized alerts: {len(response.get('personalized_alerts', []))}")
            
            # Check if personalized alerts exist (they should for users with allergies/conditions)
            alerts = response.get('personalized_alerts', [])
            if alerts:
                for alert in alerts:
                    print(f"      - {alert.get('type', 'unknown')}: {alert.get('message', 'No message')}")
            
        return success

    def test_analyze_without_auth(self):
        """Test analyze endpoint without authentication"""
        # Create a simple test image (1x1 pixel PNG in base64)
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        success, response = self.run_test(
            "Analyze without Authentication",
            "POST",
            "analyze",
            200,
            data={"image_base64": test_image_b64}
        )
        
        if success and response:
            print(f"   ✅ Analysis completed for anonymous user")
            print(f"   ✅ Product: {response.get('product_name')} by {response.get('brand')}")
            print(f"   ✅ Personalized alerts: {len(response.get('personalized_alerts', []))}")
            
        return success

    def test_logout(self):
        """Test user logout"""
        if not self.token:
            print("⚠️  Skipping logout test - no token available")
            return True
            
        success, response = self.run_test(
            "User Logout",
            "POST",
            "auth/logout",
            200,
            auth_required=True
        )
        
        if success:
            print(f"   ✅ Logout successful")
            # Clear token after logout
            self.token = None
            
        return success

    def test_analyze_endpoint(self):
        """Test analyze endpoint with sample data"""
        success, response = self.run_test(
            "Analyze Label",
            "POST",
            "analyze",
            200,
            data={"image_base64": None}
        )
        
        if success and response:
            # Validate response structure
            required_fields = ["product_name", "brand", "health_score", "nutrients", "warnings", "recommendations"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"⚠️  Missing required fields: {missing_fields}")
                return False
            
            # Validate nutrients structure
            if response.get("nutrients") and len(response["nutrients"]) > 0:
                nutrient = response["nutrients"][0]
                nutrient_fields = ["name", "value", "unit", "status"]
                missing_nutrient_fields = [field for field in nutrient_fields if field not in nutrient]
                
                if missing_nutrient_fields:
                    print(f"⚠️  Missing nutrient fields: {missing_nutrient_fields}")
                    return False
                
                print(f"   ✅ Found {len(response['nutrients'])} nutrients")
                print(f"   ✅ Health score: {response.get('health_score')}")
                print(f"   ✅ Product: {response.get('product_name')} by {response.get('brand')}")
            
        return success

    def test_status_endpoints(self):
        """Test status check endpoints"""
        # Test creating status check
        success1, response1 = self.run_test(
            "Create Status Check",
            "POST",
            "status",
            200,
            data={"client_name": "test_client"}
        )
        
        # Test getting status checks
        success2, response2 = self.run_test(
            "Get Status Checks",
            "GET",
            "status",
            200
        )
        
        return success1 and success2

    def test_history_endpoint(self):
        """Test scan history endpoint"""
        return self.run_test(
            "Get Scan History",
            "GET",
            "history",
            200
        )

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting NutriScan API Tests")
        print(f"   Base URL: {self.base_url}")
        print("=" * 50)

        # Test all endpoints
        self.test_root_endpoint()
        self.test_analyze_endpoint()
        self.test_status_endpoints()
        self.test_history_endpoint()

        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed")
            failed_tests = [r for r in self.results if not r["success"]]
            for test in failed_tests:
                print(f"   - {test['test_name']}: {test.get('error', 'Status code mismatch')}")
            return 1

def main():
    tester = NutriScanAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())