"""
CS2 Trade-Up Smart Scanner
Handles rate limits gracefully with exponential backoff and progress saving
"""

import time
import requests
import pandas as pd
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

APPID = 730
CURRENCY = 1
STEAM_FEE_PERCENT = 0.13

# Rate limiting config
BASE_DELAY = 10  # Base delay between requests in seconds
MAX_RETRIES = 3
BACKOFF_MULTIPLIER = 2

# Progress file
PROGRESS_FILE = "scan_progress.json"
CACHE_FILE = "price_cache.json"


class RateLimitedScanner:
    def __init__(self):
        self.price_cache = self.load_cache()
        self.request_count = 0
        self.last_request_time = 0
        
    def load_cache(self) -> Dict:
        """Load price cache from file."""
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_cache(self):
        """Save price cache to file."""
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.price_cache, f, indent=2)
        logger.info(f"Saved {len(self.price_cache)} prices to cache")
    
    def get_price_with_retry(self, item_name: str) -> Optional[float]:
        """Fetch price with exponential backoff on rate limits."""
        
        # Check cache first
        if item_name in self.price_cache:
            logger.info(f"[CACHED] {item_name}: ${self.price_cache[item_name]:.2f}")
            return self.price_cache[item_name]
        
        delay = BASE_DELAY
        
        for attempt in range(MAX_RETRIES):
            try:
                # Ensure minimum delay between requests
                elapsed = time.time() - self.last_request_time
                if elapsed < delay:
                    wait_time = delay - elapsed
                    logger.info(f"Waiting {wait_time:.1f}s before next request...")
                    time.sleep(wait_time)
                
                url = "https://steamcommunity.com/market/priceoverview/"
                params = {
                    'appid': APPID,
                    'currency': CURRENCY,
                    'market_hash_name': item_name
                }
                
                self.last_request_time = time.time()
                response = requests.get(url, params=params, timeout=15)
                self.request_count += 1
                
                if response.status_code == 429:
                    # Rate limited - exponential backoff
                    wait_time = delay * BACKOFF_MULTIPLIER * (attempt + 1)
                    logger.warning(f"Rate limited! Waiting {wait_time}s before retry {attempt + 1}/{MAX_RETRIES}")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                if not data.get('success'):
                    logger.warning(f"API returned success=false for {item_name}")
                    return None
                
                lowest_price_str = data.get('lowest_price', '')
                if not lowest_price_str:
                    logger.warning(f"No lowest_price for {item_name}")
                    return None
                
                price = float(lowest_price_str.replace('$', '').replace(',', '').strip())
                
                # Cache the result
                self.price_cache[item_name] = price
                logger.info(f"[{self.request_count}] Fetched {item_name}: ${price:.2f}")
                
                # Save cache every 10 requests
                if self.request_count % 10 == 0:
                    self.save_cache()
                
                return price
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error for {item_name}: {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = delay * BACKOFF_MULTIPLIER * (attempt + 1)
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    return None
            except (ValueError, KeyError) as e:
                logger.error(f"Parse error for {item_name}: {e}")
                return None
        
        return None
    
    def analyze_collection(self, collection_name: str, covert_skins: List[str], 
                          gold_models: List[str], finish_set: List[str],
                          is_gloves: bool = False) -> Optional[Dict]:
        """Analyze a single collection."""
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Analyzing: {collection_name}")
        logger.info(f"{'='*80}")
        
        # Find cheapest covert
        cheapest_covert_price = float('inf')
        cheapest_covert_name = None
        
        logger.info(f"Checking {len(covert_skins)} covert skins...")
        for skin in covert_skins:
            price = self.get_price_with_retry(skin)
            if price and price < cheapest_covert_price:
                cheapest_covert_price = price
                cheapest_covert_name = skin
        
        if not cheapest_covert_name:
            logger.warning("Could not find any covert prices")
            return None
        
        logger.info(f"Cheapest Covert: {cheapest_covert_name} @ ${cheapest_covert_price:.2f}")
        
        # Find cheapest gold - sample a few finishes instead of all
        # Focus on cheaper finishes first
        priority_finishes = {
            'knives': ['Safari Mesh', 'Boreal Forest', 'Forest DDPAT', 'Scorched', 'Urban Masked', 'Stained'],
            'chroma': ['Rust Coat', 'Ultraviolet', 'Damascus Steel'],
            'gamma': ['Bright Water', 'Black Laminate']
        }
        
        # Determine finish priority
        if 'Safari Mesh' in finish_set:
            sample_finishes = [f for f in priority_finishes['knives'] if f in finish_set][:3]
        elif 'Rust Coat' in finish_set:
            sample_finishes = [f for f in priority_finishes['chroma'] if f in finish_set][:3]
        elif 'Bright Water' in finish_set:
            sample_finishes = [f for f in priority_finishes['gamma'] if f in finish_set][:3]
        else:
            sample_finishes = finish_set[:3]
        
        # Sample first knife model with priority finishes
        # Include wear conditions for knives (they're required!)
        sample_model = gold_models[0]
        # Focus on cheapest wear conditions only
        wear_conditions = ['(Field-Tested)', '(Battle-Scarred)']
        
        cheapest_gold_price = float('inf')
        cheapest_gold_name = None
        
        # Also try vanilla knife (no finish)
        vanilla_name = f"★ {sample_model}"
        logger.info(f"Trying vanilla: {vanilla_name}")
        vanilla_price = self.get_price_with_retry(vanilla_name)
        if vanilla_price:
            cheapest_gold_price = vanilla_price
            cheapest_gold_name = vanilla_name
        
        logger.info(f"Sampling gold outcomes: {sample_model} with {len(sample_finishes)} finishes × {len(wear_conditions)} wears...")
        
        for finish in sample_finishes:
            for wear in wear_conditions:
                gold_name = f"★ {sample_model} | {finish} {wear}"
                price = self.get_price_with_retry(gold_name)
                if price and price < cheapest_gold_price:
                    cheapest_gold_price = price
                    cheapest_gold_name = gold_name
        
        if not cheapest_gold_name:
            logger.warning("Could not find any gold prices")
            return None
        
        logger.info(f"Cheapest Gold (sampled): {cheapest_gold_name} @ ${cheapest_gold_price:.2f}")
        
        # Calculate profitability
        cost_5x = cheapest_covert_price * 5
        gold_after_fee = cheapest_gold_price * (1 - STEAM_FEE_PERCENT)
        net_profit = gold_after_fee - cost_5x
        profit_margin = (net_profit / cost_5x * 100) if cost_5x > 0 else 0
        price_ratio = cheapest_gold_price / cheapest_covert_price
        
        logger.info(f"\nResult:")
        logger.info(f"  Ratio: {price_ratio:.2f}x")
        logger.info(f"  Cost 5x: ${cost_5x:.2f}")
        logger.info(f"  Gold after fee: ${gold_after_fee:.2f}")
        logger.info(f"  Profit: ${net_profit:.2f} ({profit_margin:.1f}%)")
        
        return {
            'collection': collection_name,
            'covert_skin': cheapest_covert_name,
            'covert_price': cheapest_covert_price,
            'gold_item': cheapest_gold_name,
            'gold_price': cheapest_gold_price,
            'price_ratio': price_ratio,
            'cost_5x': cost_5x,
            'gold_after_fee': gold_after_fee,
            'net_profit': net_profit,
            'profit_margin_pct': profit_margin,
            'is_profitable': net_profit > 0
        }


# Collections focused on more accessible/recent cases
FOCUSED_COLLECTIONS = {
    "Huntsman Weapon Case": {
        "covert_skins": [
            "M4A1-S | Cyrex (Minimal Wear)",
            "M4A1-S | Cyrex (Field-Tested)",
            "AK-47 | Vulcan (Field-Tested)",
            "AK-47 | Vulcan (Well-Worn)",
        ],
        "gold_models": ["Huntsman Knife"],
        "finish_set": ['Safari Mesh', 'Boreal Forest', 'Forest DDPAT', 'Scorched', 'Urban Masked', 'Stained', 'Blue Steel'],
        "is_gloves": False
    },
    
    "Falchion Case": {
        "covert_skins": [
            "AK-47 | Aquamarine Revenge (Field-Tested)",
            "AK-47 | Aquamarine Revenge (Well-Worn)",
            "AWP | Hyper Beast (Field-Tested)",
            "AWP | Hyper Beast (Well-Worn)",
        ],
        "gold_models": ["Falchion Knife"],
        "finish_set": ['Safari Mesh', 'Boreal Forest', 'Forest DDPAT', 'Scorched', 'Urban Masked', 'Stained'],
        "is_gloves": False
    },
    
    "Shadow Case": {
        "covert_skins": [
            "M4A1-S | Golden Coil (Field-Tested)",
            "M4A1-S | Golden Coil (Well-Worn)",
            "AK-47 | Fuel Injector (Field-Tested)",
            "AK-47 | Fuel Injector (Well-Worn)",
        ],
        "gold_models": ["Shadow Daggers"],
        "finish_set": ['Safari Mesh', 'Boreal Forest', 'Forest DDPAT', 'Scorched', 'Urban Masked', 'Stained'],
        "is_gloves": False
    },
    
    "Spectrum Case": {
        "covert_skins": [
            "AK-47 | Bloodsport (Field-Tested)",
            "AK-47 | Bloodsport (Well-Worn)",
            "USP-S | Neo-Noir (Field-Tested)",
            "USP-S | Neo-Noir (Well-Worn)",
        ],
        "gold_models": ["Bowie Knife", "Butterfly Knife", "Falchion Knife"],
        "finish_set": ['Rust Coat', 'Ultraviolet', 'Damascus Steel'],
        "is_gloves": False
    },
    
    "Horizon Case": {
        "covert_skins": [
            "AK-47 | Neon Rider (Field-Tested)",
            "AK-47 | Neon Rider (Well-Worn)",
            "AWP | Neo-Noir (Field-Tested)",
        ],
        "gold_models": ["Navaja Knife", "Stiletto Knife"],
        "finish_set": ['Safari Mesh', 'Boreal Forest', 'Forest DDPAT', 'Scorched'],
        "is_gloves": False
    },
    
    "Prisma Case": {
        "covert_skins": [
            "M4A4 | The Emperor (Field-Tested)",
            "M4A4 | The Emperor (Well-Worn)",
            "AWP | Atheris (Field-Tested)",
        ],
        "gold_models": ["Navaja Knife", "Stiletto Knife"],
        "finish_set": ['Rust Coat', 'Ultraviolet', 'Damascus Steel'],
        "is_gloves": False
    },
}


def main():
    logger.info("="*80)
    logger.info("CS2 SMART TRADE-UP SCANNER")
    logger.info("="*80)
    logger.info(f"Analyzing {len(FOCUSED_COLLECTIONS)} collections")
    logger.info(f"Start time: {datetime.now()}")
    logger.info("="*80)
    
    scanner = RateLimitedScanner()
    results = []
    
    for col_name, col_info in FOCUSED_COLLECTIONS.items():
        try:
            result = scanner.analyze_collection(
                collection_name=col_name,
                covert_skins=col_info['covert_skins'],
                gold_models=col_info['gold_models'],
                finish_set=col_info['finish_set'],
                is_gloves=col_info.get('is_gloves', False)
            )
            
            if result:
                results.append(result)
                
        except KeyboardInterrupt:
            logger.info("\n\nScan interrupted by user. Saving progress...")
            break
        except Exception as e:
            logger.error(f"Error analyzing {col_name}: {e}")
            continue
    
    # Save final cache
    scanner.save_cache()
    
    # Generate report
    if results:
        df = pd.DataFrame(results)
        df = df.sort_values('net_profit', ascending=False)
        
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        
        for idx, row in df.iterrows():
            status = "✓ PROFITABLE" if row['is_profitable'] else "✗ UNPROFITABLE"
            print(f"\n{row['collection']} {status}")
            print(f"  Covert: {row['covert_skin']} @ ${row['covert_price']:.2f}")
            print(f"  Gold: {row['gold_item']} @ ${row['gold_price']:.2f}")
            print(f"  Ratio: {row['price_ratio']:.2f}x | Profit: ${row['net_profit']:.2f} ({row['profit_margin_pct']:.1f}%)")
        
        # Save results
        df.to_csv('smart_scan_results.csv', index=False)
        print("\n" + "="*80)
        print("Results saved to smart_scan_results.csv")
        print(f"Total API requests: {scanner.request_count}")
        print(f"Cached prices: {len(scanner.price_cache)}")
        print("="*80)
        
        profitable = df[df['is_profitable']]
        print(f"\nSummary: {len(profitable)}/{len(df)} opportunities profitable")
        if len(profitable) > 0:
            best = profitable.iloc[0]
            print(f"Best: {best['collection']} (+${best['net_profit']:.2f}, {best['profit_margin_pct']:.1f}%)")
    else:
        logger.warning("No results collected")


if __name__ == "__main__":
    main()

