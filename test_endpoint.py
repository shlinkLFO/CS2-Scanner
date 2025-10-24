"""
Test script to verify the knife search endpoint functionality
"""

import requests
import time
import json
from typing import Optional, Dict, List

def test_knife_search_robust(collection_id: str, collection_name: str) -> Optional[Dict]:
    """Test knife search with robust error handling."""
    print(f"\n{'='*60}")
    print(f"Testing: {collection_name} (ID: {collection_id})")
    print(f"{'='*60}")
    
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
    
    try:
        # Add headers to avoid some issues
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://steamcommunity.com/market/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=20)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 429:
            print("Rate limited - waiting 30 seconds...")
            time.sleep(30)
            return None
            
        if response.status_code == 502:
            print("Bad Gateway - Steam API issue")
            return None
            
        # Try to parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response content (first 200 chars): {response.text[:200]}")
            return None
        
        print(f"Success: {data.get('success')}")
        print(f"Total Results: {data.get('total_count', 0)}")
        
        if data.get('success') and data.get('results'):
            results = data['results']
            print(f"Found {len(results)} knife results:")
            
            for i, item in enumerate(results[:5]):
                name = item.get('name', 'Unknown')
                price = item.get('sell_price_text', 'N/A')
                print(f"  {i+1}. {name} - {price}")
            
            # Return cheapest knife
            if results:
                cheapest = results[0]
                print(f"\nCheapest knife: {cheapest.get('name')} @ {cheapest.get('sell_price_text')}")
                return cheapest
        else:
            print("No knife results found")
            return None
            
    except requests.exceptions.Timeout:
        print("Request timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def test_covert_search(collection_id: str, collection_name: str) -> Optional[Dict]:
    """Test covert skin search."""
    print(f"\n{'='*60}")
    print(f"Testing Covert Search: {collection_name}")
    print(f"{'='*60}")
    
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
        'category_730_Rarity[]': 'tag_Rarity_Ancient_Weapon'  # Covert rarity
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://steamcommunity.com/market/'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=20)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 429:
            print("Rate limited")
            return None
            
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Total Results: {data.get('total_count', 0)}")
        
        if data.get('success') and data.get('results'):
            results = data['results']
            print(f"Found {len(results)} covert results:")
            
            for i, item in enumerate(results[:3]):
                name = item.get('name', 'Unknown')
                price = item.get('sell_price_text', 'N/A')
                print(f"  {i+1}. {name} - {price}")
            
            return results[0] if results else None
        else:
            print("No covert results found")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    """Test the endpoints."""
    print("CS2 MARKET API ENDPOINT TEST")
    print("Testing knife and covert search functionality")
    
    # Test collections with known IDs
    test_collections = [
        ("tag_set_community_3", "Huntsman Weapon Case"),
        ("tag_set_community_6", "Chroma Case"),
        ("tag_set_community_4", "Falchion Case")
    ]
    
    for collection_id, collection_name in test_collections:
        # Test knife search
        knife_result = test_knife_search_robust(collection_id, collection_name)
        
        # Wait between requests
        time.sleep(5)
        
        # Test covert search
        covert_result = test_covert_search(collection_id, collection_name)
        
        # Wait before next collection
        time.sleep(10)
        
        if knife_result and covert_result:
            print(f"\n✓ SUCCESS: {collection_name}")
            print(f"  Cheapest Knife: {knife_result.get('name')} @ {knife_result.get('sell_price_text')}")
            print(f"  Cheapest Covert: {covert_result.get('name')} @ {covert_result.get('sell_price_text')}")
        else:
            print(f"\n✗ FAILED: {collection_name}")

if __name__ == "__main__":
    main()
