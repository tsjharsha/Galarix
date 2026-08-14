# =====================================================
# STRING GENERATORS — Non-statistical variable types
# =====================================================
# Handles variables that don't come from probability
# distributions: names, emails, IDs, dates, card numbers.
#
# All generators are DETERMINISTIC — seeded by the
# master RNG from seed_engine, so the same prompt
# always produces the same synthetic identities.
# =====================================================

import hashlib
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Dict


# ── Regional Data Pools ──
REGIONAL_DATA = {
    "US": {
        "FIRST_NAMES": ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda"],
        "LAST_NAMES": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"],
        "BANKS": ["Chase", "Bank of America", "Wells Fargo", "Citibank", "US Bank", "PNC"],
        "MERCHANTS": ["Amazon", "Walmart", "Target", "Starbucks", "Uber", "CVS Pharmacy", "Home Depot"],
        "LOCATIONS": ["New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Miami, FL"],
        "COMPANIES": ["Acme Corp", "Globex Industries", "Umbrella Inc", "Initech Systems"],
        "IBAN_PREFIX": "US",
        "CURRENCY": "USD",
        "PHONE_FORMAT": "+1-{area}-{pre}-{line}",
        "PHONE_AREAS": ["212", "310", "312", "713", "305", "415", "202", "404"],
        "ADDRESS_FORMATS": ["{num} {street}, {city}, {state} {zip}"],
        "STREETS": ["Main St", "Oak Ave", "Broadway", "Park Blvd", "Market St", "Elm Rd"],
        "STATES": ["NY", "CA", "IL", "TX", "FL"],
        "TAX_ID_FORMAT": "{a}{b}-{c}{d}-{e}{f}{g}{h}",
        "TAX_ID_NAME": "SSN",
    },
    "UK": {
        "FIRST_NAMES": ["Oliver", "Olivia", "George", "Amelia", "Arthur", "Isla", "Noah", "Ava"],
        "LAST_NAMES": ["Smith", "Jones", "Taylor", "Williams", "Brown", "Davies", "Evans", "Thomas"],
        "BANKS": ["Barclays", "HSBC", "Lloyds Bank", "NatWest", "Monzo", "Santander UK"],
        "MERCHANTS": ["Tesco", "Sainsbury's", "Asda", "Greggs", "Costa Coffee", "Boots", "Deliveroo"],
        "LOCATIONS": ["London", "Manchester", "Birmingham", "Edinburgh", "Glasgow", "Liverpool"],
        "COMPANIES": ["British Gas", "BP", "Unilever", "GlaxoSmithKline", "AstraZeneca"],
        "IBAN_PREFIX": "GB",
        "CURRENCY": "GBP",
        "PHONE_FORMAT": "+44-{area}-{line}",
        "PHONE_AREAS": ["20", "121", "131", "141", "161", "113"],
        "ADDRESS_FORMATS": ["{num} {street}, {city} {postcode}"],
        "STREETS": ["High Street", "Church Road", "Station Road", "King Street", "Queen Street"],
        "STATES": ["England", "Scotland", "Wales"],
        "TAX_ID_FORMAT": "{a}{b} {c}{d} {e}{f} {g}{h} {i}",
        "TAX_ID_NAME": "NIN",
    },
    "IN": {
        "FIRST_NAMES": ["Aarav", "Aadya", "Vihaan", "Diya", "Arjun", "Ananya", "Rohan", "Priya"],
        "LAST_NAMES": ["Patel", "Singh", "Sharma", "Kumar", "Gupta", "Desai", "Joshi", "Verma"],
        "BANKS": ["HDFC Bank", "ICICI Bank", "State Bank of India", "Axis Bank", "Kotak Mahindra"],
        "MERCHANTS": ["Flipkart", "Reliance Smart", "Zomato", "Swiggy", "BigBasket", "Ola", "Paytm"],
        "LOCATIONS": ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Pune", "Kolkata"],
        "COMPANIES": ["Tata Consultancy Services", "Reliance Industries", "Infosys", "Wipro"],
        "IBAN_PREFIX": "IN",
        "CURRENCY": "INR",
        "PHONE_FORMAT": "+91-{area}-{line}",
        "PHONE_AREAS": ["22", "11", "80", "40", "44", "20", "33"],
        "ADDRESS_FORMATS": ["{num}, {street}, {city} - {zip}"],
        "STREETS": ["MG Road", "Station Road", "Link Road", "Gandhi Nagar", "Nehru Place"],
        "STATES": ["Maharashtra", "Karnataka", "Delhi", "Tamil Nadu", "Telangana"],
        "TAX_ID_FORMAT": "{a}{b}{c}{d}{e}{f}{g}{h}{i}{j}",
        "TAX_ID_NAME": "PAN",
    },
    "EU": {
        "FIRST_NAMES": ["Lukas", "Mia", "Leon", "Emma", "Louis", "Chloe", "Maximilian", "Sofia"],
        "LAST_NAMES": ["Mueller", "Schmidt", "Rossi", "Russo", "Garcia", "Martinez", "Dubois", "Moreau"],
        "BANKS": ["Deutsche Bank", "BNP Paribas", "Santander", "ING Group", "Societe Generale"],
        "MERCHANTS": ["Carrefour", "Aldi", "Lidl", "Zara", "Decathlon", "IKEA"],
        "LOCATIONS": ["Berlin", "Paris", "Madrid", "Rome", "Amsterdam", "Frankfurt", "Milan"],
        "COMPANIES": ["Siemens", "Volkswagen", "LVMH", "SAP", "Airbus"],
        "IBAN_PREFIX": "DE",
        "CURRENCY": "EUR",
        "PHONE_FORMAT": "+49-{area}-{line}",
        "PHONE_AREAS": ["30", "40", "89", "69", "221", "711"],
        "ADDRESS_FORMATS": ["{street} {num}, {zip} {city}"],
        "STREETS": ["Hauptstrasse", "Bahnhofstrasse", "Berliner Strasse", "Schillerstrasse"],
        "STATES": ["Bavaria", "Hesse", "NRW", "Berlin"],
        "TAX_ID_FORMAT": "DE{a}{b}{c}{d}{e}{f}{g}{h}{i}",
        "TAX_ID_NAME": "Steuer-ID",
    },
    "JP": {
        "FIRST_NAMES": ["Hiroshi", "Yoko", "Kenji", "Mika", "Takumi", "Sakura", "Daiki", "Aoi"],
        "LAST_NAMES": ["Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe", "Ito", "Yamamoto", "Nakamura"],
        "BANKS": ["Mitsubishi UFJ", "Sumitomo Mitsui", "Mizuho", "Japan Post Bank"],
        "MERCHANTS": ["7-Eleven", "Lawson", "FamilyMart", "Rakuten", "Uniqlo", "Sony Store"],
        "LOCATIONS": ["Tokyo", "Osaka", "Yokohama", "Nagoya", "Sapporo", "Fukuoka"],
        "COMPANIES": ["Toyota", "Sony", "Honda", "SoftBank", "Nintendo"],
        "IBAN_PREFIX": "JP",
        "CURRENCY": "JPY",
        "PHONE_FORMAT": "+81-{area}-{line}",
        "PHONE_AREAS": ["3", "6", "45", "52", "11", "92"],
        "ADDRESS_FORMATS": ["{city} {street} {num}"],
        "STREETS": ["Chuo-ku", "Shibuya", "Minato-ku", "Shinjuku", "Ginza"],
        "STATES": ["Tokyo", "Osaka", "Kanagawa", "Aichi", "Hokkaido"],
        "TAX_ID_FORMAT": "{a}{b}{c}{d}-{e}{f}{g}{h}-{i}{j}{k}{l}",
        "TAX_ID_NAME": "My Number",
    },
    "AU": {
        "FIRST_NAMES": ["Jack", "Charlotte", "William", "Isla", "Noah", "Mia", "Oliver", "Grace"],
        "LAST_NAMES": ["Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Morton", "White"],
        "BANKS": ["Commonwealth Bank", "Westpac", "ANZ", "NAB", "Macquarie"],
        "MERCHANTS": ["Woolworths", "Coles", "Bunnings", "Kmart", "JB Hi-Fi", "Qantas"],
        "LOCATIONS": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Hobart"],
        "COMPANIES": ["BHP", "Rio Tinto", "CSL", "Telstra", "Woolworths Group"],
        "IBAN_PREFIX": "AU",
        "CURRENCY": "AUD",
        "PHONE_FORMAT": "+61-{area}-{line}",
        "PHONE_AREAS": ["2", "3", "7", "8"],
        "ADDRESS_FORMATS": ["{num} {street}, {city} {state} {zip}"],
        "STREETS": ["George Street", "King Street", "Collins Street", "Pitt Street"],
        "STATES": ["NSW", "VIC", "QLD", "WA", "SA", "TAS"],
        "TAX_ID_FORMAT": "{a}{b}{c} {d}{e}{f} {g}{h}{i}",
        "TAX_ID_NAME": "TFN",
    },
    "BR": {
        "FIRST_NAMES": ["Miguel", "Alice", "Arthur", "Laura", "Heitor", "Sophia", "Davi", "Maria"],
        "LAST_NAMES": ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves"],
        "BANKS": ["Itau", "Bradesco", "Banco do Brasil", "Caixa", "Nubank"],
        "MERCHANTS": ["Mercado Livre", "Magazine Luiza", "Americanas", "Ifood", "Pao de Acucar"],
        "LOCATIONS": ["Sao Paulo", "Rio de Janeiro", "Brasilia", "Salvador", "Fortaleza"],
        "COMPANIES": ["Petrobras", "Vale", "Ambev", "JBS", "Itau Unibanco"],
        "IBAN_PREFIX": "BR",
        "CURRENCY": "BRL",
        "PHONE_FORMAT": "+55-{area}-{line}",
        "PHONE_AREAS": ["11", "21", "31", "41", "51", "61"],
        "ADDRESS_FORMATS": ["Rua {street}, {num} - {city}/{state}"],
        "STREETS": ["Augusta", "Paulista", "Copacabana", "Ipanema", "Consolacao"],
        "STATES": ["SP", "RJ", "MG", "BA", "RS"],
        "TAX_ID_FORMAT": "{a}{b}{c}.{d}{e}{f}.{g}{h}{i}-{j}{k}",
        "TAX_ID_NAME": "CPF",
    }
}

CRYPTO_EXCHANGES = ["Binance", "Coinbase", "Kraken", "Bybit", "OKX", "KuCoin"]
CRYPTO_PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT", "XRP/USDT", "ADA/USDT"]
FOREX_PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "NZD/USD", "USD/CAD", "EUR/GBP"]

EXPENSE_CATEGORIES = ["Airfare", "Hotel", "Ground Transportation", "Meals - Client", "Meals - Solo", "Conference", "Office Supplies", "Parking"]


def generate_string_column(
    rng: np.random.Generator,
    var_name: str,
    var_type: str,
    n_rows: int,
    entity: str = "",
    region: str = "US",
) -> List:
    """
    Generate a column of non-statistical data based on the variable name
    and type. Regionalized to match the selected region.
    """
    name_lower = var_name.lower()
    
    # Get regional data (fallback to US if missing)
    if region not in REGIONAL_DATA:
        region = "US"
    r_data = REGIONAL_DATA[region]

    # ── ID Fields ──
    if any(k in name_lower for k in ["_id", "record_id", "transaction_id", "alert_id", "trade_id", "contract_id"]):
        return _generate_ids(rng, var_name, n_rows, entity)

    # ── Policy Number Fields ──
    if "policy" in name_lower and ("number" in name_lower or "no" in name_lower or name_lower == "policy_number"):
        prefix = entity[:3].upper() if entity else "POL"
        base = rng.integers(100000, 999999)
        return [f"{prefix}-{base + i:08d}" for i in range(n_rows)]

    # ── Name Fields ──
    if "first_name" in name_lower:
        indices = rng.integers(0, len(r_data["FIRST_NAMES"]), size=n_rows)
        return [r_data["FIRST_NAMES"][i] for i in indices]

    if "last_name" in name_lower:
        indices = rng.integers(0, len(r_data["LAST_NAMES"]), size=n_rows)
        return [r_data["LAST_NAMES"][i] for i in indices]

    # ── Email Fields ──
    if "email" in name_lower:
        first_idx = rng.integers(0, len(r_data["FIRST_NAMES"]), size=n_rows)
        last_idx = rng.integers(0, len(r_data["LAST_NAMES"]), size=n_rows)
        domains = ["gmail.com", "yahoo.com", "outlook.com"] if region == "US" else ["gmail.com", f"mail.{region.lower()}", "yahoo.com"]
        dom_idx = rng.integers(0, len(domains), size=n_rows)
        return [
            f"{r_data['FIRST_NAMES'][fi].lower()}.{r_data['LAST_NAMES'][li].lower()}{rng.integers(1, 999)}@{domains[di]}"
            for fi, li, di in zip(first_idx, last_idx, dom_idx)
        ]

    # ── Card Number Fields ──
    if "card_number" in name_lower or "card_no" in name_lower:
        suffixes = rng.integers(1000, 9999, size=n_rows)
        return [f"****-****-****-{s}" for s in suffixes]

    # ── Merchant Names ──
    if "merchant_name" in name_lower:
        indices = rng.integers(0, len(r_data["MERCHANTS"]), size=n_rows)
        return [r_data["MERCHANTS"][i] for i in indices]

    # ── Company Names ──
    if "company" in name_lower or "employer" in name_lower:
        indices = rng.integers(0, len(r_data["COMPANIES"]), size=n_rows)
        return [r_data["COMPANIES"][i] for i in indices]

    # ── Bank Names ──
    if "bank_name" in name_lower or ("bank" in name_lower and "account" not in name_lower):
        indices = rng.integers(0, len(r_data["BANKS"]), size=n_rows)
        return [r_data["BANKS"][i] for i in indices]

    # ── Location Fields ──
    if "location" in name_lower or "city" in name_lower:
        indices = rng.integers(0, len(r_data["LOCATIONS"]), size=n_rows)
        return [r_data["LOCATIONS"][i] for i in indices]

    # ── Currency ──
    if "currency" in name_lower:
        return [r_data["CURRENCY"]] * n_rows

    # ── Country Fields ──
    if "country" in name_lower or "jurisdiction" in name_lower:
        # Direct mapping: region code → country name (no fragile indexing)
        _REGION_TO_COUNTRY = {
            "US": "United States", "UK": "United Kingdom", "IN": "India",
            "EU": "Germany", "JP": "Japan", "AU": "Australia", "BR": "Brazil",
        }
        country_name = _REGION_TO_COUNTRY.get(region, "United States")
        return [country_name] * n_rows

    # ── Account Numbers ──
    # ── Account Numbers (sender_account, receiver_account, etc.) ──
    if "account" in name_lower and "statement" not in name_lower:
        return [f"ACCT-{rng.integers(10000000, 99999999)}" for _ in range(n_rows)]

    # ── IBAN ──
    if "iban" in name_lower:
        return [f"{r_data['IBAN_PREFIX']}{rng.integers(10, 99)}{rng.integers(10000000, 99999999)}{rng.integers(10000000, 99999999)}" for _ in range(n_rows)]

    # ── SWIFT/BIC Code ──
    if "swift" in name_lower or "bic" in name_lower:
        bank_codes = [f"{r_data['BANKS'][0][:4].upper()}{r_data['IBAN_PREFIX']}33", f"{r_data['BANKS'][1][:4].upper()}{r_data['IBAN_PREFIX']}XX"]
        indices = rng.integers(0, len(bank_codes), size=n_rows)
        return [bank_codes[i] for i in indices]

    # ── Wallet Address (Crypto) ──
    if "wallet" in name_lower or ("address" in name_lower and "crypto" in entity):
        return [f"0x{hashlib.sha256(f'{rng.integers(0, 2**63)}'.encode()).hexdigest()[:40]}" for _ in range(n_rows)]

    # ── Trading Symbol / Ticker ──
    if "symbol" in name_lower or "ticker" in name_lower:
        if "crypto" in entity or "crypto" in name_lower:
            indices = rng.integers(0, len(CRYPTO_PAIRS), size=n_rows)
            return [CRYPTO_PAIRS[i] for i in indices]
        elif "forex" in entity or "fx" in name_lower:
            indices = rng.integers(0, len(FOREX_PAIRS), size=n_rows)
            return [FOREX_PAIRS[i] for i in indices]
        else:
            # Stock ticker symbols
            stock_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM",
                             "V", "JNJ", "WMT", "PG", "UNH", "HD", "DIS", "BAC", "XOM",
                             "KO", "PFE", "CSCO", "INTC", "VZ", "MRK", "ABT", "CVX"]
            indices = rng.integers(0, len(stock_tickers), size=n_rows)
            return [stock_tickers[i] for i in indices]

    # ── Trading Pair ──
    if "pair" in name_lower:
        if "crypto" in entity or "crypto" in name_lower:
            indices = rng.integers(0, len(CRYPTO_PAIRS), size=n_rows)
            return [CRYPTO_PAIRS[i] for i in indices]
        elif "forex" in entity or "fx" in name_lower:
            indices = rng.integers(0, len(FOREX_PAIRS), size=n_rows)
            return [FOREX_PAIRS[i] for i in indices]

    # ── Exchange ──
    if "exchange" in name_lower or "platform" in name_lower:
        indices = rng.integers(0, len(CRYPTO_EXCHANGES), size=n_rows)
        return [CRYPTO_EXCHANGES[i] for i in indices]

    # ── Expense Category ──
    if "expense" in name_lower and "category" in name_lower:
        indices = rng.integers(0, len(EXPENSE_CATEGORIES), size=n_rows)
        return [EXPENSE_CATEGORIES[i] for i in indices]

    # ── Phone Number Fields ──
    if "phone" in name_lower or "mobile" in name_lower or "tel" in name_lower:
        areas = r_data.get("PHONE_AREAS", ["555"])
        results = []
        for _ in range(n_rows):
            area = areas[int(rng.integers(0, len(areas)))]
            line = f"{rng.integers(100, 999)}-{rng.integers(1000, 9999)}"
            results.append(f"+{area}-{line}")
        return results

    # ── Address Fields ──
    if "address" in name_lower and "wallet" not in name_lower and "email" not in name_lower:
        streets = r_data.get("STREETS", ["Main St"])
        locs = r_data["LOCATIONS"]
        results = []
        for _ in range(n_rows):
            num = int(rng.integers(1, 9999))
            street = streets[int(rng.integers(0, len(streets)))]
            city = locs[int(rng.integers(0, len(locs)))]
            results.append(f"{num} {street}, {city}")
        return results

    # ── Tax ID / PAN / SSN / NIN Fields ──
    if "tax_id" in name_lower or "pan" in name_lower or "ssn" in name_lower or "nin" in name_lower:
        tax_name = r_data.get("TAX_ID_NAME", "TAX")
        results = []
        for _ in range(n_rows):
            digits = [str(int(rng.integers(0, 10))) for _ in range(12)]
            results.append(f"{tax_name}-{''.join(digits[:4])}-{''.join(digits[4:8])}-{''.join(digits[8:])}")
        return results

    # ── Description Fields (prevents string-fallback garbage) ──
    if "description" in name_lower or "memo" in name_lower or "notes" in name_lower or "remarks" in name_lower:
        txn_descriptions = [
            "Direct Deposit", "ATM Withdrawal", "Online Transfer", "POS Purchase",
            "Wire Transfer", "Check Deposit", "Bill Payment", "Refund",
            "Subscription Fee", "Salary Credit", "Loan Payment", "Interest Credit",
            "Service Charge", "Cash Deposit", "Mobile Payment",
        ]
        indices = rng.integers(0, len(txn_descriptions), size=n_rows)
        return [txn_descriptions[i] for i in indices]

    # ── DateTime Fields ──
    if var_type == "datetime" or "date" in name_lower or "timestamp" in name_lower:
        return _generate_datetimes(rng, n_rows)

    # ── Generic String Fallback ──
    return [f"{var_name}_{i+1}" for i in range(n_rows)]


def _generate_ids(
    rng: np.random.Generator,
    var_name: str,
    n_rows: int,
    entity: str,
) -> List[str]:
    """Generate unique deterministic IDs."""
    # Create a short prefix from entity name
    prefix = entity[:3].upper() if entity else "GX"
    # Sequential base + random suffix for uniqueness
    base = rng.integers(100000, 999999)
    return [f"{prefix}-{base + i:08d}" for i in range(n_rows)]


def _generate_datetimes(
    rng: np.random.Generator,
    n_rows: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[str]:
    """Generate uniformly distributed datetimes within a range."""
    if start_date is None:
        start_date = datetime(2024, 1, 1)
    if end_date is None:
        end_date = datetime(2025, 12, 31)

    total_seconds = int((end_date - start_date).total_seconds())
    offsets = rng.integers(0, max(total_seconds, 1), size=n_rows)

    return [
        (start_date + timedelta(seconds=int(offset))).strftime("%Y-%m-%d %H:%M:%S")
        for offset in offsets
    ]


def weave_semantic_strings(columns: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """
    Semantic Weaver (Auto-Heal Phase 3):
    Two-pass consistency engine:
      1. Identity Weaver: binds name fields to emails
      2. Entity Consistency Cache: ensures repeated entities
         (companies, banks, merchants, people) always carry
         the same correlated attributes across all rows.
    """
    if not columns:
        return columns

    # ── PASS 1: Name → Email Binding ──
    fname_col = None
    lname_col = None
    email_col = None

    for col in columns:
        if "first_name" in col: fname_col = col
        elif "last_name" in col: lname_col = col
        elif "email" in col: email_col = col

    if fname_col and lname_col and email_col:
        n_rows = len(columns[fname_col])
        domains = ["gmail.com", "yahoo.com", "outlook.com", "protonmail.com", "icloud.com"]
        new_emails = []
        for i in range(n_rows):
            f = str(columns[fname_col][i]).lower()
            l = str(columns[lname_col][i]).lower()
            domain = domains[(i + len(f)) % len(domains)]
            num = (_stable_int(f"{f}|{l}|{i}") % 899) + 100
            new_emails.append(f"{f}.{l}{num}@{domain}")
        columns[email_col] = np.array(new_emails, dtype=object)

    # ── PASS 2: Entity Consistency Cache ──
    columns = _enforce_entity_consistency(columns)

    return columns


# ═══════════════════════════════════════════════════════
# ENTITY CONSISTENCY CACHE
# ═══════════════════════════════════════════════════════
# Defines "anchor" columns and their "bound" columns.
# When the same anchor value appears in multiple rows,
# all bound column values are forced to match whatever
# was assigned in the FIRST occurrence.
#
# Example: If row 3 has company_name="Globex" with
# industry="Tech" and employees=20, then row 47 with
# company_name="Globex" will also get industry="Tech"
# and employees=20.
# ═══════════════════════════════════════════════════════

# Each rule: (anchor_keywords, bound_keywords)
# anchor_keywords: substrings that identify the anchor column
# bound_keywords:  substrings that identify columns bound to that anchor
_CONSISTENCY_RULES = [
    # Company anchor → industry, sector, employees, revenue, country, location, address
    (
        ["company", "employer", "firm"],
        ["industry", "sector", "employee", "revenue", "country", "location",
         "address", "city", "state", "headquarters", "hq", "founded", "size",
         "annual_revenue", "market_cap", "num_employees"]
    ),
    # Bank anchor → branch, swift, bic, iban_prefix, country, location
    (
        ["bank_name", "bank"],
        ["branch", "swift", "bic", "country", "location", "city"]
    ),
    # Merchant anchor → merchant_category, location
    (
        ["merchant_name", "merchant"],
        ["merchant_category", "category", "merchant_type"]
    ),
    # Person (full_name or first+last combo) → phone, address, city, state, department
    (
        ["full_name"],
        ["phone", "mobile", "address", "city", "state", "department", "title",
         "job_title", "position"]
    ),
    # Ticker/symbol anchor → exchange, company, sector
    (
        ["ticker", "symbol"],
        ["exchange", "company", "sector", "industry"]
    ),
]


def _enforce_entity_consistency(columns: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """
    For each consistency rule, find matching anchor and bound columns
    in the dataset. Build a cache keyed by anchor values, and rewrite
    bound columns so repeated anchor values always get the same
    bound attributes.
    """
    col_names = list(columns.keys())
    n_rows = len(next(iter(columns.values()))) if columns else 0
    if n_rows == 0:
        return columns

    for anchor_keywords, bound_keywords in _CONSISTENCY_RULES:
        # Find anchor column(s) — take the first match
        anchor_col = None
        for cn in col_names:
            cn_lower = cn.lower()
            # Skip columns that are IDs, dates, or internal
            if cn.startswith("_") or "_id" in cn_lower:
                continue
            # "account" columns are not anchors for bank rules
            if "account" in cn_lower:
                continue
            if any(kw in cn_lower for kw in anchor_keywords):
                # Make sure this column is a string/object column
                if columns[cn].dtype == object:
                    anchor_col = cn
                    break

        if anchor_col is None:
            continue

        # Find bound columns — all columns matching any bound keyword
        bound_cols = []
        for cn in col_names:
            if cn == anchor_col or cn.startswith("_"):
                continue
            cn_lower = cn.lower()
            if any(kw in cn_lower for kw in bound_keywords):
                bound_cols.append(cn)

        if not bound_cols:
            continue

        # Build the cache: anchor_value → {bound_col: value}
        cache: Dict[str, Dict[str, Any]] = {}

        for i in range(n_rows):
            anchor_val = str(columns[anchor_col][i])
            if not anchor_val or anchor_val in ("nan", "None", ""):
                continue

            if anchor_val not in cache:
                # First occurrence — cache ALL bound values
                cache[anchor_val] = {}
                for bc in bound_cols:
                    cache[anchor_val][bc] = columns[bc][i]
            else:
                # Subsequent occurrence — OVERWRITE with cached values
                for bc in bound_cols:
                    if bc in cache[anchor_val]:
                        columns[bc][i] = cache[anchor_val][bc]

    return columns


def _stable_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:16], 16)
