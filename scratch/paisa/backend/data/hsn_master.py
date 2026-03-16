import requests

# The GST e-invoice portal provides HSN search, but for our v1 open source
# deployment we will largely rely on our hardcoded common dictionary
GST_PORTAL_URL = "https://services.gst.gov.in/services/api/search/hsnsachapters"

# Fallback: hardcoded top-100 common HSN codes
COMMON_HSN = {
    "8471": {"desc": "Computers, laptops",          "rate": 18.0},
    "8517": {"desc": "Mobile phones",               "rate": 18.0},
    "8528": {"desc": "Televisions, monitors",       "rate": 18.0},
    "8443": {"desc": "Printers",                    "rate": 18.0},
    "9403": {"desc": "Furniture",                   "rate": 18.0},
    "6403": {"desc": "Footwear",                    "rate": 12.0},
    "6101": {"desc": "Garments above ₹1000",        "rate": 12.0},
    "2201": {"desc": "Water (packaged)",            "rate":  18.0},
    "1901": {"desc": "Food preparations",           "rate":  18.0},
    "3004": {"desc": "Medicines",                   "rate":  12.0},
    "3401": {"desc": "Soap, detergents",            "rate":  18.0},
    "8716": {"desc": "Trailers, vehicles (NMV)",    "rate":  28.0},
    "8703": {"desc": "Cars, automobiles",            "rate":  28.0},
    "2402": {"desc": "Cigarettes, tobacco",         "rate":  28.0},
    "2203": {"desc": "Beer",                        "rate":  28.0},
    "0101": {"desc": "Live animals",                "rate":   0.0},
    "0701": {"desc": "Vegetables",                  "rate":   0.0},
    "1001": {"desc": "Wheat",                       "rate":   0.0},
    "0401": {"desc": "Milk",                        "rate":   0.0},
    
    # SAC codes (services start with 99)
    "9983": {"desc": "IT services, software",       "rate":  18.0},
    "9985": {"desc": "Support services",            "rate":  18.0},
    "9954": {"desc": "Construction services",       "rate":  18.0},
    "9991": {"desc": "Education services",          "rate":   0.0},
    "9993": {"desc": "Health services",             "rate":   0.0},
    "9972": {"desc": "Real estate services",        "rate":  18.0},
    "9971": {"desc": "Financial services",          "rate":  18.0},
    "9968": {"desc": "Postal/courier services",     "rate":  18.0},
    "9967": {"desc": "Transport of goods",          "rate":   5.0},
    "9964": {"desc": "Passenger transport",         "rate":   5.0},
    "9963": {"desc": "Restaurant/food services",    "rate":   5.0},
}
