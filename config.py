# Blostem's existing partners - exclude from prospecting
EXISTING_PARTNERS = [
    "MobiKwik", "Jupiter Money", "Jupiter", "Upstox", "Zerodha",
    "Tide", "Fello", "Aspero", "Centricity", "GoldenPi",
    "Coin by Zerodha", "Zerodha Coin"
]

COMPETITORS = [
    "Stable Money", "Deciml", "Wint Wealth", "Jiraaf", "Grip Invest",
    "Stablemoney"
]

# Companies that appear in fintech news but are NOT Blostem prospects
NON_PROSPECTS = [
    # Regulatory / Government
    "RBI", "Reserve Bank of India", "SEBI", "NPCI", "IRDAI", "MCA",
    "NITI Aayog", "Ministry of Finance", "Government of India",
    "EPF", "EPFO", "Post Office", "India Post", "IPPB",
    "India Post Payments Bank",
    
    # Traditional banks / payment banks
    "SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Bank",
    "Bank of India", "Punjab National Bank", "Canara Bank", "DCB Bank",
    "Airtel Payments Bank", "Paytm Payments Bank", "Jio Payments Bank",
    
    # Foreign companies with no India product relevance
    "Revolut", "Wise", "N26", "Monzo",
    
    # Non-fintech companies
    "Meta", "Facebook", "Google", "Amazon", "Flipkart",
    "Dabur India", "Falcon",
    
    # News/data companies
    "Tracxn", "Inc42", "YourStory", "Entrackr", "VCCircle",
    
    # Generic terms
    "India Fintech", "None", "None mentioned", "Fintech",
]

# Product categories and their Blostem fit
CATEGORY_PRODUCT_MAP = {
    "broker": {
        "gap_products": ["has_fd", "has_rd", "has_bonds"],
        "recommended_blostem_product": "FD + RD SDK",
        "pitch_angle": "Your users already invest with you — FDs are the next logical product"
    },
    "payment": {
        "gap_products": ["has_fd", "has_upi_credit"],
        "recommended_blostem_product": "Credit on UPI + FD SDK",
        "pitch_angle": "Your UPI transaction volume is the perfect base for Credit on UPI"
    },
    "neobank": {
        "gap_products": ["has_fd", "has_rd"],
        "recommended_blostem_product": "FD + RD SDK",
        "pitch_angle": "Complete your savings stack with multi-bank FDs in 7 days"
    },
    "wealth": {
        "gap_products": ["has_fd", "has_bonds"],
        "recommended_blostem_product": "FD + Bonds SDK",
        "pitch_angle": "Add fixed-income depth to your wealth platform"
    },
    "savings": {
        "gap_products": ["has_rd", "has_fd"],
        "recommended_blostem_product": "RD SDK",
        "pitch_angle": "Turn savings goals into recurring deposits automatically"
    },
    "credit_building": {
        "gap_products": ["has_fd"],
        "recommended_blostem_product": "FD-backed Credit Card infrastructure",
        "pitch_angle": "Your thin-file users can build credit history through FD-backed cards"
    }
}

# Keywords to detect in news articles
FD_KEYWORDS = ["fixed deposit", "FD", "term deposit", "savings deposit"]
RD_KEYWORDS = ["recurring deposit", "RD", "systematic savings", "monthly savings"]
CREDIT_KEYWORDS = ["credit on UPI", "UPI credit", "credit line", "overdraft"]
BONDS_KEYWORDS = ["bonds", "fixed income", "debt", "debentures"]
BANKING_INFRA_KEYWORDS = ["banking infrastructure", "FD API", "banking API", "deposit infrastructure"]

EXPANSION_KEYWORDS = [
    "expanding into", "launching", "plans to offer", "will introduce",
    "adding", "new product", "product expansion", "savings products",
    "banking products", "financial products"
]

COMPETITOR_INTEGRATION_KEYWORDS = [
    "powered by Stable Money", "in partnership with Stable Money",
    "powered by GoldenPi", "Wint Wealth integration",
    "Deciml partnership", "Jiraaf integration"
]

# Signal weights for WHO score
SIGNAL_WEIGHTS = {
    "PRODUCT_GAP": 35,       # structural, always present
    "FUNDING_EXPANSION": 25, # strong intent signal
    "COMPETITOR_MOVE": 20,   # urgency signal
    "LEADERSHIP_HIRE": 15,   # strategic intent signal
    "DISPLACEMENT": 30,      # separate track, high weight
}

# Score thresholds
HOT_THRESHOLD = 60
WARM_THRESHOLD = 30

# Only monitor prospects with WHO score >= this threshold
# Prevents wasting resources on low-potential WATCH prospects
MONITORING_MIN_SCORE = 30  # WARM and HOT only

# LLM config
LLM_MODEL = "gemini-2.0-flash-lite"
LLM_DAILY_LIMIT = 1000  # Free tier limit

# Rate limiting — stay well under the 15 RPM limit
# With 0.5s sleep between calls in news_monitor.py we're at ~2 RPM
# Safe buffer for the free tier
LLM_CALL_DELAY_SECONDS = 0.5