# CS2 Intelligent Knife Market Scraper

**The most advanced CS2 knife market scraper** with rate limit detection, VPN rotation, duplicate elimination, and comprehensive checklist-based scraping.

## 🚀 Key Features

### 1. **Rate Limit Detection & Auto-Recovery**
- Detects Steam rate limits automatically
- Triggers VPN server rotation (NordVPN/ExpressVPN)
- Exponential backoff with intelligent wait times
- Auto-retries failed searches

### 2. **Duplicate Detection**
- Tracks every knife collected in memory
- Filters out duplicates from overlapping searches
- Example: "M9 Bayonet Doppler" won't re-collect "Bayonet Doppler"

### 3. **Comprehensive Checklist System**
- Maintains database of ALL possible knife combinations
- Tracks which knives have been found (0/1)
- Prioritizes unfound knives in search strategy
- Shows completion percentage in real-time

### 4. **Intelligent Search Strategy**
- Searches based on what hasn't been found yet
- Groups searches by knife+finish to minimize API calls
- Adapts search delays based on success rate
- Strategic VPN rotation to avoid detection

## 📊 What You Get

### Comprehensive Database
Every CS2 knife combination:
- **19 knife types** × **25+ finishes** × **5 wear levels** × **2 (StatTrak/Regular)**
- Total: **~4,750 possible combinations**
- Tracks: `knife_type`, `finish`, `wear`, `is_stattrak`, `found`, `quantity`, `price`, `last_updated`

### Output Files

**`comprehensive_knife_checklist.csv`** - Master checklist
```csv
knife_type,finish,wear,is_stattrak,found,quantity,price,last_updated
Karambit,Doppler,FN,0,1,18,1244.78,2025-10-24T18:01:19
Karambit,Doppler,FN,1,1,8,1365.42,2025-10-24T18:01:19
Karambit,Doppler,MW,0,0,,,
```

## 🔧 Setup

### 1. Install Dependencies

```bash
cd CS2-Scanner
pip install -r requirements.txt
playwright install chromium
```

### 2. (Optional) Setup VPN

For large-scale scraping, install VPN CLI:

**NordVPN:**
```bash
# Download from: https://nordvpn.com/download/
nordvpn login
nordvpn connect
```

**ExpressVPN:**
```bash
# Download from: https://www.expressvpn.com/support/vpn-setup/app-for-windows/
expressvpn connect
```

### 3. Generate Comprehensive Checklist

```bash
python setup_intelligent_scraper.py
```

This creates:
- `comprehensive_knife_checklist.csv` - All 4,750 combinations
- `comprehensive_knife_checklist.json` - Same in JSON format

## ⚡ Usage

### Run the Intelligent Scraper

```bash
python intelligent_knife_scraper.py
```

**Interactive prompts:**
1. **Use VPN?** - Recommended for large scrapes (y/n)
2. **VPN type?** - nordvpn or expressvpn
3. **Headless mode?** - Run browser in background (y/n)

### What Happens

1. **Loads checklist** - Sees which knives haven't been found
2. **Plans searches** - Groups unfound knives by type+finish
3. **Scrapes systematically** - Searches in batches of 10
4. **Handles rate limits** - Auto-switches IP and retries
5. **Eliminates duplicates** - Filters out already-collected knives
6. **Updates checklist** - Marks found knives with quantity/price
7. **Saves progress** - Checkpoints after each batch

### Example Session

```
BATCH 1: 10 searches
================================================================================

[1/10] Karambit Doppler
  Extracted 6 raw listings
  Skipped 0 duplicates
  Filtered 0 irrelevant results
  ✓ Collected 6 new knives
  + Karambit | Doppler (FN) - 18 @ $1244.78
  + Karambit | Doppler (FN) [ST] - 8 @ $1365.42
  + Karambit | Doppler (MW) - 5 @ $1296.18

[2/10] M9 Bayonet Gamma Doppler
  Extracted 9 raw listings
  Skipped 3 duplicates (Bayonet Gamma Doppler already collected)
  Filtered 2 irrelevant results (Bayonet Doppler)
  ✓ Collected 4 new knives
  + M9 Bayonet | Gamma Doppler (FN) - 4 @ $1424.71
  + M9 Bayonet | Gamma Doppler (MW) - 2 @ $1816.74

... rate limit detected after 15 searches ...

⚠️  RATE LIMIT DETECTED
================================================================================
Rate limit hit #1
Wait time: 60 seconds (1.0 minutes)
Attempting to switch IP address...
✓ NordVPN: Connected to new server (us9876)
✓ IP switched successfully
Reduced wait time to 30 seconds
Waiting 30 seconds before retry...
  30 seconds remaining...
Wait complete, resuming scraping
================================================================================

Progress: 45.2% complete
  Found: 2,148/4,750
  Successful scrapes: 127
  Failed scrapes: 3
```

## 📁 Output Files

After scraping:

1. **`comprehensive_knife_checklist.csv`** - Updated with all found knives
2. **`intelligent_scrape_YYYYMMDD_HHMMSS.log`** - Detailed log file
3. **Progress tracking** - Real-time completion percentage

## 🎯 Advantages

| Feature | Old Scraper | Intelligent Scraper |
|---------|-------------|---------------------|
| Rate Limit Handling | ❌ Crashes | ✅ Auto-detects & recovers |
| VPN Rotation | ❌ Manual | ✅ Automatic |
| Duplicate Detection | ❌ Collects duplicates | ✅ Filters duplicates |
| Search Strategy | 🔄 Fixed list | ✅ Checklist-based |
| Progress Tracking | ❌ None | ✅ Real-time percentage |
| Completion Guarantee | ❌ Partial | ✅ Comprehensive |
| Resume Support | ❌ Start over | ✅ Continues from checkpoint |

## 🔍 How It Works

### 1. Comprehensive Database Generation
```python
# Every knife type × finish × wear × StatTrak
Karambit × Doppler × FN × Regular = 1 entry
Karambit × Doppler × FN × StatTrak = 1 entry
... (4,750 total combinations)
```

### 2. Intelligent Search Planning
```python
# Instead of searching randomly:
queries = get_next_search_queries()  # Returns unfound knives only

# Groups searches efficiently:
"Karambit Doppler" → Finds all Karambit Dopplers in one search
```

### 3. Duplicate Elimination
```python
# Tracks collected knives in memory:
collected_knives = {
    ('Karambit', 'Doppler', 'FN', 0),
    ('Karambit', 'Doppler', 'FN', 1),
    ...
}

# Filters duplicates during parsing:
if is_duplicate(knife_type, finish, wear, is_stattrak):
    continue  # Skip
```

### 4. Rate Limit Recovery
```python
# Detects rate limit:
if "Target page closed" or "Too Many Requests":
    handle_rate_limit()
    
def handle_rate_limit():
    1. Close browser
    2. Switch VPN server (new IP)
    3. Wait (exponential backoff: 60s → 120s → 240s)
    4. Reinitialize browser
    5. Retry same search
```

## 📈 Completion Tracking

View progress at any time:
```bash
python -c "from comprehensive_knife_list import load_checklist, get_completion_stats; \
           stats = get_completion_stats(load_checklist()); \
           print(f'Completion: {stats[\"completion_percent\"]:.1f}%')"
```

## 🛠️ Troubleshooting

### Rate limits hit repeatedly
- Increase base wait time in `rate_limit_handler.py`
- Use VPN with more servers
- Run during off-peak hours

### VPN not switching
- Verify VPN CLI is installed: `nordvpn --version`
- Login to VPN: `nordvpn login`
- Check permissions (may need admin/sudo)

### Browser crashes
- Run in visible mode (headless=n) to debug
- Check system resources (RAM/CPU)
- Reduce batch size in scraper

## 📋 Files Overview

| File | Purpose |
|------|---------|
| `intelligent_knife_scraper.py` | Main scraper with all features |
| `rate_limit_handler.py` | Rate limit detection & VPN rotation |
| `comprehensive_knife_list.py` | Database generator & checklist manager |
| `setup_intelligent_scraper.py` | One-time setup script |
| `comprehensive_knife_checklist.csv` | Master checklist (generated) |

## 🎉 Expected Results

After complete run:
- **4,750 knife combinations** checked
- **~1,500-2,500 knives found** (many combinations don't exist on market)
- **Zero duplicates** (intelligent filtering)
- **Complete coverage** (checklist ensures nothing missed)
- **Market snapshot** with quantities and prices

## 🚀 Next Steps

1. **Generate hidden gems report** from comprehensive data
2. **Track price changes** over time by re-running
3. **Analyze market trends** (most/least available, price ranges)
4. **Investment opportunities** (rare knives, undervalued items)

---

**Built for comprehensive, intelligent, and respectful market data collection.**

