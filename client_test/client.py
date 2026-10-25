import httpx

BASE_URL = "http://127.0.0.1:8000"

def add_item(name: str, category: str):
    payload = {"name": name, "category": category}
    response = httpx.post(f"{BASE_URL}/items/", json=payload)

    if response.status_code == 200:
        print("Successfully added item:", response.json())
    else:
        print(f"Error ({response.status_code}):", response.json())

def list_items():
    response = httpx.get(f"{BASE_URL}/items/")
    print("Current Inventory:", response.json())

if __name__ == "__main__":
    add_item("Milk", "Dairy")
    list_items()
    
    