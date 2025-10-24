"""
Setup script for the Intelligent Knife Scraper
Generates the comprehensive knife checklist
"""

from comprehensive_knife_list import save_comprehensive_list, get_completion_stats

print("\n" + "="*80)
print("INTELLIGENT KNIFE SCRAPER - SETUP")
print("="*80)
print("\nGenerating comprehensive knife database checklist...")
print("This will create a checklist of EVERY possible knife combination in CS2")
print("="*80 + "\n")

# Generate checklist
knives = save_comprehensive_list("comprehensive_knife_checklist")

# Show stats
stats = get_completion_stats(knives)

print("\n" + "="*80)
print("SETUP COMPLETE")
print("="*80)
print(f"Total knife combinations: {stats['total_combinations']}")
print(f"  - {stats['total_combinations'] // 2} regular knives")
print(f"  - {stats['total_combinations'] // 2} StatTrak knives")
print("\nBreakdown by knife type:")
for knife_type, data in sorted(stats['by_type'].items()):
    print(f"  {knife_type}: {data['total']} combinations")

print("\n" + "="*80)
print("Next step: Run intelligent_knife_scraper.py to begin scraping")
print("  python intelligent_knife_scraper.py")
print("="*80 + "\n")

