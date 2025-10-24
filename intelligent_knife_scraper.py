"""
Intelligent CS2 Knife Market Scraper
- Rate limit detection & VPN rotation
- Duplicate detection
- Checklist-based comprehensive scraping
- Strategic search ordering
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Set, Tuple
from playwright.async_api import async_playwright, Browser, Page
import re

from rate_limit_handler import RateLimitHandler
from comprehensive_knife_list import (
    load_checklist, save_updated_checklist, mark_knife_found,
    get_unfound_knives, get_completion_stats
)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'intelligent_scrape_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', 
                          encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Reduce playwright noise
logging.getLogger('playwright').setLevel(logging.WARNING)


class IntelligentKnifeScraper:
    def __init__(self, use_vpn: bool = False, vpn_type: str = "nordvpn", headless: bool = True):
        self.browser: Browser = None
        self.page: Page = None
        self.playwright = None
        self.headless = headless
        
        # Rate limit handling
        self.rate_limit_handler = RateLimitHandler()
        self.use_vpn = use_vpn
        self.vpn_type = vpn_type
        
        # Tracking
        self.collected_knives: Set[Tuple[str, str, str, int]] = set()
        self.successful_scrapes = 0
        self.failed_scrapes = 0
        
        # Checklist
        self.checklist = load_checklist()
        logger.info(f"Loaded checklist: {len(self.checklist)} total combinations")
    
    async def init_browser(self):
        """Initialize browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await context.new_page()
        logger.info("Browser initialized")
    
    def is_duplicate(self, knife_type: str, finish: str, wear: str, is_stattrak: int) -> bool:
        """Check if this knife has already been collected"""
        key = (knife_type, finish, wear, is_stattrak)
        return key in self.collected_knives
    
    def add_to_collected(self, knife_type: str, finish: str, wear: str, is_stattrak: int):
        """Mark knife as collected"""
        key = (knife_type, finish, wear, is_stattrak)
        self.collected_knives.add(key)
    
    async def scrape_search(self, search_query: str, expected_knife: str = None, 
                          expected_finish: str = None, retry_count: int = 0) -> List[Dict]:
        """
        Scrape a search query with rate limit handling
        
        Args:
            search_query: Search string for Steam Market
            expected_knife: Expected knife type to filter for
            expected_finish: Expected finish to filter for
            retry_count: Number of retries attempted
        """
        if retry_count > 3:
            logger.error(f"Max retries reached for '{search_query}', skipping")
            return []
        
        url = f"https://steamcommunity.com/market/search?appid=730&q={search_query.replace(' ', '+')}&start=0&count=100"
        
        try:
            logger.info(f"Searching: {search_query}")
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Strategic delay
            delay = self.rate_limit_handler.get_strategic_delay(self.successful_scrapes)
            await asyncio.sleep(delay)
            
            # Check if page loaded correctly
            try:
                await self.page.wait_for_selector('.market_listing_row', timeout=5000)
            except:
                # No results - check if rate limited
                page_content = await self.page.content()
                if self.rate_limit_handler.detect_rate_limit(page_html=page_content):
                    logger.warning(f"Rate limit detected on '{search_query}'")
                    await self.handle_rate_limit_and_retry(search_query, expected_knife, 
                                                          expected_finish, retry_count)
                    return []
                else:
                    logger.info(f"No results for '{search_query}'")
                    return []
            
            # Extract data
            listings = await self.extract_page_data()
            
            if not listings:
                logger.info(f"No listings extracted for '{search_query}'")
                return []
            
            logger.info(f"  Extracted {len(listings)} raw listings")
            
            # Log first listing for debugging
            if listings:
                logger.debug(f"First listing sample: {listings[0]}")
            
            # Parse and filter
            parsed_listings = []
            duplicates_skipped = 0
            irrelevant_skipped = 0
            parse_failed = 0
            
            for listing in listings:
                parsed = self.parse_listing(listing)
                
                if not parsed:
                    parse_failed += 1
                    logger.debug(f"Failed to parse: {listing.get('name', 'NO NAME')}")
                    continue
                
                # Filter by expected knife/finish if specified
                if expected_knife and parsed['knife_type'] != expected_knife:
                    irrelevant_skipped += 1
                    continue
                
                if expected_finish and parsed['finish'] != expected_finish:
                    irrelevant_skipped += 1
                    continue
                
                # Check for duplicates
                if self.is_duplicate(parsed['knife_type'], parsed['finish'], 
                                   parsed['wear'], parsed['is_stattrak']):
                    duplicates_skipped += 1
                    continue
                
                # New knife!
                parsed_listings.append(parsed)
                self.add_to_collected(parsed['knife_type'], parsed['finish'], 
                                    parsed['wear'], parsed['is_stattrak'])
                
                # Update checklist
                mark_knife_found(self.checklist, parsed['knife_type'], parsed['finish'],
                               parsed['wear'], parsed['is_stattrak'], 
                               parsed['quantity'], parsed['price'])
            
            if parse_failed > 0:
                logger.warning(f"  Failed to parse {parse_failed} listings")
            if duplicates_skipped > 0:
                logger.info(f"  Skipped {duplicates_skipped} duplicates")
            if irrelevant_skipped > 0:
                logger.info(f"  Filtered {irrelevant_skipped} irrelevant results")
            
            if len(parsed_listings) > 0:
                logger.info(f"  ✓ Collected {len(parsed_listings)} new knives")
            else:
                logger.warning(f"  ✗ Collected 0 new knives (check parsing logic)")
            
            self.successful_scrapes += 1
            
            # Reset rate limit counter after successful scrapes
            if self.successful_scrapes % 5 == 0:
                self.rate_limit_handler.reset_rate_limit_counter()
            
            return parsed_listings
        
        except Exception as e:
            # Check if rate limit
            if self.rate_limit_handler.detect_rate_limit(error=e):
                logger.warning(f"Rate limit detected (exception): {e}")
                await self.handle_rate_limit_and_retry(search_query, expected_knife, 
                                                      expected_finish, retry_count)
                return []
            else:
                logger.error(f"Error scraping '{search_query}': {e}")
                self.failed_scrapes += 1
                return []
    
    async def handle_rate_limit_and_retry(self, search_query: str, expected_knife: str,
                                         expected_finish: str, retry_count: int):
        """Handle rate limit and retry the search"""
        # Close and reinitialize browser
        try:
            await self.close()
        except:
            pass
        
        # Handle rate limit (wait + VPN switch if available)
        vpn = self.vpn_type if self.use_vpn else None
        self.rate_limit_handler.handle_rate_limit(vpn)
        
        # Reinitialize browser
        await self.init_browser()
        
        # Retry the search
        await self.scrape_search(search_query, expected_knife, expected_finish, retry_count + 1)
    
    async def extract_page_data(self) -> List[Dict]:
        """Extract listing data from current page"""
        listings = await self.page.evaluate('''() => {
            const results = [];
            const rows = document.querySelectorAll('.market_listing_row');
            
            rows.forEach((row) => {
                try {
                    const nameEl = row.querySelector('.market_listing_item_name');
                    const name = nameEl ? nameEl.innerText.trim() : '';
                    
                    const qtyEl = row.querySelector('.market_listing_num_listings_qty');
                    const quantity = qtyEl ? parseInt(qtyEl.innerText.trim().replace(/,/g, '')) || 0 : 0;
                    
                    let priceText = '';
                    let priceEl = row.querySelector('.market_listing_price');
                    if (priceEl) priceText = priceEl.innerText.trim();
                    
                    if (!priceText) {
                        priceEl = row.querySelector('.market_listing_their_price');
                        if (priceEl) priceText = priceEl.innerText.trim();
                    }
                    
                    const gameEl = row.querySelector('.market_listing_game_name');
                    const game = gameEl ? gameEl.innerText.trim() : '';
                    
                    results.push({name, quantity, price_text: priceText, game});
                } catch (e) {
                    console.error('Error extracting row:', e);
                }
            });
            
            return results;
        }''')
        
        return listings
    
    def parse_listing(self, listing: Dict) -> Dict:
        """Parse a single listing"""
        try:
            name = listing.get('name', '')
            logger.debug(f"Parsing: {name}")
            
            if '★' not in name:
                logger.debug(f"  Rejected: No star character")
                return None
            
            if 'knife' not in name.lower():
                logger.debug(f"  Rejected: Not a knife")
                return None
            
            is_stattrak = 'StatTrak™' in name
            name_clean = name.replace('★', '').replace('StatTrak™', '').strip()
            
            if '|' not in name_clean:
                logger.debug(f"  Rejected: No pipe separator in '{name_clean}'")
                return None
            
            parts = name_clean.split('|')
            knife_type = parts[0].strip()
            finish_and_wear = parts[1].strip() if len(parts) > 1 else ''
            
            logger.debug(f"  Knife: {knife_type}, Finish+Wear: {finish_and_wear}")
            
            # Extract wear
            wear_map = {
                'Factory New': 'FN',
                'Minimal Wear': 'MW',
                'Field-Tested': 'FT',
                'Well-Worn': 'WW',
                'Battle-Scarred': 'BS'
            }
            
            wear = None
            finish = finish_and_wear
            for wear_full, wear_abbr in wear_map.items():
                if wear_full in finish_and_wear:
                    wear = wear_abbr
                    finish = finish_and_wear.replace(f'({wear_full})', '').strip()
                    break
            
            if not wear:
                logger.debug(f"  Rejected: No wear level found in '{finish_and_wear}'")
                return None
            
            logger.debug(f"  Extracted - Finish: {finish}, Wear: {wear}")
            
            # Extract price
            price_text = listing.get('price_text', '')
            logger.debug(f"  Price text: '{price_text}'")
            
            price_match = re.search(r'\$\s*([\d,]+\.\d{2})', price_text)
            if not price_match:
                price_match = re.search(r'\$\s*([\d,]+)', price_text)
            
            if not price_match:
                logger.debug(f"  Rejected: Could not extract price from '{price_text}'")
                return None
            
            price = float(price_match.group(1).replace(',', ''))
            quantity = listing.get('quantity', 0)
            
            logger.debug(f"  Success: {knife_type} | {finish} ({wear}) - {quantity} @ ${price:.2f}")
            
            return {
                'knife_type': knife_type,
                'finish': finish,
                'wear': wear,
                'is_stattrak': 1 if is_stattrak else 0,
                'quantity': quantity,
                'price': price,
                'full_name': name,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.debug(f"Parse error: {e}")
            return None
    
    def get_next_search_queries(self, batch_size: int = 5) -> List[Tuple[str, str, str]]:
        """
        Get next batch of search queries based on unfound knives
        Returns: List of (search_query, expected_knife, expected_finish)
        """
        unfound = get_unfound_knives(self.checklist)
        
        if not unfound:
            logger.info("All knives found!")
            return []
        
        # Group by knife + finish to minimize searches
        search_groups = {}
        for knife in unfound:
            key = (knife['knife_type'], knife['finish'])
            if key not in search_groups:
                search_groups[key] = []
            search_groups[key].append(knife)
        
        # Create search queries
        queries = []
        for (knife_type, finish), knives in list(search_groups.items())[:batch_size]:
            search_query = f"{knife_type} {finish}"
            queries.append((search_query, knife_type, finish))
        
        return queries
    
    async def close(self):
        """Cleanup"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


async def main():
    import sys
    
    # Check for test mode
    max_searches = None
    if len(sys.argv) > 1:
        try:
            max_searches = int(sys.argv[1])
            print("\n" + "="*100)
            print(f"TEST MODE - Limiting to {max_searches} searches")
            print("="*100 + "\n")
        except ValueError:
            pass
    
    print("\n" + "="*100)
    print("INTELLIGENT CS2 KNIFE MARKET SCRAPER")
    print("="*100)
    print("Features: Rate Limit Detection, VPN Rotation, Duplicate Detection, Checklist-Based")
    print("="*100 + "\n")
    
    use_vpn = input("Use VPN for IP rotation? (y/n): ").strip().lower() == 'y'
    vpn_type = "nordvpn"
    if use_vpn:
        vpn_type = input("VPN type (nordvpn/expressvpn): ").strip().lower() or "nordvpn"
    
    headless = input("Run in headless mode? (y/n): ").strip().lower() == 'y'
    
    scraper = IntelligentKnifeScraper(use_vpn=use_vpn, vpn_type=vpn_type, headless=headless)
    
    try:
        await scraper.init_browser()
        
        # Get initial stats
        stats = get_completion_stats(scraper.checklist)
        print(f"\nInitial completion: {stats['completion_percent']:.1f}%")
        print(f"  Found: {stats['found']}/{stats['total_combinations']}")
        print(f"  Remaining: {stats['not_found']}\n")
        
        # Scrape in batches
        batch_num = 0
        total_searches_done = 0
        
        while True:
            batch_num += 1
            
            # Check if we've hit max searches (test mode)
            if max_searches and total_searches_done >= max_searches:
                print(f"\n✓ Test complete - reached {max_searches} searches limit")
                break
            
            # Get next queries
            batch_size = 10
            if max_searches:
                # Limit batch size if we're close to max
                remaining = max_searches - total_searches_done
                batch_size = min(batch_size, remaining)
            
            queries = scraper.get_next_search_queries(batch_size=batch_size)
            
            if not queries:
                print("\n✓ All knives scraped!")
                break
            
            print(f"\n{'='*100}")
            print(f"BATCH {batch_num}: {len(queries)} searches")
            print(f"{'='*100}")
            
            for i, (query, expected_knife, expected_finish) in enumerate(queries, 1):
                print(f"\n[{i}/{len(queries)}] {query}")
                results = await scraper.scrape_search(query, expected_knife, expected_finish)
                total_searches_done += 1
                
                if results:
                    for r in results:
                        st = "[ST]" if r['is_stattrak'] else ""
                        print(f"  + {r['knife_type']} | {r['finish']} ({r['wear']}) {st} - "
                              f"{r['quantity']} @ ${r['price']:.2f}")
            
            # Save progress
            save_updated_checklist(scraper.checklist)
            
            # Stats
            stats = get_completion_stats(scraper.checklist)
            print(f"\n{'='*100}")
            print(f"Progress: {stats['completion_percent']:.1f}% complete")
            print(f"  Found: {stats['found']}/{stats['total_combinations']}")
            print(f"  Successful scrapes: {scraper.successful_scrapes}")
            print(f"  Failed scrapes: {scraper.failed_scrapes}")
            print(f"{'='*100}")
        
        # Final summary
        print("\n" + "="*100)
        print("SCRAPING COMPLETE")
        print("="*100)
        stats = get_completion_stats(scraper.checklist)
        print(f"Total knives found: {stats['found']}/{stats['total_combinations']}")
        print(f"Completion: {stats['completion_percent']:.1f}%")
        print(f"Checklist saved to: comprehensive_knife_checklist.csv")
        print("="*100)
    
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())

