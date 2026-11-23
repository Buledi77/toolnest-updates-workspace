#!/usr/bin/env python3
"""Base extractor module — normalized field extraction from source content.

Provides the foundation for per-tool and per-pattern extractors.
Pricing extraction preserves:
- currency, plan, amount, billing_interval, billing_basis
- per_user/seat/workspace, usage_based, annual_commitment
- monthly_billing, annual-billing_monthly_equivalent
- custom/contact_sales

Rules:
- NEVER normalize: unknown → zero, unknown → free, trial → free plan
- NEVER normalize: annual equivalent → monthly billing
- Capabilities only mapped when evidence supports the interpretation

Usage:
    from scripts.extractors.base import BaseExtractor, PricingExtractor
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseExtractor(ABC):
    """Base class for source content extractors."""
    
    def __init__(self, tool_id: str, extractor_name: str):
        self.tool_id = tool_id
        self.extractor_name = extractor_name
    
    @abstractmethod
    def extract(self, text_content: str, url: str) -> dict:
        """Extract structured fields from source content.
        
        Args:
            text_content: Cleaned text content from the source
            url: Source URL for context
        
        Returns:
            Dict of extracted fields
        """
        pass
    
    def validate(self, extracted: dict) -> List[str]:
        """Validate extracted fields for common errors.
        
        Returns:
            List of validation warnings (empty if valid)
        """
        warnings = []
        
        # Check for empty pricing
        pricing = extracted.get("pricing", {})
        if pricing and pricing.get("tiers"):
            for tier in pricing["tiers"]:
                if tier.get("amount") == 0 and tier.get("plan", "").lower() not in ("free", "starter"):
                    warnings.append(f"Zero amount for plan '{tier.get('plan')}' — verify this is not 'unknown'")
        
        return warnings


class PricingExtractor(BaseExtractor):
    """Generic pricing page extractor.
    
    Extracts pricing information from text content using pattern matching.
    This is a generic extractor — per-tool extractors should override for
    more accurate parsing of specific page structures.
    """
    
    CURRENCY_PATTERNS = {
        "USD": [r'\$', r'USD', r'US Dollar'],
        "EUR": [r'€', r'EUR', r'Euro'],
        "GBP": [r'£', r'GBP', r'Pound'],
    }
    
    def __init__(self, tool_id: str):
        super().__init__(tool_id, f"{tool_id}_pricing_v1")
    
    def extract(self, text_content: str, url: str) -> dict:
        """Extract pricing fields from text content."""
        result = {
            "extractor": self.extractor_name,
            "source_url": url,
            "pricing": {},
            "free_plan": None,
            "trial": None,
            "custom_pricing": False,
        }
        
        # Detect currency
        currency = self._detect_currency(text_content)
        result["pricing"]["currency"] = currency
        
        # Extract price mentions
        prices = self._extract_prices(text_content, currency)
        result["pricing"]["detected_prices"] = prices
        
        # Check for free plan
        result["free_plan"] = self._check_free_plan(text_content)
        
        # Check for trial
        result["trial"] = self._check_trial(text_content)
        
        # Check for custom pricing
        result["custom_pricing"] = self._check_custom_pricing(text_content)
        
        # Check for per-seat/user pricing
        result["pricing"]["per_seat"] = self._check_per_seat(text_content)
        result["pricing"]["usage_based"] = self._check_usage_based(text_content)
        
        # Check for annual billing
        result["pricing"]["annual_billing"] = self._check_annual_billing(text_content)
        
        return result
    
    def _detect_currency(self, text: str) -> Optional[str]:
        """Detect currency from text content."""
        text_lower = text.lower()
        if '$' in text or 'usd' in text_lower:
            return "USD"
        elif '€' in text or 'eur' in text_lower:
            return "EUR"
        elif '£' in text or 'gbp' in text_lower:
            return "GBP"
        return None
    
    def _extract_prices(self, text: str, currency: Optional[str]) -> List[dict]:
        """Extract price mentions from text.
        
        GAP FIX: billing_basis field distinguishes monthly_billing from
        annual_billing_monthly_equivalent. Annual-equivalent prices must
        NEVER be fed into month-to-month budget logic as if identical.
        """
        prices = []
        
        # Pattern: $X/mo, $X/month, $X per month (true monthly billing)
        pattern = r'[\$€£]([\d,]+\.?\d*)\s*(?:/|per)\s*(?:mo|month|monthly)'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            amount = match.group(1).replace(',', '')
            prices.append({
                "amount": float(amount),
                "billing_interval": "monthly",
                "billing_basis": "monthly_billing",
                "raw": match.group(0),
            })
        
        # Pattern: $X/yr, $X/year, $X per year (annual billing)
        pattern = r'[\$€£]([\d,]+\.?\d*)\s*(?:/|per)\s*(?:yr|year|annual)'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            amount = match.group(1).replace(',', '')
            prices.append({
                "amount": float(amount),
                "billing_interval": "annual",
                "billing_basis": "annual_billing",
                "raw": match.group(0),
            })
        
        # Pattern: annual equivalent shown as monthly (e.g. "$X/mo billed annually")
        pattern = r'[\$€£]([\d,]+\.?\d*)\s*(?:/|per)\s*(?:mo|month|monthly).*?(?:billed\s+)?annually'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            amount = match.group(1).replace(',', '')
            prices.append({
                "amount": float(amount),
                "billing_interval": "monthly",
                "billing_basis": "annual_billing_monthly_equivalent",
                "raw": match.group(0),
                "note": "Annual commitment shown as monthly equivalent — NOT true monthly price",
            })
        
        # Pattern: $X (standalone price)
        pattern = r'[\$€£]([\d,]+\.?\d*)'
        for match in re.finditer(pattern, text):
            amount = match.group(1).replace(',', '')
            # Avoid duplicates
            if not any(p["raw"] == match.group(0) for p in prices):
                prices.append({
                    "amount": float(amount),
                    "billing_interval": "unknown",
                    "billing_basis": "unknown",
                    "raw": match.group(0),
                })
        
        return prices[:20]  # Limit to 20 price mentions
    
    def _check_free_plan(self, text: str) -> Optional[bool]:
        """Check if a free plan is mentioned.
        
        Returns None if uncertain, True/False if confident.
        """
        text_lower = text.lower()
        
        # Positive indicators
        free_indicators = [
            r'free\s+plan', r'free\s+tier', r'free\s+forever',
            r'free\s+version', r'free\s+account',
        ]
        for pattern in free_indicators:
            if re.search(pattern, text_lower):
                return True
        
        # Negative indicators
        no_free_indicators = [
            r'no\s+free\s+plan', r'no\s+free\s+tier',
            r'not\s+free', r'paid\s+only',
        ]
        for pattern in no_free_indicators:
            if re.search(pattern, text_lower):
                return False
        
        return None  # Uncertain
    
    def _check_trial(self, text: str) -> Optional[dict]:
        """Check for trial mentions.
        
        IMPORTANT: Trial is NOT a free plan — keep them separate.
        """
        text_lower = text.lower()
        
        # Pattern: X-day trial, X day free trial
        pattern = r'(\d+)\s*day\s*(?:free\s*)?trial'
        match = re.search(pattern, text_lower)
        if match:
            return {
                "available": True,
                "duration_days": int(match.group(1)),
                "type": "trial",  # NOT "free_plan"
            }
        
        # Pattern: free trial
        if 'free trial' in text_lower or 'free trial' in text:
            return {
                "available": True,
                "duration_days": None,
                "type": "trial",
            }
        
        return None
    
    def _check_custom_pricing(self, text: str) -> bool:
        """Check for custom/contact pricing mentions."""
        text_lower = text.lower()
        custom_indicators = [
            'custom pricing', 'contact sales', 'contact us',
            'enterprise pricing', 'tailored pricing', 'get a quote',
        ]
        return any(ind in text_lower for ind in custom_indicators)
    
    def _check_per_seat(self, text: str) -> bool:
        """Check for per-seat/per-user pricing."""
        text_lower = text.lower()
        return bool(re.search(r'per\s*(?:seat|user|member)', text_lower))
    
    def _check_usage_based(self, text: str) -> bool:
        """Check for usage-based pricing."""
        text_lower = text.lower()
        usage_indicators = [
            'usage-based', 'pay per use', 'pay as you go',
            'per request', 'per api call', 'per mb', 'per gb',
        ]
        return any(ind in text_lower for ind in usage_indicators)
    
    def _check_annual_billing(self, text: str) -> Optional[dict]:
        """Check for annual billing options."""
        text_lower = text.lower()
        
        if 'annual' in text_lower or 'yearly' in text_lower or 'per year' in text_lower:
            # Look for discount mention
            discount_pattern = r'(\d+)%\s*(?:off|save|discount).*annual'
            match = re.search(discount_pattern, text_lower)
            if match:
                return {
                    "available": True,
                    "discount_percent": int(match.group(1)),
                }
            return {"available": True, "discount_percent": None}
        
        return None


class FeatureExtractor(BaseExtractor):
    """Generic feature/capability extractor."""
    
    # Negation patterns that indicate a feature is NOT supported
    # These prevent "does not support X" from becoming a positive capability
    NEGATION_PATTERNS = [
        r'does\s+not\s+',
        r'do\s+not\s+',
        r'don\'t\s+',
        r'no\s+free\s+plan',
        r'no\s+free\s+tier',
        r'no\s+free\s+trial',
        r'not\s+available\s+on\s+',
        r'not\s+supported',
        r'not\s+included',
        r'without\s+',
        r'lacks\s+',
        r'missing\s+',
        r'unavailable\s+on\s+',
        r'cannot\s+',
        r'can\'t\s+',
        r'unable\s+to\s+',
        r'not\s+offered',
        r'not\s+provided',
    ]
    
    def __init__(self, tool_id: str):
        super().__init__(tool_id, f"{tool_id}_features_v1")
    
    def _is_negation(self, text: str) -> bool:
        """Check if a text fragment contains negation patterns.
        
        Returns True if the text appears to negate a capability,
        meaning it should NOT become a positive capability fact.
        
        NOTE: Absence of mention is NOT negation — only explicit negation
        patterns are detected. Do not infer negative evidence from silence.
        """
        text_lower = text.lower().strip()
        for pattern in self.NEGATION_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def extract(self, text_content: str, url: str) -> dict:
        """Extract feature mentions from text content.
        
        NOTE: This is a basic extractor. Per-tool extractors should
        provide more accurate feature lists based on known page structure.
        
        Negation patterns are filtered so "does not support X" never becomes
        a positive capability. Limitations are collected separately.
        """
        result = {
            "extractor": self.extractor_name,
            "source_url": url,
            "capabilities": [],
            "limitations": [],
        }
        
        # Extract bullet-point features (common pattern)
        bullet_patterns = [
            r'•\s*(.+?)(?:\n|$)',
            r'•\s*(.+?)(?:<br>|<li>)',
            r'✓\s*(.+?)(?:\n|$)',
        ]
        
        features = []
        limitations = []
        for pattern in bullet_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                cleaned = match.strip()
                if 10 < len(cleaned) < 200:  # Filter noise
                    # GAP FIX: Negation pattern matching
                    # If the text contains a negation pattern, it's a limitation, not a capability
                    if self._is_negation(cleaned):
                        limitations.append(cleaned)
                    else:
                        features.append(cleaned)
        
        result["capabilities"] = features[:50]  # Limit to 50
        result["limitations"] = limitations[:50]  # Limit to 50
        
        return result


def normalize_dict_capabilities(capabilities: Any) -> List[dict]:
    """Normalize structured/dict capability records without losing evidence provenance.
    
    GAP FIX: Some tools store capabilities as dicts with nested structure
    (e.g., {"name": "API", "category": "integration", "verified": True}).
    This function normalizes them to a consistent format while preserving
    evidence provenance fields.
    
    Args:
        capabilities: Can be a list of strings, list of dicts, or a single dict.
    
    Returns:
        List of normalized capability dicts with consistent structure:
        - name: The capability name (str)
        - category: Optional category (str)
        - evidence_source: Where this capability was verified (str)
        - verified: Whether officially verified (bool)
        - raw: Original data for provenance (str)
    """
    if capabilities is None:
        return []
    
    normalized = []
    
    # Handle single dict
    if isinstance(capabilities, dict):
        capabilities = [capabilities]
    
    # Handle list
    if isinstance(capabilities, list):
        for item in capabilities:
            if isinstance(item, str):
                normalized.append({
                    "name": item.strip(),
                    "category": None,
                    "evidence_source": None,
                    "verified": False,
                    "raw": item,
                })
            elif isinstance(item, dict):
                # Preserve provenance fields from the original dict
                entry = {
                    "name": str(item.get("name", item.get("capability", item.get("feature", "")))),
                    "category": item.get("category"),
                    "evidence_source": item.get("evidence_source", item.get("source")),
                    "verified": bool(item.get("verified", False)),
                    "raw": json.dumps(item) if len(str(item)) > 200 else str(item),
                }
                # Preserve any additional fields from the original dict
                for key in ("description", "url", "verified_at", "claim_id"):
                    if key in item:
                        entry[key] = item[key]
                normalized.append(entry)
            else:
                # Unknown type — store as raw string
                normalized.append({
                    "name": str(item),
                    "category": None,
                    "evidence_source": None,
                    "verified": False,
                    "raw": str(item),
                })
    
    return normalized


def get_extractor(tool_id: str, source_role: str) -> Optional[BaseExtractor]:
    """Get the appropriate extractor for a tool and source role.
    
    Args:
        tool_id: Tool identifier
        source_role: Source role (PRICING, PRODUCT_FEATURES, etc.)
    
    Returns:
        Extractor instance or None if no specific extractor exists
    """
    if source_role == "PRICING":
        return PricingExtractor(tool_id)
    elif source_role in ("PRODUCT_FEATURES", "DOCUMENTATION"):
        return FeatureExtractor(tool_id)
    
    return None
