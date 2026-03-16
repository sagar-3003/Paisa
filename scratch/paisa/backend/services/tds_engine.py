import json
import os
from rapidfuzz import fuzz

# Dynamically resolve the absolute path to this file to allow tests/execution from any working directory.
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, "..", "data", "tds_rules.json")
    with open(data_path) as f:
        TDS_RULES = json.load(f)["rules"]
except Exception as e:
    print(f"Warning: Could not load TDS rules: {e}")
    TDS_RULES = []

def check_tds(
    description: str,
    amount: float,
    party_type: str,          # "individual" | "company" | "llp" | "huf"
    buyer_entity_type: str,   # "company" | "individual" | "huf"
    buyer_turnover_crore: float,  # buyer's last year turnover
    yearly_total_paid: float  # total paid to this party this FY
) -> dict:
    """
    Returns TDS applicability and amount for a transaction.
    """
    result = {
        "applicable": False,
        "section": None,
        "rate": 0.0,
        "tds_amount": 0.0,
        "net_payable": amount,
        "reason": "TDS not applicable"
    }

    # Rule 1: Individual/HUF buyers below turnover threshold
    if buyer_entity_type in ("individual", "huf"):
        if buyer_turnover_crore < 1.0:
            result["reason"] = (
                "Buyer is Individual/HUF with turnover < ₹1 crore. "
                "Not liable to deduct TDS."
            )
            return result

    # Rule 2: Match description to TDS section
    matched_rule = None
    best_score = 0

    if not description:
        result["reason"] = "No description provided to match TDS rule."
        return result

    for rule in TDS_RULES:
        for keyword in rule["keywords"]:
            score = fuzz.partial_ratio(description.lower(), keyword.lower())
            if score > best_score and score > 70:
                best_score = score
                matched_rule = rule

    if not matched_rule:
        result["reason"] = "No TDS section matched for this type of payment."
        return result

    # Rule 3: Check threshold
    threshold = matched_rule.get("threshold_single", 0)
    agg_threshold = matched_rule.get("threshold_aggregate_yearly", 0)
    projected_total = yearly_total_paid + amount

    if amount < threshold and projected_total < agg_threshold:
        result["reason"] = (
            f"Section {matched_rule['section']}: Amount ₹{amount:,.0f} is below "
            f"threshold of ₹{threshold:,.0f} per transaction "
            f"and aggregate ₹{agg_threshold:,.0f}/year."
        )
        return result

    # Rule 4: Apply rate
    rate = (matched_rule["rate_company"]
            if party_type == "company"
            else matched_rule["rate_individual"])

    tds_amount = round(amount * rate / 100, 2)

    result.update({
        "applicable":  True,
        "section":     matched_rule["section"],
        "description": matched_rule["description"],
        "rate":        rate,
        "tds_amount":  tds_amount,
        "net_payable": round(amount - tds_amount, 2),
        "reason":      f"Section {matched_rule['section']} @ {rate}%"
    })
    return result
