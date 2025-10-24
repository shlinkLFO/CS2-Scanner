"""
CS2 Trade-Up Market Scraper
Scrapes actual buy listings from Steam Market to find real purchasable prices
"""

import time
import requests
from bs4 import BeautifulSoup
import re
import json
import logging
from typing import Optional, Dict
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

APPID = 730
BASE_DELAY = 12  # Conservative delay between requests
MAX_RETRIES = 3
CACHE_FILE = "market_prices.json"


class SteamMarketScraper:
    def __init__(self, use_cache=True):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.cache = self.load_cache() if use_cache else {}
        self.last_request_time = 0
        self.request_count = 0
    
    def load_cache(self) -> Dict:
        """Load price cache."""
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_cache(self):
        """Save price cache."""
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f, indent=2)
        logger.info(f"Saved {len(self.cache)} prices to cache")
    
    def get_lowest_buy_order(self, item_name: str) -> Optional[float]:
        """
        Get the lowest actual buy order (not "Sold!" items) from Steam Market.
        Uses the market JSON API endpoint for better reliability.
        """
        
        # Check cache
        if item_name in self.cache:
            logger.info(f"[CACHED] {item_name}: ${self.cache[item_name]:.2f}")
            return self.cache[item_name]
        
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < BASE_DELAY:
            wait = BASE_DELAY - elapsed
            logger.info(f"Rate limit: waiting {wait:.1f}s...")
            time.sleep(wait)
        
        for attempt in range(MAX_RETRIES):
            try:
                # Use the itemordershistogram endpoint to get actual buy orders
                url = f"https://steamcommunity.com/market/itemordershistogram"
                params = {
                    'country': 'US',
                    'language': 'english',
                    'currency': 1,
                    'item_nameid': self._get_item_nameid(item_name),
                    'two_factor': 0
                }
                
                self.last_request_time = time.time()
                response = self.session.get(url, params=params, timeout=15)
                self.request_count += 1
                
                if response.status_code == 429:
                    wait = BASE_DELAY * (2 ** attempt)
                    logger.warning(f"Rate limited! Waiting {wait}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(wait)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                # Get lowest sell order (what we'd pay to buy)
                if data.get('success') and data.get('lowest_sell_order'):
                    price = float(data['lowest_sell_order']) / 100  # Convert cents to dollars
                    self.cache[item_name] = price
                    logger.info(f"[{self.request_count}] {item_name}: ${price:.2f}")
                    
                    if self.request_count % 5 == 0:
                        self.save_cache()
                    
                    return price
                else:
                    # Fallback to price overview API
                    return self._get_price_fallback(item_name)
                    
            except Exception as e:
                logger.error(f"Error fetching {item_name}: {e}")
                if attempt < MAX_RETRIES - 1:
                    wait = BASE_DELAY * (2 ** attempt)
                    time.sleep(wait)
                else:
                    # Try fallback
                    return self._get_price_fallback(item_name)
        
        return None
    
    def _get_item_nameid(self, item_name: str) -> Optional[int]:
        """
        Get the internal Steam item_nameid for an item.
        This is needed for the itemordershistogram endpoint.
        
        For now, we'll use the simpler price overview endpoint.
        """
        # This would require additional scraping, so we'll use fallback
        raise NotImplementedError("Use fallback method")
    
    def _get_price_fallback(self, item_name: str) -> Optional[float]:
        """
        Fallback method using the price overview API.
        This gives us the lowest listed price.
        """
        try:
            url = "https://steamcommunity.com/market/priceoverview/"
            params = {
                'appid': APPID,
                'currency': 1,
                'market_hash_name': item_name
            }
            
            # Ensure rate limiting
            elapsed = time.time() - self.last_request_time
            if elapsed < BASE_DELAY:
                time.sleep(BASE_DELAY - elapsed)
            
            self.last_request_time = time.time()
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 429:
                logger.warning(f"Rate limited on fallback for {item_name}")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and data.get('lowest_price'):
                price_str = data['lowest_price']
                # Parse price (format: "$123.45" or "US$ 123.45")
                price = float(re.sub(r'[^\d.]', '', price_str))
                
                self.cache[item_name] = price
                logger.info(f"[FALLBACK] {item_name}: ${price:.2f}")
                return price
            else:
                logger.warning(f"No price data for {item_name}")
                return None
                
        except Exception as e:
            logger.error(f"Fallback failed for {item_name}: {e}")
            return None


def test_scraper():
    """Test the scraper with a few items."""
    scraper = SteamMarketScraper()
    
    test_items = [
        "AK-47 | Aquamarine Revenge (Well-Worn)",
        "★ Shadow Daggers | Safari Mesh",
        "M4A1-S | Cyrex (Field-Tested)"
    ]
    
    print("\n" + "="*80)
    print("TESTING MARKET SCRAPER")
    print("="*80 + "\n")
    
    for item in test_items:
        price = scraper.get_lowest_buy_order(item)
        if price:
            print(f"✓ {item}: ${price:.2f}")
        else:
            print(f"✗ {item}: No price found")
        print()
    
    scraper.save_cache()
    print(f"\nTotal requests: {scraper.request_count}")


if __name__ == "__main__":
    test_scraper()

