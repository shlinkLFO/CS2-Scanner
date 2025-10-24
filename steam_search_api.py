"""
Steam Market Search API
Uses Steam's search endpoint to find items by filters and sort by price
"""

import requests
import time
import json
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SteamMarketSearch:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://steamcommunity.com/market/'
        })
        self.last_request = 0
        self.delay = 8  # 8 second delay between requests (more conservative)
    
    def search_items(self, appid: int = 730, query: str = "", sort_column: str = "price", 
                    sort_dir: str = "asc", start: int = 0, count: int = 10, 
                    filters: Dict = None) -> Optional[Dict]:
        """
        Search Steam Market with filters and sorting.
        
        Args:
            appid: Game ID (730 = CS2/CS:GO)
            query: Search query string
            sort_column: Column to sort by ("price", "name", "quantity")
            sort_dir: Sort direction ("asc", "desc")
            start: Starting index for pagination
            count: Number of results to return
            filters: Dict of filters to apply
        """
        
        # Conservative rate limiting
        elapsed = time.time() - self.last_request
        if elapsed < self.delay:
            wait_time = self.delay - elapsed
            logger.info(f"Rate limiting: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        
        url = "https://steamcommunity.com/market/search/render/"
        params = {
            'query': query,
            'start': start,
            'count': count,
            'search_descriptions': 0,
            'sort_column': sort_column,
            'sort_dir': sort_dir,
            'appid': appid,
            'norender': 1,
            'currency': 1  # USD
        }
        
        # Add filters if provided
        if filters:
            for key, value in filters.items():
                params[key] = value
        
        try:
            self.last_request = time.time()
            response = self.session.get(url, params=params, timeout=20)
            
            if response.status_code == 429:
                logger.warning("Rate limited! Waiting 30 seconds...")
                time.sleep(30)
                return None
            
            response.raise_for_status()
            data = response.json()
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if "429" in str(e):
                logger.warning("Rate limited! Waiting 30 seconds...")
                time.sleep(30)
            return None
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return None
    
    def find_cheapest_knife_in_collection(self, collection_name: str) -> Optional[Dict]:
        """
        Find the cheapest knife in a specific collection.
        """
        logger.info(f"Searching for cheapest knife in {collection_name} collection...")
        
        # Search for knives in the collection
        # Try different search terms for the collection
        search_terms = [
            f"{collection_name} knife",
            f"{collection_name} ★",
            collection_name,
            "★ knife"
        ]
        
        cheapest_item = None
        cheapest_price = float('inf')
        
        for term in search_terms:
            logger.info(f"Searching: '{term}'")
            
            # Search with price ascending (reduce count to avoid rate limits)
            results = self.search_items(
                query=term,
                sort_column="price",
                sort_dir="asc",
                count=50  # Reduced from 100 to avoid rate limits
            )
            
            if not results or not results.get('results'):
                continue
            
            # Filter for actual knives (items with ★ symbol)
            knife_items = []
            for item in results['results']:
                name = item.get('name', '')
                if '★' in name and 'knife' in name.lower():
                    knife_items.append(item)
            
            logger.info(f"Found {len(knife_items)} knives with term '{term}'")
            
            # Find cheapest among these
            for item in knife_items:
                try:
                    price_str = item.get('sell_price_text', '')
                    if price_str and '$' in price_str:
                        price = float(price_str.replace('$', '').replace(',', ''))
                        if price < cheapest_price:
                            cheapest_price = price
                            cheapest_item = item
                except (ValueError, TypeError):
                    continue
        
        if cheapest_item:
            logger.info(f"Cheapest knife found: {cheapest_item['name']} @ ${cheapest_price:.2f}")
            return cheapest_item
        
        return None
    
    def find_cheapest_covert_in_collection(self, collection_name: str) -> Optional[Dict]:
        """
        Find the cheapest covert skin in a specific collection.
        """
        logger.info(f"Searching for cheapest covert in {collection_name} collection...")
        
        # Known covert skin names for each collection
        collection_coverts = {
            'Huntsman': ['M4A1-S | Cyrex', 'AK-47 | Vulcan'],
            'Falchion': ['AK-47 | Aquamarine Revenge', 'AWP | Hyper Beast'],
            'Shadow': ['M4A1-S | Golden Coil', 'AK-47 | Fuel Injector'],
            'Spectrum': ['AK-47 | Bloodsport', 'USP-S | Neo-Noir'],
            'Chroma': ['M4A1-S | Hyper Beast', 'AK-47 | Cartel'],
            'Chroma 2': ['M4A1-S | Hyper Beast', 'AK-47 | Aquamarine Revenge']
        }
        
        # Get covert skins for this collection
        covert_skins = collection_coverts.get(collection_name, [])
        
        cheapest_item = None
        cheapest_price = float('inf')
        
        for skin in covert_skins:
            # Search for this specific skin (reduced count)
            results = self.search_items(
                query=skin,
                sort_column="price",
                sort_dir="asc",
                count=25  # Reduced to avoid rate limits
            )
            
            if not results or not results.get('results'):
                continue
            
            # Find cheapest wear condition
            for item in results['results']:
                try:
                    price_str = item.get('sell_price_text', '')
                    if price_str and '$' in price_str:
                        price = float(price_str.replace('$', '').replace(',', ''))
                        if price < cheapest_price:
                            cheapest_price = price
                            cheapest_item = item
                except (ValueError, TypeError):
                    continue
        
        if cheapest_item:
            logger.info(f"Cheapest covert found: {cheapest_item['name']} @ ${cheapest_price:.2f}")
            return cheapest_item
        
        return None
    
    def analyze_collection(self, collection_name: str) -> Optional[Dict]:
        """
        Analyze a collection for trade-up profitability.
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Analyzing: {collection_name}")
        logger.info(f"{'='*60}")
        
        # Find cheapest covert
        cheapest_covert = self.find_cheapest_covert_in_collection(collection_name)
        if not cheapest_covert:
            logger.warning("No covert skins found")
            return None
        
        # Find cheapest knife
        cheapest_knife = self.find_cheapest_knife_in_collection(collection_name)
        if not cheapest_knife:
            logger.warning("No knives found")
            return None
        
        # Calculate costs
        covert_price = float(cheapest_covert['sell_price_text'].replace('$', '').replace(',', ''))
        knife_price = float(cheapest_knife['sell_price_text'].replace('$', '').replace(',', ''))
        
        cost_5x = covert_price * 5
        knife_after_fee = knife_price * 0.87  # 13% Steam fee
        profit = knife_after_fee - cost_5x
        margin = (profit / cost_5x * 100) if cost_5x > 0 else 0
        
        logger.info(f"\nResults:")
        logger.info(f"  Covert: {cheapest_covert['name']} @ ${covert_price:.2f}")
        logger.info(f"  Knife: {cheapest_knife['name']} @ ${knife_price:.2f}")
        logger.info(f"  Cost 5x: ${cost_5x:.2f}")
        logger.info(f"  Knife after fee: ${knife_after_fee:.2f}")
        logger.info(f"  Profit: ${profit:.2f} ({margin:.1f}%)")
        
        return {
            'collection': collection_name,
            'covert': cheapest_covert,
            'knife': cheapest_knife,
            'covert_price': covert_price,
            'knife_price': knife_price,
            'cost_5x': cost_5x,
            'profit': profit,
            'margin_pct': margin,
            'is_profitable': profit > 0
        }


def test_search():
    """Test the search functionality."""
    searcher = SteamMarketSearch()
    
    # Test basic search
    print("\n" + "="*60)
    print("Testing Steam Market Search API")
    print("="*60 + "\n")
    
    # Test searching for knives
    results = searcher.search_items(
        query="★ knife",
        sort_column="price",
        sort_dir="asc",
        count=5  # Reduced count for testing
    )
    
    if results and results.get('results'):
        print("Cheapest knives found:")
        for i, item in enumerate(results['results'][:5]):
            name = item.get('name', 'Unknown')
            price = item.get('sell_price_text', 'N/A')
            print(f"{i+1}. {name} - {price}")
    else:
        print("No results found")
    
    print("\n" + "="*60)
    print("Testing Collection Analysis")
    print("="*60 + "\n")
    
    # Test collection analysis
    collections = ['Huntsman', 'Falchion', 'Shadow']
    
    for collection in collections:
        result = searcher.analyze_collection(collection)
        if result:
            status = "✓ PROFITABLE" if result['is_profitable'] else "✗ UNPROFITABLE"
            print(f"{collection}: {status} (${result['profit']:.2f})")
        print()


if __name__ == "__main__":
    test_search()
