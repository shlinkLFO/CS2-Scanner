"""
CS2 Collection Trade-Up Analyzer
Finds cheapest covert in each collection, calculates 5x cost, 
then compares to cheapest gold outcome in same collection
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
REQUEST_DELAY = 10  # 10 seconds between requests


class CollectionAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.last_request = 0
        self.results = []
    
    def rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request
        if elapsed < REQUEST_DELAY:
            wait = REQUEST_DELAY - elapsed
            logger.info(f"Rate limiting: waiting {wait:.1f}s...")
            time.sleep(wait)
        self.last_request = time.time()
    
    def get_price(self, item_name: str) -> Optional[float]:
        """Get lowest price for an item."""
        self.rate_limit()
        
        try:
            url = "https://steamcommunity.com/market/priceoverview/"
            params = {
                'appid': 730,
                'currency': 1,
                'market_hash_name': item_name
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 429:
                logger.warning("Rate limited! Waiting 30 seconds...")
                time.sleep(30)
                return None
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and data.get('lowest_price'):
                price_str = data['lowest_price']
                price = float(price_str.replace('$', '').replace(',', ''))
                return price
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error fetching {item_name}: {e}")
            return None
    
    def find_cheapest_covert(self, collection: str, covert_skins: List[str]) -> Optional[Dict]:
        """Find the cheapest covert skin in a collection."""
        logger.info(f"Finding cheapest covert in {collection}...")
        
        cheapest_price = float('inf')
        cheapest_skin = None
        
        for skin in covert_skins:
            # Try different wear conditions
            wear_conditions = ['(Field-Tested)', '(Well-Worn)', '(Battle-Scarred)', '(Minimal Wear)']
            
            for wear in wear_conditions:
                full_name = f"{skin} {wear}"
                price = self.get_price(full_name)
                
                if price and price < cheapest_price:
                    cheapest_price = price
                    cheapest_skin = {
                        'name': full_name,
                        'price': price
                    }
        
        if cheapest_skin:
            logger.info(f"Cheapest covert: {cheapest_skin['name']} @ ${cheapest_skin['price']:.2f}")
        
        return cheapest_skin
    
    def find_cheapest_gold(self, collection: str, gold_models: List[str], finish_set: List[str]) -> Optional[Dict]:
        """Find the cheapest gold (knife/glove) in a collection."""
        logger.info(f"Finding cheapest gold in {collection}...")
        
        cheapest_price = float('inf')
        cheapest_gold = None
        
        # Focus on cheaper finishes first
        priority_finishes = ['Safari Mesh', 'Boreal Forest', 'Forest DDPAT', 'Scorched', 'Urban Masked', 'Stained']
        cheap_finishes = [f for f in priority_finishes if f in finish_set][:3]
        
        # Try vanilla first (no finish)
        for model in gold_models:
            vanilla_name = f"★ {model}"
            price = self.get_price(vanilla_name)
            if price and price < cheapest_price:
                cheapest_price = price
                cheapest_gold = {
                    'name': vanilla_name,
                    'price': price
                }
        
        # Try cheapest finishes with wear conditions
        wear_conditions = ['(Field-Tested)', '(Battle-Scarred)', '(Well-Worn)']
        
        for model in gold_models:
            for finish in cheap_finishes:
                for wear in wear_conditions:
                    gold_name = f"★ {model} | {finish} {wear}"
                    price = self.get_price(gold_name)
                    
                    if price and price < cheapest_price:
                        cheapest_price = price
                        cheapest_gold = {
                            'name': gold_name,
                            'price': price
                        }
        
        if cheapest_gold:
            logger.info(f"Cheapest gold: {cheapest_gold['name']} @ ${cheapest_gold['price']:.2f}")
        
        return cheapest_gold
    
    def analyze_collection(self, collection_name: str, covert_skins: List[str], 
                          gold_models: List[str], finish_set: List[str]) -> Optional[Dict]:
        """Analyze a single collection for trade-up profitability."""
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Analyzing: {collection_name}")
        logger.info(f"{'='*80}")
        
        # Find cheapest covert
        cheapest_covert = self.find_cheapest_covert(collection_name, covert_skins)
        if not cheapest_covert:
            logger.warning("No covert skins found")
            return None
        
        # Find cheapest gold
        cheapest_gold = self.find_cheapest_gold(collection_name, gold_models, finish_set)
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


# Collections to analyze
COLLECTIONS = {
    "Huntsman Weapon Case": {
        "covert_skins": [
            "M4A1-S | Cyrex",
            "AK-47 | Vulcan"
        ],
        "gold_models": ["Huntsman Knife"],
        "finish_set": ["Safari Mesh", "Boreal Forest", "Forest DDPAT", "Scorched", "Urban Masked", "Stained", "Blue Steel"]
    },
    
    "Falchion Case": {
        "covert_skins": [
            "AK-47 | Aquamarine Revenge",
            "AWP | Hyper Beast"
        ],
        "gold_models": ["Falchion Knife"],
        "finish_set": ["Safari Mesh", "Boreal Forest", "Forest DDPAT", "Scorched", "Urban Masked", "Stained"]
    },
    
    "Shadow Case": {
        "covert_skins": [
            "M4A1-S | Golden Coil",
            "AK-47 | Fuel Injector"
        ],
        "gold_models": ["Shadow Daggers"],
        "finish_set": ["Safari Mesh", "Boreal Forest", "Forest DDPAT", "Scorched", "Urban Masked", "Stained"]
    },
    
    "Spectrum Case": {
        "covert_skins": [
            "AK-47 | Bloodsport",
            "USP-S | Neo-Noir"
        ],
        "gold_models": ["Bowie Knife", "Butterfly Knife", "Falchion Knife", "Huntsman Knife", "Shadow Daggers"],
        "finish_set": ["Rust Coat", "Ultraviolet", "Damascus Steel"]
    },
    
    "Chroma Case": {
        "covert_skins": [
            "M4A1-S | Hyper Beast",
            "AK-47 | Cartel"
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": ["Rust Coat", "Ultraviolet", "Damascus Steel"]
    },
    
    "Chroma 2 Case": {
        "covert_skins": [
            "M4A1-S | Hyper Beast",
            "AK-47 | Aquamarine Revenge"
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": ["Rust Coat", "Ultraviolet", "Damascus Steel"]
    }
}


def main():
    """Run the collection analyzer."""
    print("\n" + "="*80)
    print("CS2 COLLECTION TRADE-UP ANALYZER")
    print("="*80)
    print("Finding cheapest covert in each collection, calculating 5x cost,")
    print("then comparing to cheapest gold outcome in same collection")
    print("="*80 + "\n")
    
    analyzer = CollectionAnalyzer()
    results = []
    
    for collection_name, collection_info in COLLECTIONS.items():
        try:
            result = analyzer.analyze_collection(
                collection_name=collection_name,
                covert_skins=collection_info["covert_skins"],
                gold_models=collection_info["gold_models"],
                finish_set=collection_info["finish_set"]
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
            print(f"\n{result['collection']} {status}")
            print(f"  Covert: {result['covert']['name']} @ ${result['covert_price']:.2f}")
            print(f"  Gold: {result['gold']['name']} @ ${result['gold_price']:.2f}")
            print(f"  Ratio: {result['price_ratio']:.2f}x")
            print(f"  Cost 5x: ${result['cost_5x_covert']:.2f} → Gold after fee: ${result['gold_after_fee']:.2f}")
            print(f"  Net Profit: ${result['net_profit']:.2f} ({result['profit_margin_pct']:.1f}%)")
        
        # Save results
        with open('collection_analysis.json', 'w') as f:
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
