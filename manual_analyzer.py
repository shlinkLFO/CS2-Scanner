"""
CS2 Trade-Up Manual Analyzer
For when you have specific covert and gold prices to analyze
"""

import pandas as pd
from typing import List, Dict

# Steam Market fee: ~13% total
STEAM_FEE_PERCENT = 0.13


def analyze_tradeup(covert_price: float, gold_price: float, collection_name: str = "") -> Dict:
    """
    Analyze a single trade-up opportunity.
    
    Args:
        covert_price: Price of the cheapest covert skin
        gold_price: Price of the cheapest gold (knife/glove) outcome
        collection_name: Name of the collection (optional)
    
    Returns:
        Dictionary with analysis results
    """
    cost_5x_covert = covert_price * 5
    gold_after_fee = gold_price * (1 - STEAM_FEE_PERCENT)
    net_profit = gold_after_fee - cost_5x_covert
    profit_margin = (net_profit / cost_5x_covert * 100) if cost_5x_covert > 0 else 0
    price_ratio = gold_price / covert_price if covert_price > 0 else 0
    
    return {
        "collection": collection_name,
        "covert_price": covert_price,
        "gold_price": gold_price,
        "price_ratio": price_ratio,
        "cost_5x_covert": cost_5x_covert,
        "gold_after_fee": gold_after_fee,
        "net_profit": net_profit,
        "profit_margin_pct": profit_margin,
        "is_profitable": net_profit > 0
    }


def batch_analyze(opportunities: List[Dict]) -> pd.DataFrame:
    """
    Analyze multiple trade-up opportunities.
    
    Args:
        opportunities: List of dicts with keys: 'collection', 'covert_price', 'gold_price'
    
    Returns:
        DataFrame sorted by profitability
    """
    results = []
    
    for opp in opportunities:
        result = analyze_tradeup(
            covert_price=opp['covert_price'],
            gold_price=opp['gold_price'],
            collection_name=opp.get('collection', 'Unknown')
        )
        results.append(result)
    
    df = pd.DataFrame(results)
    df = df.sort_values('net_profit', ascending=False)
    
    return df


def print_analysis(df: pd.DataFrame):
    """Print formatted analysis results."""
    print("\n" + "="*90)
    print("CS2 TRADE-UP ANALYSIS (5 Covert → 1 Gold)")
    print("="*90)
    print()
    
    for idx, row in df.iterrows():
        status = "✓ PROFITABLE" if row['is_profitable'] else "✗ NOT PROFITABLE"
        print(f"{row['collection']}")
        print(f"  Covert: ${row['covert_price']:.2f} | Gold: ${row['gold_price']:.2f} | Ratio: {row['price_ratio']:.2f}x")
        print(f"  Buy 5x Covert: ${row['cost_5x_covert']:.2f}")
        print(f"  Sell Gold (after 13% fee): ${row['gold_after_fee']:.2f}")
        print(f"  Net Profit: ${row['net_profit']:.2f} ({row['profit_margin_pct']:.1f}%) {status}")
        print()


# Example usage with manual price data
if __name__ == "__main__":
    
    # Enter your price data here
    # Format: {'collection': 'Name', 'covert_price': X.XX, 'gold_price': Y.YY}
    
    opportunities = [
        # Example collections - replace with actual Steam Market prices
        {
            'collection': 'Huntsman Weapon Case',
            'covert_price': 50.00,  # Cheapest covert in MW/FT
            'gold_price': 300.00     # Cheapest Huntsman knife (any finish)
        },
        {
            'collection': 'Chroma Case',
            'covert_price': 40.00,
            'gold_price': 250.00
        },
        {
            'collection': 'Shadow Case',
            'covert_price': 60.00,
            'gold_price': 150.00     # Shadow Daggers are cheaper
        },
        {
            'collection': 'Spectrum Case',
            'covert_price': 35.00,
            'gold_price': 280.00
        },
        # Add more collections here...
    ]
    
    # Analyze all opportunities
    results_df = batch_analyze(opportunities)
    
    # Print results
    print_analysis(results_df)
    
    # Save to CSV
    results_df.to_csv('tradeup_manual_analysis.csv', index=False)
    print("="*90)
    print("Results saved to tradeup_manual_analysis.csv")
    print("="*90)
    
    # Quick summary
    profitable = results_df[results_df['is_profitable']]
    print(f"\nSummary: {len(profitable)}/{len(results_df)} opportunities are profitable")
    
    if len(profitable) > 0:
        best = profitable.iloc[0]
        print(f"Best opportunity: {best['collection']} (${best['net_profit']:.2f} profit, {best['profit_margin_pct']:.1f}%)")

