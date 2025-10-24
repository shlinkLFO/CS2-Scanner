"""
CS2 Browser-based Market Scraper
Uses Steam Market search API with price sorting to find cheapest items
"""

import requests
import time
import json
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Steam fee: 13%
STEAM_FEE = 0.13

# Rate limiting
REQUEST_DELAY = 15  # 15 seconds between requests (more conservative)


class SteamMarketBrowser:
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
    
    def rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request
        if elapsed < REQUEST_DELAY:
            wait = REQUEST_DELAY - elapsed
            logger.info(f"Rate limiting: waiting {wait:.1f}s...")
            time.sleep(wait)
        self.last_request = time.time()
    
    def search_market(self, query: str = "", sort_by: str = "price", sort_dir: str = "asc", 
                     count: int = 50, collection_filter: str = None, rarity_filter: str = None, 
                     quality_filter: str = None) -> Optional[List[Dict]]:
        """
        Search Steam Market with collection, rarity, and quality filters.
        
        Args:
            query: Search query
            sort_by: Sort column ("price", "name", "quantity")
            sort_dir: Sort direction ("asc", "desc")
            count: Number of results
            collection_filter: Collection ID (e.g., "tag_set_community_3" for Huntsman)
            rarity_filter: Rarity ID (e.g., "tag_Rarity_Ancient_Weapon" for Covert)
            quality_filter: Quality ID (e.g., "tag_unusual" for Knives)
        """
        self.rate_limit()
        
        try:
            url = "https://steamcommunity.com/market/search/render/"
            params = {
                'query': query,
                'start': 0,
                'count': count,
                'search_descriptions': 0,
                'sort_column': sort_by,
                'sort_dir': sort_dir,
                'appid': 730,  # CS2/CS:GO
                'norender': 1,
                'currency': 1,  # USD
                'category_730_ItemSet[]': collection_filter if collection_filter else 'any',
                'category_730_Rarity[]': rarity_filter if rarity_filter else 'any',
                'category_730_Quality[]': quality_filter if quality_filter else 'any'
            }
            
            response = self.session.get(url, params=params, timeout=20)
            
            if response.status_code == 429:
                logger.warning("Rate limited! Waiting 30 seconds...")
                time.sleep(30)
                return None
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and data.get('results'):
                return data['results']
            else:
                logger.warning(f"No results for query: {query}")
                return None
                
        except Exception as e:
            logger.error(f"Search failed for '{query}': {e}")
            return None
    
    def find_cheapest_covert_in_collection(self, collection_name: str, collection_id: str) -> Optional[Dict]:
        """Find the cheapest covert skin in a collection using market search with filters."""
        logger.info(f"Searching for cheapest covert in {collection_name}...")
        
        # Search for covert items in this specific collection, sorted by price ascending
        results = self.search_market(
            query="",  # Empty query to get all items
            sort_by="price",
            sort_dir="asc",
            count=100,
            collection_filter=collection_id,
            rarity_filter="tag_Rarity_Ancient_Weapon"  # Covert rarity
        )
        
        if not results:
            logger.warning("No covert items found in collection")
            return None
        
        # Find the cheapest covert item
        cheapest_item = None
        cheapest_price = float('inf')
        
        for item in results:
            try:
                price_str = item.get('sell_price_text', '')
                if price_str and '$' in price_str:
                    price = float(price_str.replace('$', '').replace(',', ''))
                    if price < cheapest_price:
                        cheapest_price = price
                        cheapest_item = {
                            'name': item.get('name', ''),
                            'price': price,
                            'market_url': item.get('asset_description', {}).get('market_hash_name', '')
                        }
            except (ValueError, TypeError):
                continue
        
        if cheapest_item:
            logger.info(f"Cheapest covert: {cheapest_item['name']} @ ${cheapest_item['price']:.2f}")
        
        return cheapest_item
    
    def find_cheapest_gold_in_collection(self, collection_name: str, collection_id: str) -> Optional[Dict]:
        """Find the cheapest gold (knife/glove) in a collection using market search with filters."""
        logger.info(f"Searching for cheapest gold in {collection_name}...")
        
        # Search for gold items (knives/gloves) in this specific collection, sorted by price ascending
        # Use quality filter "tag_unusual" for knives as shown in your URL
        results = self.search_market(
            query="",  # Empty query to get all items
            sort_by="price",
            sort_dir="asc",
            count=100,
            collection_filter=collection_id,
            quality_filter="tag_unusual"  # Knife quality filter
        )
        
        if not results:
            logger.warning("No gold items found in collection")
            return None
        
        # Find the cheapest gold item (knife or glove)
        cheapest_item = None
        cheapest_price = float('inf')
        
        for item in results:
            try:
                name = item.get('name', '')
                # Only consider knives (★ symbol) and gloves
                if '★' in name and ('knife' in name.lower() or 'glove' in name.lower()):
                    price_str = item.get('sell_price_text', '')
                    if price_str and '$' in price_str:
                        price = float(price_str.replace('$', '').replace(',', ''))
                        if price < cheapest_price:
                            cheapest_price = price
                            cheapest_item = {
                                'name': name,
                                'price': price,
                                'market_url': item.get('asset_description', {}).get('market_hash_name', '')
                            }
            except (ValueError, TypeError):
                continue
        
        if cheapest_item:
            logger.info(f"Cheapest gold: {cheapest_item['name']} @ ${cheapest_item['price']:.2f}")
        
        return cheapest_item
    
    def analyze_collection(self, collection_name: str, collection_id: str) -> Optional[Dict]:
        """Analyze a collection for trade-up profitability."""
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Analyzing: {collection_name}")
        logger.info(f"{'='*80}")
        
        # Find cheapest covert using market search with collection filter
        cheapest_covert = self.find_cheapest_covert_in_collection(collection_name, collection_id)
        if not cheapest_covert:
            logger.warning("No covert skins found")
            return None
        
        # Find cheapest gold using market search with collection filter
        cheapest_gold = self.find_cheapest_gold_in_collection(collection_name, collection_id)
        if not cheapest_gold:
            logger.warning("No gold items found")
            return None
        
        # Calculate profitability
        covert_price = cheapest_covert['price']
        gold_price = cheapest_gold['price']
        
        cost_5x_covert = covert_price * 5
        gold_after_fee = gold_price * (1 - STEAM_FEE)
        net_profit = gold_after_fee - cost_5x_covert
        profit_margin = (net_profit / cost_5x_covert * 100) if cost_5x_covert > 0 else 0
        price_ratio = gold_price / covert_price if covert_price > 0 else 0
        
        logger.info(f"\nResults:")
        logger.info(f"  Covert: {cheapest_covert['name']} @ ${covert_price:.2f}")
        logger.info(f"  Gold: {cheapest_gold['name']} @ ${gold_price:.2f}")
        logger.info(f"  Price Ratio: {price_ratio:.2f}x")
        logger.info(f"  Cost 5x Covert: ${cost_5x_covert:.2f}")
        logger.info(f"  Gold After Fee: ${gold_after_fee:.2f}")
        logger.info(f"  Net Profit: ${net_profit:.2f} ({profit_margin:.1f}%)")
        
        return {
            'collection': collection_name,
            'covert': cheapest_covert,
            'gold': cheapest_gold,
            'covert_price': covert_price,
            'gold_price': gold_price,
            'price_ratio': price_ratio,
            'cost_5x_covert': cost_5x_covert,
            'gold_after_fee': gold_after_fee,
            'net_profit': net_profit,
            'profit_margin_pct': profit_margin,
            'is_profitable': net_profit > 0
        }


# Collections to analyze with their Steam Market collection IDs
# Based on the table provided - these are the collections with exceedingly rare items
COLLECTIONS = {
    # Original CS:GO cases with Bayonet, Flip, Gut, Karambit, M9 Bayonet
    "CS:GO Weapon Case": {
        "collection_id": "tag_set_community_1",  # Original CS:GO case
        "gold_type": "Knives",
        "models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": "Original"
    },
    
    "eSports 2013": {
        "collection_id": "tag_set_community_2",
        "gold_type": "Knives", 
        "models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": "Original"
    },
    
    "Huntsman Weapon Case": {
        "collection_id": "tag_set_community_3",  # From the URL you provided
        "gold_type": "Knife",
        "models": ["Huntsman Knife"],
        "finish_set": "Original"
    },
    
    "Falchion Case": {
        "collection_id": "tag_set_community_8",  # Corrected based on test results
        "gold_type": "Knife",
        "models": ["Falchion Knife"],
        "finish_set": "Original"
    },
    
    "Shadow Case": {
        "collection_id": "tag_set_community_5",  # Need to find correct ID
        "gold_type": "Knife",
        "models": ["Shadow Daggers"],
        "finish_set": "Original"
    },
    
    "Chroma Case": {
        "collection_id": "tag_set_community_6",  # Need to find correct ID
        "gold_type": "Knives",
        "models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": "Chroma"
    },
    
    "Chroma 2 Case": {
        "collection_id": "tag_set_community_7",  # Need to find correct ID
        "gold_type": "Knives",
        "models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": "Chroma"
    },
    
    "Chroma 3 Case": {
        "collection_id": "tag_set_community_8",  # This one has Falchion knives, not Chroma 3
        "gold_type": "Knives",
        "models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": "Chroma"
    },
    
    "Gamma Case": {
        "collection_id": "tag_set_community_9",
        "gold_type": "Knives",
        "models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": "Gamma"
    },
    
    "Gamma 2 Case": {
        "collection_id": "tag_set_community_10",
        "gold_type": "Knives",
        "models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": "Gamma"
    },
    
    "Operation Breakout": {
        "collection_id": "tag_set_community_4",  # Found this contains Butterfly Knives
        "gold_type": "Knife",
        "models": ["Butterfly Knife"],
        "finish_set": "Original"
    },
    
    "Operation Wildfire": {
        "collection_id": "tag_set_community_12",
        "gold_type": "Knife",
        "models": ["Bowie Knife"],
        "finish_set": "Original"
    },
    
    "Spectrum Case": {
        "collection_id": "tag_set_community_13",
        "gold_type": "Knives",
        "models": ["Bowie Knife", "Butterfly Knife", "Falchion Knife", "Huntsman Knife", "Shadow Daggers"],
        "finish_set": "Chroma"
    },
    
    "Spectrum 2 Case": {
        "collection_id": "tag_set_community_14",
        "gold_type": "Knives",
        "models": ["Bowie Knife", "Butterfly Knife", "Falchion Knife", "Huntsman Knife", "Shadow Daggers"],
        "finish_set": "Chroma"
    },
    
    "Operation Riptide": {
        "collection_id": "tag_set_community_15",
        "gold_type": "Knives",
        "models": ["Bowie Knife", "Butterfly Knife", "Falchion Knife", "Huntsman Knife", "Shadow Daggers"],
        "finish_set": "Gamma"
    },
    
    "Dreams & Nightmares": {
        "collection_id": "tag_set_community_16",
        "gold_type": "Knives",
        "models": ["Bowie Knife", "Butterfly Knife", "Falchion Knife", "Huntsman Knife", "Shadow Daggers"],
        "finish_set": "Gamma"
    },
    
    "Horizon Case": {
        "collection_id": "tag_set_community_17",
        "gold_type": "Knives",
        "models": ["Navaja Knife", "Stiletto Knife", "Talon Knife", "Ursus Knife"],
        "finish_set": "Original"
    },
    
    "Danger Zone Case": {
        "collection_id": "tag_set_community_18",
        "gold_type": "Knives",
        "models": ["Navaja Knife", "Stiletto Knife", "Talon Knife", "Ursus Knife"],
        "finish_set": "Original"
    },
    
    "Prisma Case": {
        "collection_id": "tag_set_community_19",
        "gold_type": "Knives",
        "models": ["Navaja Knife", "Stiletto Knife", "Talon Knife", "Ursus Knife"],
        "finish_set": "Chroma"
    },
    
    "Prisma 2 Case": {
        "collection_id": "tag_set_community_20",
        "gold_type": "Knives",
        "models": ["Navaja Knife", "Stiletto Knife", "Talon Knife", "Ursus Knife"],
        "finish_set": "Chroma"
    },
    
    "CS20 Case": {
        "collection_id": "tag_set_community_21",
        "gold_type": "Knife",
        "models": ["Classic Knife"],
        "finish_set": "Original"
    },
    
    "Shattered Web Case": {
        "collection_id": "tag_set_community_22",
        "gold_type": "Knives",
        "models": ["Nomad Knife", "Paracord Knife", "Skeleton Knife", "Survival Knife"],
        "finish_set": "Original"
    },
    
    "Fracture Case": {
        "collection_id": "tag_set_community_23",
        "gold_type": "Knives",
        "models": ["Nomad Knife", "Paracord Knife", "Skeleton Knife", "Survival Knife"],
        "finish_set": "Original"
    },
    
    "Kilowatt Case": {
        "collection_id": "tag_set_community_24",
        "gold_type": "Knife",
        "models": ["Kukri Knife"],
        "finish_set": "Original"
    },
    
    "Gallery Case": {
        "collection_id": "tag_set_community_25",
        "gold_type": "Knife",
        "models": ["Kukri Knife"],
        "finish_set": "Original"
    },
    
    "Fever Case": {
        "collection_id": "tag_set_community_26",
        "gold_type": "Knives",
        "models": ["Nomad Knife", "Paracord Knife", "Skeleton Knife", "Survival Knife"],
        "finish_set": "Chroma"
    },
    
    # Glove cases
    "Glove Case": {
        "collection_id": "tag_set_community_27",
        "gold_type": "Gloves",
        "models": ["Bloodhound Gloves", "Driver Gloves", "Hand Wraps", "Moto Gloves", "Specialist Gloves", "Sport Gloves"],
        "finish_set": "Set 1"
    },
    
    "Operation Hydra Case": {
        "collection_id": "tag_set_community_28",
        "gold_type": "Gloves",
        "models": ["Bloodhound Gloves", "Driver Gloves", "Hand Wraps", "Moto Gloves", "Specialist Gloves", "Sport Gloves"],
        "finish_set": "Set 1"
    },
    
    "Clutch Case": {
        "collection_id": "tag_set_community_29",
        "gold_type": "Gloves",
        "models": ["Driver Gloves", "Hand Wraps", "Hydra Gloves", "Moto Gloves", "Specialist Gloves", "Sport Gloves"],
        "finish_set": "Set 2"
    },
    
    "Revolution Case": {
        "collection_id": "tag_set_community_30",
        "gold_type": "Gloves",
        "models": ["Driver Gloves", "Hand Wraps", "Hydra Gloves", "Moto Gloves", "Specialist Gloves", "Sport Gloves"],
        "finish_set": "Set 2"
    },
    
    "Operation Broken Fang Case": {
        "collection_id": "tag_set_community_31",
        "gold_type": "Gloves",
        "models": ["Broken Fang Gloves", "Driver Gloves", "Hand Wraps", "Moto Gloves", "Specialist Gloves", "Sport Gloves"],
        "finish_set": "Set 3"
    },
    
    "Snakebite Case": {
        "collection_id": "tag_set_community_32",
        "gold_type": "Gloves",
        "models": ["Broken Fang Gloves", "Driver Gloves", "Hand Wraps", "Moto Gloves", "Specialist Gloves", "Sport Gloves"],
        "finish_set": "Set 3"
    },
    
    "Recoil Case": {
        "collection_id": "tag_set_community_33",
        "gold_type": "Gloves",
        "models": ["Broken Fang Gloves", "Driver Gloves", "Hand Wraps", "Moto Gloves", "Specialist Gloves", "Sport Gloves"],
        "finish_set": "Set 3"
    }
}


def main():
    """Run the browser-based market analyzer."""
    print("\n" + "="*80)
    print("CS2 BROWSER-BASED MARKET ANALYZER")
    print("="*80)
    print("Analyzing all collections with exceedingly rare items")
    print("Using Steam Market search API with collection and rarity filters")
    print("="*80 + "\n")
    
    browser = SteamMarketBrowser()
    results = []
    
    # Filter out Operation Breakout as it's known to be unprofitable
    collections_to_analyze = {k: v for k, v in COLLECTIONS.items() if k != "Operation Breakout"}
    
    print(f"Analyzing {len(collections_to_analyze)} collections...")
    print("(Operation Breakout excluded - known unprofitable)")
    print()
    
    for collection_name, collection_info in collections_to_analyze.items():
        try:
            result = browser.analyze_collection(
                collection_name=collection_name,
                collection_id=collection_info["collection_id"]
            )
            
            if result:
                results.append(result)
                
        except KeyboardInterrupt:
            logger.info("\n\nAnalysis interrupted by user.")
            break
        except Exception as e:
            logger.error(f"Error analyzing {collection_name}: {e}")
            continue
    
    # Print summary
    if results:
        print("\n" + "="*80)
        print("SUMMARY RESULTS")
        print("="*80)
        
        # Sort by profit
        results.sort(key=lambda x: x['net_profit'], reverse=True)
        
        for result in results:
            status = "✓ PROFITABLE" if result['is_profitable'] else "✗ UNPROFITABLE"
            collection_info = collections_to_analyze.get(result['collection'], {})
            gold_type = collection_info.get('gold_type', 'Unknown')
            finish_set = collection_info.get('finish_set', 'Unknown')
            
            print(f"\n{result['collection']} {status}")
            print(f"  Type: {gold_type} | Finish Set: {finish_set}")
            print(f"  Covert: {result['covert']['name']} @ ${result['covert_price']:.2f}")
            print(f"  Gold: {result['gold']['name']} @ ${result['gold_price']:.2f}")
            print(f"  Ratio: {result['price_ratio']:.2f}x")
            print(f"  Cost 5x: ${result['cost_5x_covert']:.2f} → Gold after fee: ${result['gold_after_fee']:.2f}")
            print(f"  Net Profit: ${result['net_profit']:.2f} ({result['profit_margin_pct']:.1f}%)")
        
        # Save results
        with open('browser_analysis.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        profitable = [r for r in results if r['is_profitable']]
        print(f"\n" + "="*80)
        print(f"SUMMARY: {len(profitable)}/{len(results)} collections are profitable")
        if profitable:
            best = profitable[0]
            print(f"BEST OPPORTUNITY: {best['collection']}")
            print(f"  Profit: ${best['net_profit']:.2f} ({best['profit_margin_pct']:.1f}%)")
        print("="*80)
    else:
        print("No results collected")


if __name__ == "__main__":
    main()
