# CS2 Trade-Up Scanner

Scans Steam Community Market to find profitable 5 Covert → 1 Gold trade-up opportunities in Counter-Strike 2.

## New CS2 Update (2024)
Valve now allows players to trade-up 5 Covert skins for 1 Gold (knife/glove) **in the same collection**. This scanner helps identify profitable opportunities by comparing:
- Cost of 5x cheapest covert skin in a collection
- vs Price of cheapest gold outcome (after 13% Steam fee)

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Choose Your Scanner

#### Smart Scanner (Recommended)
Handles rate limits gracefully with caching and exponential backoff:
```bash
python smart_scanner.py
```

#### Market Scraper
Gets actual purchasable listings (skips "Sold!" items):
```bash
python market_scraper.py
```

#### Manual Analyzer
When you have specific prices already:
```bash
python manual_analyzer.py
```

## Avoiding Rate Limits

Steam aggressively rate-limits API requests. Best practices:

### Option 1: Use VPN on Different Device
Run the scanner on a different device with a VPN to bypass IP-based rate limits:
```bash
# On your VPN-connected device:
git clone https://github.com/shlinkLFO/CS2-Scanner.git
cd CS2-Scanner
pip install -r requirements.txt
python smart_scanner.py
```

### Option 2: Patience Mode
The smart scanner waits 10+ seconds between requests and caches results. Just let it run - it will take time but works reliably.

### Option 3: Manual Entry
Manually check Steam Market prices and use the manual analyzer:
```bash
# Edit manual_analyzer.py with your prices, then:
python manual_analyzer.py
```

## How It Works

1. **Find Cheapest Covert**: Scans all covert skins in a collection
2. **Find Cheapest Gold**: Checks knife/glove outcomes (samples common finishes)
3. **Calculate Profit**:
   - Cost: 5x covert price
   - Revenue: Gold price × 87% (after 13% Steam fee)
   - Profit: Revenue - Cost

## Files

- `smart_scanner.py` - Main scanner with rate limit handling
- `market_scraper.py` - Advanced scraper for actual buy orders
- `manual_analyzer.py` - Analyze with manual price input
- `tradeup_scanner.py` - Full collection scanner (legacy)
- `price_cache.json` - Cached prices (auto-generated)
- `market_prices.json` - Market scraper cache
- `smart_scan_results.csv` - Results output

## Collections Analyzed

Focus on accessible collections:
- Huntsman Weapon Case
- Falchion Case
- Shadow Case
- Spectrum Case
- Horizon Case
- Prisma Case
- (More can be added)

**Note**: Breakout collection (Butterfly Knife) is excluded as it's known to be unprofitable.

## Understanding Results

```
Falchion Case ✓ PROFITABLE
  Covert: AK-47 | Aquamarine Revenge (Well-Worn) @ $35.99
  Gold: ★ Falchion Knife | Safari Mesh @ $250.00
  Ratio: 6.95x | Profit: $37.55 (20.9%)
```

- **Ratio**: Gold price / Covert price (higher = better)
- **Profit**: Net profit after buying 5 coverts and selling gold
- **Margin**: Profit as percentage of investment

## Tips

1. **Volume Matters**: Check actual market volume before executing
2. **Wear Matters**: Field-Tested and Well-Worn coverts are often better ROI
3. **Gold Variance**: Some gold finishes are much cheaper (Safari Mesh, Boreal Forest)
4. **Market Volatility**: Prices change - always verify before trading up
5. **Float Values**: Some patterns (Case Hardened, Fade) vary wildly by pattern

## Troubleshooting

**"Rate limited / 429 errors"**
- Use VPN on different device
- Increase delay in scanner (edit `BASE_DELAY`)
- Use cached results

**"No lowest_price" warnings**
- Item may be extremely rare/expensive
- Try different wear conditions
- Check item exists on market

**Prices seem wrong**
- Clear cache files and re-run
- Verify item names match Steam Market exactly
- Check currency is USD

## Disclaimer

- Market prices fluctuate constantly
- This tool is for research/educational purposes
- Always verify prices manually before trading
- Past profitability doesn't guarantee future profits
- Steam market has fees and delays

