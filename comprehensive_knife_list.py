"""
Comprehensive CS2 Knife Database - ACCURATE
Every knife type × finish × wear × StatTrak combination
Based on actual CS2 knife availability
"""

import json
import csv
from typing import List, Dict

# All CS2 knife types (20 total - includes Kukri added in CS2)
KNIFE_TYPES = [
    "Bayonet",
    "Bowie Knife",
    "Butterfly Knife",
    "Classic Knife",
    "Falchion Knife",
    "Flip Knife",
    "Gut Knife",
    "Huntsman Knife",
    "Karambit",
    "Kukri Knife",  # Added in CS2
    "M9 Bayonet",
    "Navaja Knife",
    "Nomad Knife",
    "Paracord Knife",
    "Shadow Daggers",
    "Skeleton Knife",
    "Stiletto Knife",
    "Survival Knife",
    "Talon Knife",
    "Ursus Knife"
]

# All finishes with their ACTUAL available wear levels (from float ranges)
FINISH_WEARS = {
    # Original Set (CS:GO Release) - Full wear range
    "Blue Steel": ["FN", "MW", "FT", "WW", "BS"],
    "Boreal Forest": ["FN", "MW", "FT", "WW", "BS"],
    "Case Hardened": ["FN", "MW", "FT", "WW", "BS"],
    "Crimson Web": ["FN", "MW", "FT", "WW", "BS"],
    "Forest DDPAT": ["FN", "MW", "FT", "WW", "BS"],
    "Night": ["FN", "MW", "FT", "WW", "BS"],
    "Safari Mesh": ["FN", "MW", "FT", "WW", "BS"],
    "Scorched": ["FN", "MW", "FT", "WW", "BS"],
    "Stained": ["FN", "MW", "FT", "WW", "BS"],
    "Urban Masked": ["FN", "MW", "FT", "WW", "BS"],
    
    # Arms Deal - Full wear range
    "Fade": ["FN", "MW"],  # 0.00-0.08 (FN/MW only)
    "Slaughter": ["FN", "MW", "FT"],  # 0.01-0.26 (no WW/BS)
    "Ultraviolet": ["FN", "MW", "FT", "WW", "BS"],
    
    # Chroma - Restricted wears
    "Damascus Steel": ["FN", "MW", "FT", "WW", "BS"],
    "Doppler": ["FN", "MW"],  # 0.00-0.08 (FN/MW only)
    "Marble Fade": ["FN", "MW"],  # 0.00-0.08 (FN/MW only)
    "Rust Coat": ["WW", "BS"],  # 0.40-1.00 (WW/BS only)
    "Tiger Tooth": ["FN", "MW"],  # 0.00-0.08 (FN/MW only)
    
    # Gamma - Mixed wears
    "Autotronic": ["FN", "MW", "FT", "WW", "BS"],
    "Black Laminate": ["FN", "MW", "FT", "WW", "BS"],
    "Bright Water": ["FN", "MW", "FT", "WW", "BS"],
    "Freehand": ["FN", "MW", "FT", "WW", "BS"],
    "Gamma Doppler": ["FN", "MW"],  # 0.00-0.08 (FN/MW only)
    "Lore": ["FN", "MW", "FT", "WW", "BS"],
}

# Knife-specific finish availability (not all knives have all finishes)
# Based on collection/case availability
KNIFE_FINISH_AVAILABILITY = {
    # Original knives (have "original" finishes)
    "Bayonet": [
        "Blue Steel", "Boreal Forest", "Case Hardened", "Crimson Web", "Fade",
        "Forest DDPAT", "Night", "Safari Mesh", "Scorched", "Slaughter", 
        "Stained", "Urban Masked", "Ultraviolet",
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth",
        "Autotronic", "Black Laminate", "Bright Water", "Freehand", "Gamma Doppler", "Lore"
    ],
    "Flip Knife": [
        "Blue Steel", "Boreal Forest", "Case Hardened", "Crimson Web", "Fade",
        "Forest DDPAT", "Night", "Safari Mesh", "Scorched", "Slaughter",
        "Stained", "Urban Masked", "Ultraviolet",
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth",
        "Autotronic", "Black Laminate", "Bright Water", "Freehand", "Gamma Doppler", "Lore"
    ],
    "Gut Knife": [
        "Blue Steel", "Boreal Forest", "Case Hardened", "Crimson Web", "Fade",
        "Forest DDPAT", "Night", "Safari Mesh", "Scorched", "Slaughter",
        "Stained", "Urban Masked", "Ultraviolet",
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth",
        "Autotronic", "Black Laminate", "Bright Water", "Freehand", "Gamma Doppler", "Lore"
    ],
    "Karambit": [
        "Blue Steel", "Boreal Forest", "Case Hardened", "Crimson Web", "Fade",
        "Forest DDPAT", "Night", "Safari Mesh", "Scorched", "Slaughter",
        "Stained", "Urban Masked", "Ultraviolet",
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth",
        "Autotronic", "Black Laminate", "Bright Water", "Freehand", "Gamma Doppler", "Lore"
    ],
    "M9 Bayonet": [
        "Blue Steel", "Boreal Forest", "Case Hardened", "Crimson Web", "Fade",
        "Forest DDPAT", "Night", "Safari Mesh", "Scorched", "Slaughter",
        "Stained", "Urban Masked", "Ultraviolet",
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth",
        "Autotronic", "Black Laminate", "Bright Water", "Freehand", "Gamma Doppler", "Lore"
    ],
    
    # Huntsman (Arms Deal 2)
    "Huntsman Knife": [
        "Blue Steel", "Boreal Forest", "Case Hardened", "Crimson Web", "Fade",
        "Forest DDPAT", "Night", "Safari Mesh", "Scorched", "Slaughter",
        "Stained", "Urban Masked", "Ultraviolet",
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth",
        "Autotronic", "Black Laminate", "Bright Water", "Freehand", "Gamma Doppler", "Lore"
    ],
    
    # Butterfly (Breakout)
    "Butterfly Knife": [
        "Blue Steel", "Boreal Forest", "Case Hardened", "Crimson Web", "Fade",
        "Forest DDPAT", "Night", "Safari Mesh", "Scorched", "Slaughter",
        "Stained", "Urban Masked", "Ultraviolet",
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth",
        "Autotronic", "Black Laminate", "Bright Water", "Freehand", "Gamma Doppler", "Lore"
    ],
    
    # Falchion (Falchion)
    "Falchion Knife": [
        "Blue Steel", "Boreal Forest", "Case Hardened", "Crimson Web", "Fade",
        "Forest DDPAT", "Night", "Safari Mesh", "Scorched", "Slaughter",
        "Stained", "Urban Masked", "Ultraviolet",
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth",
        "Autotronic", "Black Laminate", "Bright Water", "Freehand", "Gamma Doppler", "Lore"
    ],
    
    # Shadow Daggers (Shadow)
    "Shadow Daggers": [
        "Blue Steel", "Boreal Forest", "Case Hardened", "Crimson Web", "Fade",
        "Forest DDPAT", "Night", "Safari Mesh", "Scorched", "Slaughter",
        "Stained", "Urban Masked", "Ultraviolet",
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth",
        "Autotronic", "Black Laminate", "Bright Water", "Freehand", "Gamma Doppler", "Lore"
    ],
    
    # Bowie (Revolver)
    "Bowie Knife": [
        "Blue Steel", "Boreal Forest", "Case Hardened", "Crimson Web", "Fade",
        "Forest DDPAT", "Night", "Safari Mesh", "Scorched", "Slaughter",
        "Stained", "Urban Masked", "Ultraviolet",
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth",
        "Autotronic", "Black Laminate", "Bright Water", "Freehand", "Gamma Doppler", "Lore"
    ],
    
    # Chroma 3+ knives (Chroma/Prisma pool - no "original" finishes)
    "Stiletto Knife": [
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth",
        "Autotronic", "Black Laminate", "Bright Water", "Freehand", "Gamma Doppler", "Lore"
    ],
    "Talon Knife": [
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth",
        "Autotronic", "Black Laminate", "Bright Water", "Freehand", "Gamma Doppler", "Lore"
    ],
    "Ursus Knife": [
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth",
        "Autotronic", "Black Laminate", "Bright Water", "Freehand", "Gamma Doppler", "Lore"
    ],
    "Navaja Knife": [
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth",
        "Autotronic", "Black Laminate", "Bright Water", "Freehand", "Gamma Doppler", "Lore"
    ],
    
    # Horizon knives (subset)
    "Classic Knife": [
        "Blue Steel", "Boreal Forest", "Case Hardened", "Crimson Web", "Fade",
        "Forest DDPAT", "Night", "Safari Mesh", "Scorched", "Slaughter",
        "Stained", "Urban Masked", "Ultraviolet"
    ],
    
    # Shattered Web knives
    "Nomad Knife": [
        "Blue Steel", "Case Hardened", "Crimson Web", "Fade", "Forest DDPAT",
        "Night", "Safari Mesh", "Scorched", "Slaughter", "Stained", "Urban Masked"
    ],
    "Skeleton Knife": [
        "Blue Steel", "Case Hardened", "Crimson Web", "Fade", "Forest DDPAT",
        "Night", "Safari Mesh", "Scorched", "Slaughter", "Stained", "Urban Masked"
    ],
    "Survival Knife": [
        "Blue Steel", "Case Hardened", "Crimson Web", "Fade", "Forest DDPAT",
        "Night", "Safari Mesh", "Scorched", "Slaughter", "Stained", "Urban Masked",
        "Damascus Steel", "Doppler", "Marble Fade", "Rust Coat", "Tiger Tooth"
    ],
    "Paracord Knife": [
        "Blue Steel", "Case Hardened", "Crimson Web", "Fade", "Forest DDPAT",
        "Night", "Safari Mesh", "Scorched", "Slaughter", "Stained", "Urban Masked"
    ],
    
    # CS2 Kukri Knife (Kilowatt/Gallery)
    "Kukri Knife": [
        "Blue Steel", "Case Hardened", "Crimson Web", "Fade", "Forest DDPAT",
        "Night", "Safari Mesh", "Scorched", "Slaughter", "Stained", "Urban Masked"
    ],
}


def generate_comprehensive_knife_list() -> List[Dict]:
    """
    Generate ACCURATE list of all possible knife combinations
    Based on actual CS2 knife availability
    """
    all_knives = []
    
    for knife_type in KNIFE_TYPES:
        # Get finishes available for this knife
        available_finishes = KNIFE_FINISH_AVAILABILITY.get(knife_type, [])
        
        for finish in available_finishes:
            # Get wears available for this finish
            available_wears = FINISH_WEARS.get(finish, [])
            
            for wear in available_wears:
                # Regular version
                all_knives.append({
                    "knife_type": knife_type,
                    "finish": finish,
                    "wear": wear,
                    "is_stattrak": 0,
                    "found": 0,
                    "quantity": None,
                    "price": None,
                    "last_updated": None
                })
                
                # StatTrak version (all CS2 knives can be StatTrak)
                all_knives.append({
                    "knife_type": knife_type,
                    "finish": finish,
                    "wear": wear,
                    "is_stattrak": 1,
                    "found": 0,
                    "quantity": None,
                    "price": None,
                    "last_updated": None
                })
    
    return all_knives


def save_comprehensive_list(filename: str = "comprehensive_knife_checklist"):
    """Save comprehensive knife list to CSV and JSON"""
    knives = generate_comprehensive_knife_list()
    
    # CSV
    csv_file = f"{filename}.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["knife_type", "finish", "wear", "is_stattrak", "found", 
                     "quantity", "price", "last_updated"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(knives)
    
    print(f"Saved comprehensive checklist: {csv_file}")
    print(f"  Total knife combinations: {len(knives)}")
    print(f"  Unique knives (no StatTrak): {len(knives) // 2}")
    
    # Breakdown by knife type
    by_type = {}
    for knife in knives:
        ktype = knife['knife_type']
        by_type[ktype] = by_type.get(ktype, 0) + 1
    
    print("\nBreakdown by knife type:")
    for knife_type in sorted(by_type.keys()):
        print(f"  {knife_type}: {by_type[knife_type]} combinations")
    
    # JSON
    json_file = f"{filename}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(knives, f, indent=2)
    
    print(f"\nSaved JSON: {json_file}")
    
    return knives


def load_checklist(filename: str = "comprehensive_knife_checklist.csv") -> List[Dict]:
    """Load the comprehensive knife checklist"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            knives = list(reader)
            
            # Convert types
            for knife in knives:
                knife['is_stattrak'] = int(knife['is_stattrak'])
                knife['found'] = int(knife['found'])
                if knife['quantity'] and knife['quantity'] != '':
                    knife['quantity'] = int(knife['quantity'])
                if knife['price'] and knife['price'] != '':
                    knife['price'] = float(knife['price'])
            
            return knives
    except FileNotFoundError:
        print(f"Checklist not found, generating new one...")
        save_comprehensive_list()
        return load_checklist(filename)


def get_unfound_knives(checklist: List[Dict]) -> List[Dict]:
    """Get list of knives not yet found (found=0)"""
    return [k for k in checklist if k['found'] == 0]


def mark_knife_found(checklist: List[Dict], knife_type: str, finish: str, 
                    wear: str, is_stattrak: int, quantity: int, price: float) -> bool:
    """
    Mark a knife as found in the checklist
    Returns True if found and updated, False if not in checklist
    """
    from datetime import datetime
    
    for knife in checklist:
        if (knife['knife_type'] == knife_type and
            knife['finish'] == finish and
            knife['wear'] == wear and
            knife['is_stattrak'] == is_stattrak):
            
            knife['found'] = 1
            knife['quantity'] = quantity
            knife['price'] = price
            knife['last_updated'] = datetime.now().isoformat()
            return True
    
    return False


def save_updated_checklist(checklist: List[Dict], filename: str = "comprehensive_knife_checklist.csv"):
    """Save updated checklist back to file"""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["knife_type", "finish", "wear", "is_stattrak", "found", 
                     "quantity", "price", "last_updated"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(checklist)


def get_completion_stats(checklist: List[Dict]) -> Dict:
    """Get statistics on completion"""
    total = len(checklist)
    found = sum(1 for k in checklist if k['found'] == 1)
    not_found = total - found
    
    # By knife type
    by_type = {}
    for knife in checklist:
        ktype = knife['knife_type']
        if ktype not in by_type:
            by_type[ktype] = {"total": 0, "found": 0}
        by_type[ktype]["total"] += 1
        if knife['found'] == 1:
            by_type[ktype]["found"] += 1
    
    return {
        "total_combinations": total,
        "found": found,
        "not_found": not_found,
        "completion_percent": (found / total * 100) if total > 0 else 0,
        "by_type": by_type
    }


if __name__ == "__main__":
    print("\n" + "="*80)
    print("CS2 COMPREHENSIVE KNIFE DATABASE GENERATOR - ACCURATE")
    print("="*80)
    print("Based on actual CS2 knife collections and finish availability")
    print("="*80 + "\n")
    
    knives = save_comprehensive_list()
    
    stats = get_completion_stats(knives)
    print(f"\nTotal knife combinations: {stats['total_combinations']}")
    print(f"  Regular knives: {stats['total_combinations'] // 2}")
    print(f"  StatTrak knives: {stats['total_combinations'] // 2}")
    print(f"\nFound: {stats['found']}")
    print(f"Not found: {stats['not_found']}")
    print(f"Completion: {stats['completion_percent']:.1f}%")
    
    print("\n" + "="*80)
    print("ACCURACY NOTES:")
    print("="*80)
    print("- 20 knife types (includes Kukri added in CS2)")
    print("- Finish availability varies by knife type")
    print("- Wear levels based on actual float ranges:")
    print("  - Doppler/Marble/Tiger/Gamma/Fade: FN/MW only (0.00-0.08)")
    print("  - Rust Coat: WW/BS only (0.40-1.00)")
    print("  - Slaughter: FN/MW/FT only (0.01-0.26)")
    print("  - Most others: All 5 wears")
    print("- Phase variants (Doppler) counted as single market listing")
    print("="*80 + "\n")
