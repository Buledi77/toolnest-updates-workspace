#!/usr/bin/env python3
"""
Update data/tools.json lightweight catalog with pricing data from data/tools/{slug}.json files.
This surfaces pricing on cards rendered from the lightweight catalog.
"""
import json
import os

def get_starting_price(pricing):
    """Extract the lowest starting price from pricing data."""
    plans = pricing.get("plans", [])
    if not plans:
        return None
    # Find the lowest non-zero price
    prices = []
    for p in plans:
        pm = p.get("priceMonthly")
        if pm is not None and pm > 0:
            prices.append(pm)
        elif pm == 0:
            return "Free"
    if prices:
        lowest = min(prices)
        if lowest >= 1000:
            return f"${lowest}/mo"
        return f"${lowest}/mo"
    return None

def update_catalog():
    catalog_path = "data/tools.json"
    with open(catalog_path) as f:
        data = json.load(f)
    
    tools = data.get("tools", [])
    updated = 0
    
    for tool in tools:
        slug = tool.get("id") or tool.get("slug", "")
        detail_path = f"data/tools/{slug}.json"
        
        if not os.path.exists(detail_path):
            continue
        
        with open(detail_path) as f:
            detail = json.load(f)
        
        pricing = detail.get("pricing", {})
        if not pricing.get("plans"):
            continue
        
        # Add pricing fields to catalog entry
        starting = get_starting_price(pricing)
        if starting:
            tool["startingPrice"] = starting
        
        if pricing.get("freePlan"):
            tool["freePlan"] = True
        
        if pricing.get("checkedOn"):
            tool["checkedOn"] = pricing["checkedOn"]
        
        # Add pricing status from factual_profile
        fp = detail.get("factual_profile", {})
        ps = fp.get("pricing_status")
        if ps:
            tool["pricingStatus"] = ps
        
        updated += 1
    
    with open(catalog_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    
    print(f"Updated {updated} tools in catalog with pricing data.")

if __name__ == "__main__":
    update_catalog()
