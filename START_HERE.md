# 🎯 CS2 Knife Market Scraper - START HERE

## What This Does

Scrapes **every CS2 knife** from Steam Market with:
- ✅ **Rate limit detection & auto-recovery** (switches VPN, retries)
- ✅ **Duplicate elimination** (each knife collected once)
- ✅ **Comprehensive coverage** (2,966 knife combinations tracked)
- ✅ **Intelligent search** (only searches unfound knives)

## Quick Start (2 Commands)

### 1. Generate Comprehensive Checklist
```bash
python setup_intelligent_scraper.py
```
Creates `comprehensive_knife_checklist.csv` with all 2,966 knife combinations (1,483 regular + 1,483 StatTrak).

### 2. Run the Scraper

**Test Mode (25 searches - recommended first run):**
```bash
python intelligent_knife_scraper.py 25
```

**Full Mode (all knives):**
```bash
python intelligent_knife_scraper.py
```

**Interactive Prompts:**
```
Use VPN for IP rotation? (y/n): y        ← Recommended
VPN type (nordvpn/expressvpn): nordvpn
Run in headless mode? (y/n): n           ← TEST: NO (watch it work)
                                            FULL: YES (faster)
```

**What Happens:**
1. Loads checklist → Shows completion %
2. Searches systematically through unfound knives
3. Filters duplicates automatically
4. Detects rate limits → Switches VPN → Retries
5. Saves progress after each batch
6. Shows real-time completion percentage

**Expected Runtime:** 6-12 hours for full coverage

## VPN Setup (Recommended)

**NordVPN:**
```bash
# Download: https://nordvpn.com/download/
nordvpn login
nordvpn connect
```

**ExpressVPN:**
```bash
# Download: https://www.expressvpn.com/
expressvpn connect smart
```

See `nordvpn_manual_install.md` for detailed setup.

## What You Get

**Output: `comprehensive_knife_checklist.csv`**

Every CS2 knife with:
- `found` (0/1) - Does it exist on market?
- `quantity` - How many listings available?
- `price` - Lowest price (best offer)?
- `last_updated` - When was it scraped?

**Example:**
```csv
knife_type,finish,wear,is_stattrak,found,quantity,price,last_updated
Karambit,Doppler,FN,0,1,18,1244.78,2025-10-24T18:01:19
Karambit,Doppler,FN,1,1,8,1365.42,2025-10-24T18:01:19
Shadow Daggers,Tiger Tooth,FN,0,1,63,135.94,2025-10-24T18:03:15
Navaja Knife,Tiger Tooth,FN,0,1,52,125.00,2025-10-24T18:03:03
```

**Expected Results:**
- ~1,500-2,000 knives found (out of 2,966 checked)
- Zero duplicates
- Complete market snapshot with quantities & prices

## Example Session

```
BATCH 1: 10 searches
================================================================================

[1/10] Karambit Doppler
  Extracted 6 raw listings
  Skipped 0 duplicates
  ✓ Collected 6 new knives
  + Karambit | Doppler (FN) - 18 @ $1244.78
  + Karambit | Doppler (FN) [ST] - 8 @ $1365.42

[2/10] M9 Bayonet Gamma Doppler
  Extracted 9 raw listings
  Skipped 3 duplicates     ← Filtered out Bayonet Gamma Doppler
  ✓ Collected 4 new knives

... after 15 searches, rate limit hits ...

⚠️  RATE LIMIT DETECTED
================================================================================
Switching VPN server...
✓ NordVPN: Connected to new server
Wait time: 30 seconds
Wait complete, resuming scraping
================================================================================

Progress: 12.5% complete (370/2,966)
  Successful scrapes: 15
  Rate limit hits: 1 (recovered)
```

## Key Features Explained

### 1. Rate Limit Auto-Recovery
**Before:** Browser closes → Script crashes
**Now:** Detects closure → Switches VPN → Waits → Retries automatically

### 2. Duplicate Elimination
**Before:** "M9 Doppler" search also returns "Bayonet Doppler" (already collected)
**Now:** Tracks collected knives → Filters duplicates → "Skipped 3 duplicates"

### 3. Comprehensive Checklist
**Before:** No way to know what's left to scrape
**Now:** 
```
Checklist: 2,966 total combinations
Found: 370/2,966 (12.5% complete)
Remaining: 2,596 unfound knives
→ Searches next batch of unfound knives
```

## Resume After Interrupt

Just run it again! The scraper:
- Loads existing `comprehensive_knife_checklist.csv`
- Sees which knives are already found
- Continues from where it left off

## Files Structure

```
CS2-Scanner/
├── START_HERE.md                          ← You are here
├── README.md                              ← Full documentation
├── nordvpn_manual_install.md              ← VPN setup guide
│
├── intelligent_knife_scraper.py           ← Main scraper (run this)
├── setup_intelligent_scraper.py           ← One-time setup
├── rate_limit_handler.py                  ← Rate limit detection & VPN rotation
├── comprehensive_knife_list.py            ← Database generator (2,966 combinations)
│
├── comprehensive_knife_checklist.csv      ← Output (updated as scraper runs)
├── comprehensive_knife_checklist.json     ← Output (JSON format)
├── intelligent_scrape_*.log               ← Detailed logs
│
├── requirements.txt                       ← Python dependencies
├── install_nordvpn.ps1                    ← VPN installer
├── quick_nordvpn_install.ps1              ← VPN quick setup
└── complete_covert_analysis.*             ← Reference data (covert skins)
```

## Monitor Progress While Running

**In another terminal:**
```bash
# View log in real-time
tail -f intelligent_scrape_*.log

# Count found knives
grep ",1," comprehensive_knife_checklist.csv | wc -l

# View checklist
head -20 comprehensive_knife_checklist.csv
```

## Expected Final Results

```
SCRAPING COMPLETE
================================================================================
Total knives found: 1,600/2,966
Completion: 54.0%
Successful scrapes: 284
Failed scrapes: 3
Rate limit hits: 12 (all recovered)
Duplicates filtered: 437
Checklist saved to: comprehensive_knife_checklist.csv
================================================================================
```

**Why not 100%?** 
Many combinations don't exist on Steam Market:
- Too expensive (>$2,000 Steam Market limit)
- Too rare (zero listings currently)
- Invalid combinations (Fade only has FN/MW, no FT/WW/BS)

The scraper checks ALL 2,966 and documents what actually exists.

## Troubleshooting

**Rate limits hit repeatedly:**
- Ensure VPN is installed and working: `nordvpn status`
- VPN will auto-rotate, but may need longer wait times

**VPN not switching:**
- Verify CLI is installed: `nordvpn --version`
- Login: `nordvpn login`
- Test connection: `nordvpn connect`

**Browser crashes:**
- Run in visible mode (`headless=n`) to debug
- Check system resources (RAM/CPU)

**"Target page closed" errors:**
- This is expected! It's how the scraper detects rate limits
- The scraper will auto-recover (switch VPN, retry)

## First Run Recommendation

**Test Run (25 searches, ~15-20 minutes):**
```bash
python intelligent_knife_scraper.py 25
```

**Prompts:**
- VPN: `y` (recommended)
- VPN type: `nordvpn`
- Headless: `n` (watch it work)

**What to watch for:**
- ✅ Searches completing successfully
- ✅ Duplicates being filtered ("Skipped X duplicates")
- ✅ Rate limit detection & auto-recovery (if it happens)
- ✅ Progress percentage climbing

**After test succeeds, run full scrape:**
```bash
python intelligent_knife_scraper.py
```

**Prompts for full run:**
- VPN: `y`
- Headless: `y` (faster, runs in background)

## Documentation

- **START_HERE.md** (this file) - Quick start guide
- **README.md** - Complete documentation with troubleshooting
- **nordvpn_manual_install.md** - VPN setup instructions

## Ready to Start?

```bash
# Step 1: Setup (one time)
python setup_intelligent_scraper.py

# Step 2: Test run (25 searches)
python intelligent_knife_scraper.py 25
  # VPN: y
  # Headless: n

# Step 3: Full run (after test succeeds)
python intelligent_knife_scraper.py
  # VPN: y
  # Headless: y
```

Everything else is automatic. The scraper handles:
- ✅ Rate limits (auto-recovery)
- ✅ Duplicates (auto-filtered)
- ✅ Progress (auto-tracked)
- ✅ VPN rotation (automatic)
- ✅ Search strategy (intelligent)

**Go find those hidden gems!** 💎
