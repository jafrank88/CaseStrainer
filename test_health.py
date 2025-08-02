import requests
import time
import sys

def test_health_endpoint(url, max_attempts=10, delay=5):
    """Test health check endpoint with retries"""
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Attempt {attempt}: Testing {url}")
            response = requests.get(url, verify=False, timeout=10)
            
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text[:500]}")  # Print first 500 chars
            
            if response.status_code == 200:
                print("\n✅ Health check passed!")
                return True
                
        except requests.exceptions.SSLError as e:
            print(f"  SSL Error: {e}")
            print("  Retrying with verify=False...")
            try:
                response = requests.get(url, verify=False, timeout=10)
                print(f"  Status (no verify): {response.status_code}")
                print(f"  Response: {response.text[:500]}")
                if response.status_code == 200:
                    print("\n✅ Health check passed with verify=False!")
                    return True
            except Exception as retry_e:
                print(f"  Retry failed: {retry_e}")
                
        except Exception as e:
            print(f"  Error: {e}")
        
        if attempt < max_attempts:
            print(f"  Waiting {delay} seconds before next attempt...")
            time.sleep(delay)
    
    print("\n❌ Health check failed after all attempts")
    return False

if __name__ == "__main__":
    # Default to localhost if no URL provided
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    health_url = f"{base_url}/casestrainer/api/health"
    
    print(f"Testing health endpoint: {health_url}")
    test_health_endpoint(health_url)
