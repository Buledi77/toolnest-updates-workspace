#!/usr/bin/env python3
"""
Add honest pricing status markers to the 102 tools without verified pricing data.
This ensures cards and pages don't show blank or misleading pricing information.
"""
import json
import os

# Well-known tools with known pricing models (from general knowledge)
# For tools we can't verify, we use honest fallbacks
KNOWN_PRICING = {
    # Freemium tools (known to have free tier)
    "activecampaign": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "adcreative": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "adwisely": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "amplitude": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "apollo": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "beautifulai": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "bill": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "brand24": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "breadbutter": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "browseai": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "capsule": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "circle": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "close": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "cloudflare": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "convertkit": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "copper": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "crisp": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "dialpad": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "dimdim": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "dovetail": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "drift": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "elasticemail": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "flair": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "flocksy": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "gemini": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "gleap": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "gumroad": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "hubspot": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "hunter": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "imagekit": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "instatus": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "jotform": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "klaviyo": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "lemonsqueezy": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "linear": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "mailchimp": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "mailerlite": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "memberstack": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "midjourney": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "mixpanel": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "moosend": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "noteable": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "notion": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "omniseo": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "pageclip": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "pipedrive": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "posthog": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "privacy": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "productboard": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "pictory": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "puzzle": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "qualaroo": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "rankmath": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "refiner": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "resend": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "retell": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "ringcentral": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "riverside": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "salesforce": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "salesforce-smb": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "segment": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "sentry": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "shipfast": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "shortcut": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "solarstone": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "stamped": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "storylane": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "streak": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "surveymonkey": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "systeme": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "teachable": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "tally": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "teamviewer": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "transpond": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "typeform": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "upfluence": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "userpilot": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "vimeo": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "windsorai": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "wingify": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "wordpress": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "writefull": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "xoi": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "zendesk": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "zoho": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "systeme": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "leonardo": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "logome": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "hightouch": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "notebooklm": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "bolt": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "cursor": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "github-copilot": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "lovable": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "ideogram": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "heygen": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "surferseo": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "screamingfrog": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "zapier": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "webflow": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "monday": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "clickup": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "asana": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "canva": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "hostinger": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "grammarly": {"pricing_status": "Freemium (details not verified)", "freePlan": True},
    "ahrefs": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "semrush": {"pricing_status": "Paid (details not verified)", "freePlan": False},
    "mozpro": {"pricing_status": "Paid (details not verified)", "freePlan": False},
}

def update_tool_with_fallback(slug, name):
    path = f"data/tools/{slug}.json"
    if not os.path.exists(path):
        return False
    
    with open(path) as f:
        tool = json.load(f)
    
    # Skip if already has pricing plans
    if tool.get("pricing", {}).get("plans"):
        return False
    
    info = KNOWN_PRICING.get(slug, {})
    pricing_status = info.get("pricing_status", "Pricing Not Publicly Listed")
    free_plan = info.get("freePlan")
    
    # Update factual_profile
    fp = tool.setdefault("factual_profile", {})
    fp["pricing_status"] = pricing_status
    if free_plan is not None:
        fp["free_plan_status"] = "Free plan available (details not verified)" if free_plan else "No free plan (details not verified)"
    
    # Add minimal pricing section with honest status
    tool["pricing"] = {
        "checkedOn": None,
        "pricing_status": pricing_status,
        "freePlan": free_plan,
        "plans": [],
        "notes": "Pricing not yet verified by ToolNest research. Check the official site for current pricing."
    }
    
    # Update freshness
    fresh = tool.setdefault("freshness", {})
    fresh["updated_at"] = "2026-11-23T20:00:00Z"
    
    with open(path, "w") as f:
        json.dump(tool, f, indent=2)
        f.write("\n")
    
    return True

if __name__ == "__main__":
    d = "data/tools"
    count = 0
    skipped = 0
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json"):
            continue
        slug = f.replace(".json", "")
        t = json.load(open(os.path.join(d, f)))
        if t.get("pricing", {}).get("plans"):
            skipped += 1
            continue
        name = t.get("identity", {}).get("name", slug)
        if update_tool_with_fallback(slug, name):
            count += 1
            print(f"  OK: {slug} ({name})")
    
    print(f"\nDone: {count} tools updated, {skipped} already had pricing.")
