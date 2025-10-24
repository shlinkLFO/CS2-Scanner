"""
CS2 Trade-Up Scanner
Scans Steam Community Market for profitable 5 Covert → 1 Gold trade-ups
"""

import time
import requests
import pandas as pd
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CS2 App ID
APPID = 730
CURRENCY = 1  # USD

# Steam Market fee: ~13% total (5% Steam + ~8% publisher)
STEAM_FEE_PERCENT = 0.13

# Price cache to avoid redundant API calls
price_cache = {}


def get_market_price(item_name: str, use_cache: bool = True) -> Optional[float]:
    """
    Fetch lowest sell order price from Steam Community Market.
    Returns price in USD.
    """
    if use_cache and item_name in price_cache:
        return price_cache[item_name]
    
    try:
        url = f"https://steamcommunity.com/market/priceoverview/"
        params = {
            'appid': APPID,
            'currency': CURRENCY,
            'market_hash_name': item_name
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('success'):
            logger.warning(f"API returned success=false for {item_name}")
            return None
        
        # Parse lowest price (format: "$123.45")
        lowest_price_str = data.get('lowest_price', '')
        if not lowest_price_str:
            logger.warning(f"No lowest_price for {item_name}")
            return None
        
        # Remove currency symbols and parse
        price = float(lowest_price_str.replace('$', '').replace(',', '').strip())
        
        price_cache[item_name] = price
        logger.info(f"Fetched {item_name}: ${price:.2f}")
        
        # Rate limiting: Be very conservative to avoid 429 errors
        time.sleep(6)
        
        return price
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {item_name}: {e}")
        return None
    except (ValueError, KeyError) as e:
        logger.error(f"Parse error for {item_name}: {e}")
        return None


def generate_knife_names(knife_model: str, finishes: List[str]) -> List[str]:
    """Generate full market names for knife skins."""
    return [f"★ {knife_model} | {finish}" for finish in finishes]


def generate_glove_names(glove_model: str, finishes: List[str]) -> List[str]:
    """Generate full market names for glove skins."""
    return [f"★ {glove_model} | {finish}" for finish in finishes]


# Define finish sets
ORIGINAL_FINISHES = [
    "Blue Steel", "Boreal Forest", "Case Hardened", "Crimson Web", 
    "Fade", "Forest DDPAT", "Night", "Safari Mesh", "Scorched", 
    "Slaughter", "Stained", "Urban Masked"
]

CHROMA_FINISHES = [
    "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", 
    "Tiger Tooth", "Ultraviolet"
]

GAMMA_FINISHES = [
    "Autotronic", "Black Laminate", "Bright Water", 
    "Freehand", "Gamma Doppler", "Lore"
]

# Doppler phases (for more detailed analysis if needed)
DOPPLER_PHASES = ["Phase 1", "Phase 2", "Phase 3", "Phase 4", "Ruby", "Sapphire", "Black Pearl", "Emerald"]

GLOVE_SET_1_FINISHES = [
    "Crimson Kimono", "Emerald Web", "Hedge Maze", "Superconductor",
    "Crimson Weave", "Diamondback", "Pandora's Box", "Bronzed",
    "Snakebite", "Convoy", "Lunar Weave", "POW!", "Racing Green",
    "Badlands", "Cool Mint", "Buckshot", "Foundation", "Transport",
    "Overtake", "Imperial Plaid", "Leather", "Slaughter"
]

GLOVE_SET_2_FINISHES = [
    "King Snake", "Vice", "Amphibious", "Fade", "Omega",
    "Emerald", "Mogul", "Arid", "Snow Leopard", "Polygon",
    "Rattler", "Imperial Plaid", "Blood Pressure", "Overtake",
    "Crimson Weave", "Finish Line", "Lunar Weave"
]

GLOVE_SET_3_FINISHES = [
    "Marble Fade", "Tiger Strike", "Snow Leopard", "Nocts",
    "Unhinged", "Needle Point", "Jade", "Yellow-banded",
    "Temukau", "Bronze Morph", "Overprint", "Omega",
    "Desert Shamagh", "Diamondback", "Constrictor", "Emerald"
]


# Define collections with their covert skins and gold outcomes
COLLECTIONS = {
    "CS:GO Weapon Case": {
        "covert_skins": [
            "AWP | Lightning Strike (Minimal Wear)",
            "AWP | Lightning Strike (Field-Tested)",
            "Desert Eagle | Hypnotic (Minimal Wear)",
            "Desert Eagle | Hypnotic (Field-Tested)",
            "Desert Eagle | Hypnotic (Well-Worn)",
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "eSports 2013": {
        "covert_skins": [
            "AK-47 | Fire Serpent (Factory New)",
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Operation Bravo": {
        "covert_skins": [
            "AK-47 | Fire Serpent (Factory New)",
            "Desert Eagle | Golden Koi (Factory New)",
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "CS:GO Weapon Case 2": {
        "covert_skins": [
            "M4A4 | Asiimov (Factory New)",
            "Desert Eagle | Cobalt Disruption (Factory New)",
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "eSports 2013 Winter": {
        "covert_skins": [
            "AWP | Redline (Factory New)",
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Winter Offensive": {
        "covert_skins": [
            "AWP | Redline (Factory New)",
            "M4A4 | Asiimov (Factory New)",
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "CS:GO Weapon Case 3": {
        "covert_skins": [
            "AK-47 | Case Hardened (Factory New)",
            "AWP | Lightning Strike (Factory New)",
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Operation Phoenix": {
        "covert_skins": [
            "AK-47 | Redline (Factory New)",
            "AWP | Asiimov (Factory New)",
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Huntsman Weapon Case": {
        "covert_skins": [
            "M4A1-S | Cyrex (Minimal Wear)",
            "M4A1-S | Cyrex (Field-Tested)",
            "AK-47 | Vulcan (Minimal Wear)",
            "AK-47 | Vulcan (Field-Tested)",
            "AK-47 | Vulcan (Well-Worn)",
        ],
        "gold_models": ["Huntsman Knife"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    # Breakout excluded per user request
    
    "Chroma Case": {
        "covert_skins": [
            "M4A1-S | Hyper Beast (Minimal Wear)",
            "M4A1-S | Hyper Beast (Field-Tested)",
            "AK-47 | Cartel (Minimal Wear)",
            "AK-47 | Cartel (Field-Tested)",
            "AK-47 | Cartel (Well-Worn)",
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": CHROMA_FINISHES
    },
    
    "Chroma 2 Case": {
        "covert_skins": [
            "M4A1-S | Hyper Beast (Minimal Wear)",
            "M4A1-S | Hyper Beast (Field-Tested)",
            "AK-47 | Aquamarine Revenge (Minimal Wear)",
            "AK-47 | Aquamarine Revenge (Field-Tested)",
            "AK-47 | Aquamarine Revenge (Well-Worn)",
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": CHROMA_FINISHES
    },
    
    "Chroma 3 Case": {
        "covert_skins": [
            "M4A1-S | Chantico's Fire (Minimal Wear)",
            "M4A1-S | Chantico's Fire (Field-Tested)",
            "AK-47 | Fuel Injector (Minimal Wear)",
            "AK-47 | Fuel Injector (Field-Tested)",
            "AK-47 | Fuel Injector (Well-Worn)",
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": CHROMA_FINISHES
    },
    
    "Falchion Case": {
        "covert_skins": [
            "AK-47 | Aquamarine Revenge (Minimal Wear)",
            "AK-47 | Aquamarine Revenge (Field-Tested)",
            "AWP | Hyper Beast (Minimal Wear)",
            "AWP | Hyper Beast (Field-Tested)",
            "AWP | Hyper Beast (Well-Worn)",
        ],
        "gold_models": ["Falchion Knife"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Shadow Case": {
        "covert_skins": [
            "M4A1-S | Golden Coil (Minimal Wear)",
            "M4A1-S | Golden Coil (Field-Tested)",
            "AK-47 | Fuel Injector (Minimal Wear)",
            "AK-47 | Fuel Injector (Field-Tested)",
            "AK-47 | Fuel Injector (Well-Worn)",
        ],
        "gold_models": ["Shadow Daggers"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Revolver Case": {
        "covert_skins": [
            "R8 Revolver | Fade (Factory New)",
            "M4A1-S | Hot Rod (Factory New)",
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Operation Wildfire Case": {
        "covert_skins": [
            "M4A1-S | Hot Rod (Factory New)",
            "AWP | Elite Build (Factory New)",
        ],
        "gold_models": ["Bowie Knife"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Gamma Case": {
        "covert_skins": [
            "M4A1-S | Mecha Industries (Factory New)",
            "Glock-18 | Wasteland Rebel (Factory New)",
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": GAMMA_FINISHES
    },
    
    "Gamma 2 Case": {
        "covert_skins": [
            "AK-47 | Neon Revolution (Factory New)",
            "FAMAS | Roll Cage (Factory New)",
        ],
        "gold_models": ["Bayonet", "Flip Knife", "Gut Knife", "Karambit", "M9 Bayonet"],
        "finish_set": GAMMA_FINISHES
    },
    
    "Spectrum Case": {
        "covert_skins": [
            "AK-47 | Bloodsport (Factory New)",
            "USP-S | Neo-Noir (Factory New)",
        ],
        "gold_models": ["Bowie Knife", "Butterfly Knife", "Falchion Knife", "Huntsman Knife", "Shadow Daggers"],
        "finish_set": CHROMA_FINISHES
    },
    
    "Spectrum 2 Case": {
        "covert_skins": [
            "AK-47 | The Empress (Factory New)",
            "M4A1-S | Leaded Glass (Factory New)",
        ],
        "gold_models": ["Bowie Knife", "Butterfly Knife", "Falchion Knife", "Huntsman Knife", "Shadow Daggers"],
        "finish_set": CHROMA_FINISHES
    },
    
    "Horizon Case": {
        "covert_skins": [
            "AK-47 | Neon Rider (Factory New)",
            "AWP | Neo-Noir (Factory New)",
        ],
        "gold_models": ["Navaja Knife", "Stiletto Knife", "Talon Knife", "Ursus Knife"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Danger Zone Case": {
        "covert_skins": [
            "AWP | Neo-Noir (Factory New)",
            "AK-47 | Asiimov (Factory New)",
        ],
        "gold_models": ["Navaja Knife", "Stiletto Knife", "Talon Knife", "Ursus Knife"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Prisma Case": {
        "covert_skins": [
            "M4A4 | The Emperor (Factory New)",
            "AWP | Atheris (Factory New)",
        ],
        "gold_models": ["Navaja Knife", "Stiletto Knife", "Talon Knife", "Ursus Knife"],
        "finish_set": CHROMA_FINISHES
    },
    
    "Prisma 2 Case": {
        "covert_skins": [
            "M4A1-S | Player Two (Factory New)",
            "Glock-18 | Bullet Queen (Factory New)",
        ],
        "gold_models": ["Navaja Knife", "Stiletto Knife", "Talon Knife", "Ursus Knife"],
        "finish_set": CHROMA_FINISHES
    },
    
    "CS20 Case": {
        "covert_skins": [
            "AWP | Wildfire (Factory New)",
            "USP-S | Neo-Noir (Factory New)",
        ],
        "gold_models": ["Classic Knife"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Shattered Web Case": {
        "covert_skins": [
            "AK-47 | Slate (Factory New)",
            "Desert Eagle | Mecha Industries (Factory New)",
        ],
        "gold_models": ["Nomad Knife", "Paracord Knife", "Skeleton Knife", "Survival Knife"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Fracture Case": {
        "covert_skins": [
            "AK-47 | Legion of Anubis (Factory New)",
            "Glock-18 | Vogue (Factory New)",
        ],
        "gold_models": ["Nomad Knife", "Paracord Knife", "Skeleton Knife", "Survival Knife"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Operation Riptide Case": {
        "covert_skins": [
            "AK-47 | Ice Coaled (Factory New)",
            "M4A4 | Eye of Horus (Factory New)",
        ],
        "gold_models": ["Bowie Knife", "Butterfly Knife", "Falchion Knife", "Huntsman Knife", "Shadow Daggers"],
        "finish_set": GAMMA_FINISHES
    },
    
    "Dreams & Nightmares Case": {
        "covert_skins": [
            "AK-47 | Nightwish (Factory New)",
            "MP9 | Starlight Protector (Factory New)",
        ],
        "gold_models": ["Bowie Knife", "Butterfly Knife", "Falchion Knife", "Huntsman Knife", "Shadow Daggers"],
        "finish_set": GAMMA_FINISHES
    },
    
    "Kilowatt Case": {
        "covert_skins": [
            "Zeus x27 | Olympus (Factory New)",
            "USP-S | Whiteout (Factory New)",
        ],
        "gold_models": ["Kukri Knife"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Gallery Case": {
        "covert_skins": [
            "M4A4 | Temukau (Factory New)",
            "AK-47 | Head Shot (Factory New)",
        ],
        "gold_models": ["Kukri Knife"],
        "finish_set": ORIGINAL_FINISHES
    },
    
    "Fever Case": {
        "covert_skins": [
            "AK-47 | Wild Lotus (Factory New)",
            "M4A4 | Poseidon (Factory New)",
        ],
        "gold_models": ["Nomad Knife", "Paracord Knife", "Skeleton Knife", "Survival Knife"],
        "finish_set": CHROMA_FINISHES
    },
    
    # Glove cases
    "Glove Case": {
        "covert_skins": [
            "M4A4 | Buzz Kill (Factory New)",
            "USP-S | Cyrex (Factory New)",
        ],
        "gold_models": ["Bloodhound Gloves", "Driver Gloves", "Hand Wraps", "Moto Gloves", "Specialist Gloves", "Sport Gloves"],
        "finish_set": GLOVE_SET_1_FINISHES,
        "is_gloves": True
    },
    
    "Operation Hydra Case": {
        "covert_skins": [
            "AK-47 | Orbit Mk01 (Factory New)",
            "Five-SeveN | Hyper Beast (Factory New)",
        ],
        "gold_models": ["Bloodhound Gloves", "Driver Gloves", "Hand Wraps", "Moto Gloves", "Specialist Gloves", "Sport Gloves"],
        "finish_set": GLOVE_SET_1_FINISHES,
        "is_gloves": True
    },
    
    "Clutch Case": {
        "covert_skins": [
            "AWP | Mortis (Factory New)",
            "USP-S | Cortex (Factory New)",
        ],
        "gold_models": ["Driver Gloves", "Hand Wraps", "Hydra Gloves", "Moto Gloves", "Specialist Gloves", "Sport Gloves"],
        "finish_set": GLOVE_SET_2_FINISHES,
        "is_gloves": True
    },
    
    "Revolution Case": {
        "covert_skins": [
            "AK-47 | Ice Coaled (Factory New)",
            "P250 | Cyber Shell (Factory New)",
        ],
        "gold_models": ["Driver Gloves", "Hand Wraps", "Hydra Gloves", "Moto Gloves", "Specialist Gloves", "Sport Gloves"],
        "finish_set": GLOVE_SET_2_FINISHES,
        "is_gloves": True
    },
    
    "Operation Broken Fang Case": {
        "covert_skins": [
            "M4A1-S | Printstream (Factory New)",
            "Glock-18 | Neo-Noir (Factory New)",
        ],
        "gold_models": ["Broken Fang Gloves", "Driver Gloves", "Hand Wraps", "Moto Gloves", "Specialist Gloves", "Sport Gloves"],
        "finish_set": GLOVE_SET_3_FINISHES,
        "is_gloves": True
    },
    
    "Snakebite Case": {
        "covert_skins": [
            "AK-47 | Slate (Factory New)",
            "M4A4 | In Living Color (Factory New)",
        ],
        "gold_models": ["Broken Fang Gloves", "Driver Gloves", "Hand Wraps", "Moto Gloves", "Specialist Gloves", "Sport Gloves"],
        "finish_set": GLOVE_SET_3_FINISHES,
        "is_gloves": True
    },
    
    "Recoil Case": {
        "covert_skins": [
            "AK-47 | Ice Coaled (Factory New)",
            "AWP | Chromatic Aberration (Factory New)",
        ],
        "gold_models": ["Broken Fang Gloves", "Driver Gloves", "Hand Wraps", "Moto Gloves", "Specialist Gloves", "Sport Gloves"],
        "finish_set": GLOVE_SET_3_FINISHES,
        "is_gloves": True
    },
}


def evaluate_collection(collection_name: str, collection_info: Dict) -> Optional[Dict]:
    """
    Evaluate a single collection for trade-up profitability.
    Returns best opportunity or None if not profitable.
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Evaluating: {collection_name}")
    logger.info(f"{'='*80}")
    
    # Fetch covert prices
    covert_prices = []
    for skin in collection_info["covert_skins"]:
        price = get_market_price(skin)
        if price is None:
            logger.warning(f"Could not fetch price for {skin}, skipping collection")
            return None
        covert_prices.append((skin, price))
    
    if len(covert_prices) < 1:
        logger.warning(f"No covert skins found")
        return None
    
    # Find the single cheapest covert
    covert_prices.sort(key=lambda x: x[1])
    cheapest_covert = covert_prices[0]
    selected_skin, covert_price = cheapest_covert
    cost_of_5_coverts = covert_price * 5
    
    logger.info(f"Cheapest Covert: {selected_skin} @ ${covert_price:.2f}")
    logger.info(f"Cost of 5x: ${cost_of_5_coverts:.2f}")
    
    # Generate all possible gold items
    is_gloves = collection_info.get("is_gloves", False)
    gold_items = []
    
    if is_gloves:
        for model in collection_info["gold_models"]:
            for finish in collection_info["finish_set"]:
                gold_items.append(f"★ {model} | {finish}")
    else:
        for model in collection_info["gold_models"]:
            for finish in collection_info["finish_set"]:
                gold_items.append(f"★ {model} | {finish}")
    
    # Find cheapest gold item
    cheapest_gold = None
    cheapest_gold_price = float('inf')
    
    logger.info(f"\nChecking {len(gold_items)} possible gold outcomes...")
    
    for gold_item in gold_items:
        price = get_market_price(gold_item)
        if price and price < cheapest_gold_price:
            cheapest_gold = gold_item
            cheapest_gold_price = price
    
    if not cheapest_gold:
        logger.warning("Could not find any gold item prices")
        return None
    
    logger.info(f"\nCheapest Gold: {cheapest_gold} @ ${cheapest_gold_price:.2f}")
    
    # Calculate profit
    # Account for Steam fee when selling the gold
    gold_value_after_fee = cheapest_gold_price * (1 - STEAM_FEE_PERCENT)
    raw_profit = gold_value_after_fee - cost_of_5_coverts
    profit_margin = (raw_profit / cost_of_5_coverts * 100) if cost_of_5_coverts > 0 else 0
    
    # Calculate price ratio and profitability
    price_ratio = cheapest_gold_price / covert_price if covert_price > 0 else 0
    
    logger.info(f"\nAnalysis:")
    logger.info(f"  Covert: ${covert_price:.2f}")
    logger.info(f"  Gold: ${cheapest_gold_price:.2f}")
    logger.info(f"  Ratio: {price_ratio:.2f}x (gold/covert)")
    logger.info(f"  Cost of 5 Coverts: ${cost_of_5_coverts:.2f}")
    logger.info(f"  Gold After 13% Fee: ${gold_value_after_fee:.2f}")
    logger.info(f"  Net Profit: ${raw_profit:.2f} ({profit_margin:.1f}%)")
    
    return {
        "collection": collection_name,
        "covert_skin": selected_skin,
        "covert_price": covert_price,
        "cheapest_gold": cheapest_gold,
        "gold_price": cheapest_gold_price,
        "price_ratio": price_ratio,
        "cost_5x_covert": cost_of_5_coverts,
        "gold_after_fee": gold_value_after_fee,
        "net_profit": raw_profit,
        "profit_margin_pct": profit_margin,
        "is_profitable": raw_profit > 0
    }


def run_full_scan(min_profit: float = 5.0, top_n: int = 10) -> pd.DataFrame:
    """
    Run full scan of all collections.
    Returns DataFrame of profitable opportunities sorted by profit.
    """
    logger.info(f"\n{'#'*80}")
    logger.info(f"Starting Full Market Scan - {datetime.now()}")
    logger.info(f"Analyzing {len(COLLECTIONS)} collections")
    logger.info(f"Minimum Profit Threshold: ${min_profit:.2f}")
    logger.info(f"{'#'*80}\n")
    
    results = []
    
    for collection_name, collection_info in COLLECTIONS.items():
        try:
            result = evaluate_collection(collection_name, collection_info)
            if result:
                results.append(result)
        except Exception as e:
            logger.error(f"Error evaluating {collection_name}: {e}")
            continue
    
    if not results:
        logger.warning("No results found!")
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    
    # Filter profitable only
    df_profitable = df[df["net_profit"] >= min_profit].copy()
    
    # Sort by profit
    df_profitable = df_profitable.sort_values("net_profit", ascending=False)
    
    # Format output
    df_output = df_profitable.head(top_n)[[
        "collection", "covert_price", "gold_price", "price_ratio",
        "cost_5x_covert", "gold_after_fee", "net_profit", "profit_margin_pct"
    ]].copy()
    
    return df_output


def save_results(df: pd.DataFrame, filename: str = "tradeup_opportunities.csv"):
    """Save results to CSV file."""
    df.to_csv(filename, index=False)
    logger.info(f"\nResults saved to {filename}")


def print_summary(df: pd.DataFrame):
    """Print formatted summary of opportunities."""
    if df.empty:
        print("\n" + "="*80)
        print("NO PROFITABLE OPPORTUNITIES FOUND")
        print("="*80)
        return
    
    print("\n" + "="*80)
    print(f"TOP {len(df)} PROFITABLE TRADE-UP OPPORTUNITIES")
    print("="*80)
    print()
    
    for idx, row in df.iterrows():
        print(f"{idx + 1}. {row['collection']}")
        print(f"   Covert: ${row['covert_price']:.2f} | Gold: ${row['gold_price']:.2f} | Ratio: {row['price_ratio']:.2f}x")
        print(f"   Buy 5x Covert: ${row['cost_5x_covert']:.2f} → Sell Gold: ${row['gold_after_fee']:.2f} (after 13% fee)")
        print(f"   NET PROFIT: ${row['net_profit']:.2f} ({row['profit_margin_pct']:.1f}%)")
        print()


if __name__ == "__main__":
    # Run scan
    results_df = run_full_scan(min_profit=5.0, top_n=15)
    
    # Print summary
    print_summary(results_df)
    
    # Save to file
    if not results_df.empty:
        save_results(results_df)
        
        # Also save full results with covert details
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_df.to_json(f"tradeup_detailed_{timestamp}.json", orient="records", indent=2)
    
    print("\n" + "="*80)
    print("SCAN COMPLETE")
    print("="*80)

