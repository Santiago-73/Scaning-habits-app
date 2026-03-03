import requests
import sys
import json
from datetime import datetime

class NutriScanAPITester:
    def __init__(self, base_url="https://etiqueta-app.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)

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

    def test_root_endpoint(self):
        """Test API root endpoint"""
        return self.run_test(
            "API Root",
            "GET",
            "",
            200
        )

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