"""
Script to find the correct collection IDs by testing different tag_set_community_X values
"""

import requests
import time
import json

def test_collection_id(collection_id: str) -> dict:
    """Test a collection ID to see what knives it returns."""
    print(f"Testing collection ID: {collection_id}")
    
    url = 'https://steamcommunity.com/market/search/render/'
    params = {
        'query': '',
        'start': 0,
        'count': 10,
        'search_descriptions': 0,
        'sort_column': 'price',
        'sort_dir': 'asc',
        'appid': 730,
        'norender': 1,
        'currency': 1,
        'category_730_ItemSet[]': collection_id,
        'category_730_Quality[]': 'tag_unusual'  # Knife quality filter
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://steamcommunity.com/market/'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 429:
            print(f"  Rate limited - waiting 30s...")
            time.sleep(30)
            return {"status": "rate_limited"}
            
        data = response.json()
        
        if data.get('success') and data.get('results'):
            results = data['results']
            knife_names = []
            for item in results[:5]:
                name = item.get('name', '')
                if '★' in name:
                    knife_names.append(name)
            
            print(f"  Found {len(results)} items, {len(knife_names)} knives:")
            for knife in knife_names:
                print(f"    - {knife}")
            
            return {
                "status": "success",
                "total_items": len(results),
                "knives": knife_names
            }
        else:
            print(f"  No results found")
            return {"status": "no_results"}
            
    except Exception as e:
        print(f"  Error: {e}")
        return {"status": "error", "error": str(e)}

def main():
    """Test collection IDs to find the correct ones."""
    print("Finding correct collection IDs for CS2 cases...")
    print("="*60)
    
    # Test IDs from 1 to 50 to find the correct ones
    results = {}
    
    for i in range(1, 51):  # Test IDs 1-50
        collection_id = f"tag_set_community_{i}"
        result = test_collection_id(collection_id)
        results[collection_id] = result
        
        # Wait between requests to avoid rate limiting
        time.sleep(2)
        
        # If we get rate limited, wait longer
        if result.get("status") == "rate_limited":
            time.sleep(30)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY OF COLLECTION IDS")
    print("="*60)
    
    for collection_id, result in results.items():
        if result.get("status") == "success" and result.get("knives"):
            print(f"{collection_id}: {len(result['knives'])} knives found")
            for knife in result['knives'][:2]:  # Show first 2 knives
                print(f"  - {knife}")
            print()

if __name__ == "__main__":
    main()
