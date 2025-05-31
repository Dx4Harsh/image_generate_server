import requests
import json
import time
import os
from datetime import datetime

# Server configuration
SERVER_URL = "http://localhost:5000"

def print_separator(title):
    """Print a nice separator for test sections"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def test_health_check():
    """Test the health check endpoint"""
    print_separator("TESTING HEALTH CHECK")
    
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Health check PASSED")
            return True
        else:
            print("❌ Health check FAILED")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Is the server running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_get_models():
    """Test the models endpoint"""
    print_separator("TESTING GET MODELS")
    
    try:
        response = requests.get(f"{SERVER_URL}/models", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Get models PASSED")
            return True
        else:
            print("❌ Get models FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_simple_generation():
    """Test simple image generation"""
    print_separator("TESTING SIMPLE IMAGE GENERATION")
    
    test_data = {
        "prompt": "A cute cat wearing a wizard hat, digital art"
    }
    
    try:
        print(f"Sending request: {json.dumps(test_data, indent=2)}")
        print("⏳ Generating image... (this may take 30-60 seconds)")
        
        start_time = time.time()
        response = requests.post(
            f"{SERVER_URL}/generate-simple",
            json=test_data,
            timeout=120
        )
        end_time = time.time()
        
        print(f"⏱️  Generation took: {end_time - start_time:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Simple generation PASSED")
            print(f"Generated {len(result.get('images', []))} image(s)")
            
            # Print image info without the full base64 data
            for i, img in enumerate(result.get('images', [])):
                print(f"  Image {i+1}:")
                if 'url' in img:
                    print(f"    URL: {img['url']}")
                elif 'b64_json' in img:
                    print(f"    Base64 data: {len(img['b64_json'])} characters")
            
            return True
        else:
            print(f"❌ Simple generation FAILED")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - Generation took too long")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_advanced_generation():
    """Test advanced image generation with full parameters"""
    print_separator("TESTING ADVANCED IMAGE GENERATION")
    
    test_data = {
        "prompt": "A majestic dragon flying over a castle at sunset, fantasy art, highly detailed",
        "model": "black-forest-labs/FLUX.1-schnell",
        "width": 1024,
        "height": 1024,
        "steps": 20,
        "n": 1,
        "negative_prompt": "blurry, low quality, distorted",
        "seed": 42
    }
    
    try:
        print(f"Sending request: {json.dumps(test_data, indent=2)}")
        print("⏳ Generating image... (this may take 30-60 seconds)")
        
        start_time = time.time()
        response = requests.post(
            f"{SERVER_URL}/generate",
            json=test_data,
            timeout=120
        )
        end_time = time.time()
        
        print(f"⏱️  Generation took: {end_time - start_time:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Advanced generation PASSED")
            print(f"Generated {len(result.get('images', []))} image(s)")
            print(f"Model used: {result.get('model')}")
            print(f"Parameters: {json.dumps(result.get('parameters', {}), indent=2)}")
            
            return True
        else:
            print(f"❌ Advanced generation FAILED")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - Generation took too long")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid requests"""
    print_separator("TESTING ERROR HANDLING")
    
    # Test missing prompt
    print("Testing missing prompt...")
    try:
        response = requests.post(f"{SERVER_URL}/generate-simple", json={})
        if response.status_code == 400:
            print("✅ Missing prompt error handling PASSED")
        else:
            print("❌ Missing prompt error handling FAILED")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test invalid model
    print("\nTesting invalid model...")
    try:
        response = requests.post(
            f"{SERVER_URL}/generate",
            json={
                "prompt": "test",
                "model": "invalid-model-name"
            }
        )
        if response.status_code == 400:
            print("✅ Invalid model error handling PASSED")
        else:
            print("❌ Invalid model error handling FAILED")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test invalid dimensions
    print("\nTesting invalid dimensions...")
    try:
        response = requests.post(
            f"{SERVER_URL}/generate",
            json={
                "prompt": "test",
                "width": 100,  # Too small
                "height": 3000  # Too large
            }
        )
        if response.status_code == 400:
            print("✅ Invalid dimensions error handling PASSED")
        else:
            print("❌ Invalid dimensions error handling FAILED")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("🚀 TOGETHER AI SERVER TEST SUITE")
    print(f"Testing server at: {SERVER_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if API key is configured
    if not os.getenv('TOGETHER_API_KEY'):
        print("\n⚠️  WARNING: TOGETHER_API_KEY environment variable not found!")
        print("Make sure you have set your API key in the .env file or as an environment variable.")
        print("The image generation tests will likely fail without it.\n")
    
    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("Get Models", test_get_models),
        ("Error Handling", test_error_handling),
        ("Simple Generation", test_simple_generation),
        ("Advanced Generation", test_advanced_generation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Print final results
    print_separator("TEST RESULTS SUMMARY")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your server is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()