import requests

def test_public_api():
    url = "https://openmlbb.fastapicloud.dev/api/heroes"
    try:
        response = requests.get(url, params={"size": 5, "lang": "en"})
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Code: {data.get('code')}")
            print(f"Message: {data.get('message')}")
            records = data.get("data", {}).get("records", [])
            print(f"Records found: {len(records)}")
            for record in records:
                hero_id = record.get("data", {}).get("hero_id")
                hero_name = record.get("data", {}).get("hero", {}).get("data", {}).get("name")
                print(f" - Hero: {hero_name} (ID: {hero_id})")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_public_api()
