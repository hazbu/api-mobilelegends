import requests

def test_local_api():
    base_url = "http://127.0.0.1:8001/api"
    
    endpoints = [
        "/heroes",
        "/heroes/rank",
        "/academy/meta/version"
    ]
    
    for ep in endpoints:
        url = f"{base_url}{ep}"
        try:
            response = requests.get(url, params={"size": 1, "lang": "en"})
            print(f"Endpoint: {ep}")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response Code: {data.get('code')}")
            else:
                print(f"Error: {response.text[:100]}")
            print("-" * 20)
        except Exception as e:
            print(f"Exception for {ep}: {e}")

if __name__ == "__main__":
    test_local_api()
