from rapidfuzz import fuzz
import requests
from data.hsn_master import COMMON_HSN

# Indian state codes (first 2 digits of GSTIN)
STATE_CODES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh",
    "03": "Punjab",          "04": "Chandigarh",
    "05": "Uttarakhand",     "06": "Haryana",
    "07": "Delhi",           "08": "Rajasthan",
    "09": "Uttar Pradesh",   "10": "Bihar",
    "11": "Sikkim",          "12": "Arunachal Pradesh",
    "13": "Nagaland",        "14": "Manipur",
    "15": "Mizoram",         "16": "Tripura",
    "17": "Meghalaya",       "18": "Assam",
    "19": "West Bengal",     "20": "Jharkhand",
    "21": "Odisha",          "22": "Chhattisgarh",
    "23": "Madhya Pradesh",  "24": "Gujarat",
    "26": "Dadra & NH",      "27": "Maharashtra",
    "28": "Andhra Pradesh",  "29": "Karnataka",
    "30": "Goa",             "31": "Lakshadweep",
    "32": "Kerala",          "33": "Tamil Nadu",
    "34": "Puducherry",      "36": "Telangana",
    "37": "Andhra Pradesh (new)",
}

def resolve_gst(item_description: str, seller_gstin: str,
                buyer_gstin: str, amount: float) -> dict:
    """
    Returns full GST breakdown for a transaction.
    """
    # Step 1: fuzzy match item to HSN
    hsn_code, gst_rate = lookup_hsn(item_description)

    # Step 2: determine tax type
    seller_state = seller_gstin[:2] if seller_gstin else None
    buyer_state  = buyer_gstin[:2]  if buyer_gstin  else None

    if seller_state and buyer_state and seller_state != buyer_state:
        tax_type = "IGST"
        taxes = {"IGST": round(amount * gst_rate / 100, 2)}
    else:
        tax_type = "CGST+SGST"
        half = round(amount * gst_rate / 200, 2)
        taxes = {"CGST": half, "SGST": half}

    total_tax = sum(taxes.values())

    return {
        "hsn_code":    hsn_code,
        "gst_rate":    gst_rate,
        "tax_type":    tax_type,
        "taxes":       taxes,
        "total_tax":   total_tax,
        "total_amount": amount + total_tax,
        "is_exempt":   gst_rate == 0,
    }

def lookup_hsn(description: str) -> tuple[str, float]:
    """
    Returns (hsn_code, gst_rate) for a product/service description.
    First tries local DB, then falls back to live GST portal.
    """
    if not description:
        return "UNKNOWN", 18.0

    # Try local dictionary fuzzy match
    best_hsn = None
    best_score = 0
    best_rate = 18.0
    
    for hsn_code, info in COMMON_HSN.items():
        score = fuzz.partial_ratio(description.lower(), info["desc"].lower())
        if score > best_score:
            best_score = score
            best_hsn = hsn_code
            best_rate = info["rate"]
            
    if best_score > 75 and best_hsn:
        return best_hsn, best_rate

    # Fallback to the live portal (mocked gracefully if unavailable)
    try:
        resp = requests.get(
            "https://services.gst.gov.in/services/api/search/goodservices",
            params={"searchkey": description, "lang": "EN"},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success") and data.get("data"):
                top = data["data"][0]
                return top["hsnCode"], float(top["igstRate"])
    except Exception:
        pass

    # Last resort: return 18% (most common rate) + flag for review
    return "UNKNOWN", 18.0
