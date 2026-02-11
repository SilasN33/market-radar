import sys
from pathlib import Path
# Add project root to sys.path
sys.path.append(str(Path.cwd()))

from api.server import app

def test_api():
    print("Testing /api/products endpoint...")
    with app.test_client() as client:
        try:
            resp = client.get('/api/products')
            print(f"Status Code: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.get_json()
                print(f"Success! Timestamp: {data.get('timestamp')}")
                print(f"Total Products: {data.get('total_products')}")
                print(f"Sources Breakdown: {data.get('sources')}")
                
                products = data.get('products', [])
                if products:
                    print(f"First product sample: {products[0].get('title')} ({products[0].get('marketplace')})")
                else:
                    print("No products returned (list is empty).")
            else:
                print(f"Failed response: {resp.data}")
                
        except Exception as e:
            print(f"Error during request: {e}")

if __name__ == "__main__":
    test_api()
