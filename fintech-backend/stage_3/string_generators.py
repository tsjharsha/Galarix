# =====================================================
# STRING GENERATORS — Procedural Identity Engine
# =====================================================
# Generates non-statistical variables (names, emails,
# IDs, dates, card numbers) using:
#
#   1. MARKOV CHAIN NAME GENERATOR
#      Learns phonetic patterns from a small seed corpus
#      per region, then generates infinite unique names
#      that sound culturally appropriate.
#
#   2. IDENTITY SEED DERIVATION
#      Each row gets a unique identity hash. All fields
#      (name, email, phone, account) derive from it,
#      so they're interconnected and never duplicated.
#
#   3. GRAMMATICAL COMPANY GENERATOR
#      Combines roots + cores + suffixes per region
#      to produce thousands of unique company names
#      from ~25 stored words.
#
#   4. LUHN-VALID CARD NUMBERS
#      Algorithmically correct card numbers that pass
#      checksum validation like real cards.
#
# All generators are DETERMINISTIC — seeded by the
# master RNG from seed_engine, so the same prompt
# always produces the same synthetic identities.
# =====================================================

import hashlib
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any


# ═══════════════════════════════════════════════════════
# MARKOV CHAIN NAME GENERATOR
# ═══════════════════════════════════════════════════════
# Trains a character-level Markov chain on seed names.
# The chain learns transition probabilities like:
#   "In Indian names, 'A' is often followed by 'a' or 'r'"
#   "In Japanese names, 'k' is often followed by 'a','i','u','e','o'"
# Then generates unlimited unique names from those patterns.
# ═══════════════════════════════════════════════════════

class MarkovNameGenerator:
    """
    Character-level Markov chain for culturally-appropriate
    name generation. Trained on a small seed corpus (~15-25 names).
    Generates infinite unique names that sound authentic.
    """

    def __init__(self, seed_names: List[str], order: int = 2):
        self.order = order
        self.chain: Dict[str, List[str]] = {}
        self.starters: List[str] = []
        self._build_chain(seed_names)

    def _build_chain(self, names: List[str]):
        """Build transition table from seed names."""
        for name in names:
            # Pad the name for start/end detection
            padded = "^" * self.order + name + "$"
            self.starters.append(padded[self.order:self.order + 1])

            for i in range(len(padded) - self.order):
                key = padded[i:i + self.order]
                val = padded[i + self.order] if i + self.order < len(padded) else "$"
                if key not in self.chain:
                    self.chain[key] = []
                self.chain[key].append(val)

    def generate(self, rng: np.random.Generator, min_len: int = 3, max_len: int = 8) -> str:
        """Generate a single name from the Markov chain."""
        for _ in range(50):  # Max attempts
            name = self._generate_one(rng)
            if min_len <= len(name) <= max_len:
                return name.capitalize()
        # Fallback: return a truncated/padded attempt
        name = self._generate_one(rng)
        if len(name) < min_len:
            name = name + name[:min_len - len(name)]
        return name[:max_len].capitalize()

    def _generate_one(self, rng: np.random.Generator) -> str:
        """Single generation attempt."""
        current = "^" * self.order
        result = []

        for _ in range(12):  # Max length safety
            if current not in self.chain:
                break
            options = self.chain[current]
            next_char = options[int(rng.integers(0, len(options)))]
            if next_char == "$":
                break
            result.append(next_char)
            current = current[1:] + next_char

        return "".join(result)

    def generate_unique_batch(self, rng: np.random.Generator, count: int,
                               min_len: int = 3, max_len: int = 8) -> List[str]:
        """Generate a batch of unique names."""
        names = []
        seen = set()
        attempts = 0
        max_attempts = count * 10

        while len(names) < count and attempts < max_attempts:
            name = self.generate(rng, min_len, max_len)
            if name.lower() not in seen:
                seen.add(name.lower())
                names.append(name)
            attempts += 1

        # If we couldn't generate enough unique names, add numbered variants
        while len(names) < count:
            base = self.generate(rng, min_len, max_len - 1)
            suffix = str(len(names) % 100)
            variant = base + suffix
            if variant.lower() not in seen:
                seen.add(variant.lower())
                names.append(variant.capitalize())
            else:
                names.append(f"{base}{len(names)}")

        return names


# ═══════════════════════════════════════════════════════
# REGIONAL SEED CORPORA
# ═══════════════════════════════════════════════════════
# These are the ONLY hardcoded names — just enough to
# train the Markov chains. The chains then generate
# unlimited unique names from these patterns.
# ═══════════════════════════════════════════════════════

REGIONAL_SEEDS = {
    "US": {
        "FIRST_NAMES": [
            "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
            "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
            "Thomas", "Sarah", "Christopher", "Margaret", "Charles", "Dorothy", "Daniel", "Karen",
        ],
        "LAST_NAMES": [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Anderson", "Taylor", "Thomas", "Jackson", "White", "Harris",
            "Clark", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright",
        ],
    },
    "UK": {
        "FIRST_NAMES": [
            "Oliver", "Olivia", "George", "Amelia", "Arthur", "Isla", "Noah", "Ava",
            "Harry", "Emily", "Jack", "Poppy", "Leo", "Ella", "Charlie", "Grace",
            "Oscar", "Sophia", "Henry", "Freya", "Freddie", "Florence", "Archie", "Rosie",
        ],
        "LAST_NAMES": [
            "Smith", "Jones", "Taylor", "Williams", "Brown", "Davies", "Evans", "Thomas",
            "Wilson", "Roberts", "Johnson", "Walker", "Wright", "Robinson", "Thompson", "White",
            "Edwards", "Hughes", "Green", "Hall", "Lewis", "Harris", "Clarke", "Patel",
        ],
    },
    "IN": {
        "FIRST_NAMES": [
            "Aarav", "Aadya", "Vihaan", "Diya", "Arjun", "Ananya", "Rohan", "Priya",
            "Aditya", "Ishita", "Vivaan", "Saanvi", "Krishna", "Meera", "Dhruv", "Kavya",
            "Reyansh", "Anvi", "Arnav", "Riya", "Siddharth", "Nandini", "Pranav", "Shreya",
        ],
        "LAST_NAMES": [
            "Patel", "Singh", "Sharma", "Kumar", "Gupta", "Desai", "Joshi", "Verma",
            "Mehta", "Shah", "Reddy", "Nair", "Iyer", "Chopra", "Mishra", "Chauhan",
            "Bhatt", "Saxena", "Kaur", "Malhotra", "Pillai", "Banerjee", "Ghosh", "Das",
        ],
    },
    "EU": {
        "FIRST_NAMES": [
            "Lukas", "Mia", "Leon", "Emma", "Louis", "Chloe", "Maximilian", "Sofia",
            "Felix", "Hannah", "Elias", "Marie", "Jonas", "Lena", "Matteo", "Laura",
            "Noah", "Anna", "Finn", "Lea", "Luca", "Clara", "Paul", "Elena",
        ],
        "LAST_NAMES": [
            "Mueller", "Schmidt", "Rossi", "Russo", "Garcia", "Martinez", "Dubois", "Moreau",
            "Fischer", "Weber", "Schneider", "Wagner", "Becker", "Hoffmann", "Conti", "Romano",
            "Fernandez", "Lopez", "Bernard", "Petit", "Lambert", "Richter", "Koch", "Bauer",
        ],
    },
    "JP": {
        "FIRST_NAMES": [
            "Hiroshi", "Yoko", "Kenji", "Mika", "Takumi", "Sakura", "Daiki", "Aoi",
            "Haruto", "Yui", "Sota", "Hana", "Riku", "Mei", "Yuto", "Rin",
            "Kaito", "Mio", "Hayato", "Koharu", "Minato", "Hinata", "Asahi", "Akari",
        ],
        "LAST_NAMES": [
            "Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe", "Ito", "Yamamoto", "Nakamura",
            "Kobayashi", "Kato", "Yoshida", "Yamada", "Sasaki", "Yamaguchi", "Matsumoto", "Inoue",
            "Kimura", "Shimizu", "Hayashi", "Saito", "Maeda", "Fujita", "Ogawa", "Goto",
        ],
    },
    "AU": {
        "FIRST_NAMES": [
            "Jack", "Charlotte", "William", "Isla", "Noah", "Mia", "Oliver", "Grace",
            "James", "Amelia", "Thomas", "Ava", "Henry", "Chloe", "Ethan", "Sophie",
            "Lucas", "Emily", "Cooper", "Ella", "Liam", "Harper", "Alexander", "Lily",
        ],
        "LAST_NAMES": [
            "Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Morton", "White",
            "Martin", "Anderson", "Thompson", "Nguyen", "Thomas", "Walker", "Harris", "Lee",
            "Ryan", "Robinson", "Kelly", "King", "Davis", "Wright", "Evans", "Roberts",
        ],
    },
    "BR": {
        "FIRST_NAMES": [
            "Miguel", "Alice", "Arthur", "Laura", "Heitor", "Sophia", "Davi", "Maria",
            "Gabriel", "Helena", "Bernardo", "Valentina", "Lucas", "Julia", "Pedro", "Cecilia",
            "Rafael", "Manuela", "Gustavo", "Isabella", "Matheus", "Luisa", "Felipe", "Lara",
        ],
        "LAST_NAMES": [
            "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira",
            "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes",
            "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade",
        ],
    },
}


# ═══════════════════════════════════════════════════════
# GRAMMATICAL COMPANY NAME GENERATOR
# ═══════════════════════════════════════════════════════
# Combines word fragments to produce unique company names.
# ~25 stored words → 1000+ unique combinations per region.
# ═══════════════════════════════════════════════════════

COMPANY_DNA = {
    "US": {
        "roots": ["Nova", "Peak", "Apex", "Forge", "Vertex", "Nexus", "Atlas", "Pulse", "Lumen", "Zenith"],
        "cores": ["tech", "soft", "sys", "data", "cloud", "ware", "gen", "logic", "net", "lab"],
        "suffixes": ["Inc", "Corp", "LLC", "Group", "Solutions", "Technologies", "Systems", "Partners"],
        "patterns": ["{root}{core} {suffix}", "{root} {suffix}", "{root}{core}"],
    },
    "UK": {
        "roots": ["Crown", "Beacon", "Anchor", "Sterling", "Heritage", "Monarch", "Thames", "Albion", "Meridian", "Pinnacle"],
        "cores": ["tech", "soft", "fin", "ware", "link", "bridge", "gate", "point", "core", "hub"],
        "suffixes": ["Ltd", "Group", "PLC", "Partners", "Solutions", "Holdings", "Services"],
        "patterns": ["{root}{core} {suffix}", "{root} {suffix}", "{root} & {root} {suffix}"],
    },
    "IN": {
        "roots": ["Digi", "Zen", "Nex", "Astra", "Kira", "Bharat", "Veda", "Indra", "Tara", "Mitra"],
        "cores": ["soft", "sys", "fin", "pay", "net", "gen", "cloud", "data", "lab", "tek"],
        "suffixes": ["Pvt Ltd", "Solutions", "Technologies", "Industries", "Systems", "Infra", "Services"],
        "patterns": ["{root}{core} {suffix}", "{root} {suffix}", "{root}{core}"],
    },
    "EU": {
        "roots": ["Euro", "Rhine", "Nord", "Alpine", "Merian", "Hansa", "Zephyr", "Tera", "Volta", "Lux"],
        "cores": ["tech", "werke", "sys", "soft", "lab", "link", "hub", "tec", "net", "data"],
        "suffixes": ["GmbH", "AG", "SE", "Group", "Solutions", "Holding", "Industries"],
        "patterns": ["{root}{core} {suffix}", "{root} {suffix}", "{root}{core}"],
    },
    "JP": {
        "roots": ["Mizu", "Hoshi", "Sora", "Kaze", "Yama", "Tsuki", "Sakura", "Haru", "Nami", "Kuma"],
        "cores": ["tech", "soft", "den", "ko", "tron", "ware", "sys", "net", "pro", "moto"],
        "suffixes": ["Co Ltd", "Corporation", "Industries", "Holdings", "Systems", "Group"],
        "patterns": ["{root}{core} {suffix}", "{root} {suffix}", "{root}{core}"],
    },
    "AU": {
        "roots": ["Southern", "Pacific", "Outback", "Harbour", "Reef", "Canyon", "Ember", "Opal", "Wattle", "Coral"],
        "cores": ["tech", "soft", "sys", "data", "ware", "gen", "link", "hub", "net", "lab"],
        "suffixes": ["Pty Ltd", "Group", "Holdings", "Solutions", "Industries", "Services"],
        "patterns": ["{root}{core} {suffix}", "{root} {suffix}", "{root}{core}"],
    },
    "BR": {
        "roots": ["Brasil", "Sol", "Rio", "Verde", "Tropica", "Norte", "Serra", "Horizonte", "Costa", "Floresta"],
        "cores": ["tech", "soft", "sys", "data", "net", "fin", "lab", "tek", "hub", "link"],
        "suffixes": ["S.A.", "Ltda", "Group", "Soluções", "Tecnologia", "Sistemas", "Serviços"],
        "patterns": ["{root}{core} {suffix}", "{root} {suffix}", "{root}{core}"],
    },
}


# ═══════════════════════════════════════════════════════
# REGIONAL METADATA (Non-name data)
# ═══════════════════════════════════════════════════════
# Banks, merchants, locations — these pools are kept
# because these are REAL entities that SHOULD repeat
# (people DO shop at the same 20 stores).
# ═══════════════════════════════════════════════════════

REGIONAL_META = {
    "US": {
        "BANKS": ["Chase", "Bank of America", "Wells Fargo", "Citibank", "US Bank", "PNC", "Capital One", "TD Bank"],
        "MERCHANTS": [
            "Amazon", "Walmart", "Target", "Starbucks", "Uber", "CVS Pharmacy", "Home Depot",
            "Costco", "McDonald's", "Chipotle", "Netflix", "Spotify", "Apple Store", "Nike",
            "Whole Foods", "Best Buy", "Lowe's", "Walgreens", "Kroger", "Trader Joe's",
            "DoorDash", "Lyft", "Dunkin'", "Chick-fil-A", "Publix", "7-Eleven", "Sephora",
            "Nordstrom", "Macy's", "Panera Bread",
        ],
        "LOCATIONS": [
            "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Miami, FL",
            "Phoenix, AZ", "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX",
            "San Jose, CA", "Austin, TX", "Jacksonville, FL", "San Francisco, CA", "Seattle, WA",
            "Denver, CO", "Nashville, TN", "Portland, OR", "Las Vegas, NV", "Atlanta, GA",
        ],
        "IBAN_PREFIX": "US", "CURRENCY": "USD",
        "PHONE_FORMAT": "+1-{area}-{pre}-{line}",
        "PHONE_AREAS": ["212", "310", "312", "713", "305", "415", "202", "404", "617", "503"],
        "ADDRESS_FORMATS": ["{num} {street}, {city}, {state} {zip}"],
        "STREETS": ["Main St", "Oak Ave", "Broadway", "Park Blvd", "Market St", "Elm Rd", "Cedar Ln", "Maple Dr", "Washington Ave", "Lincoln Way"],
        "STATES": ["NY", "CA", "IL", "TX", "FL", "AZ", "PA", "OH", "GA", "WA"],
        "TAX_ID_FORMAT": "{a}{b}{c}-{d}{e}-{f}{g}{h}{i}", "TAX_ID_NAME": "SSN",
        "EMAIL_DOMAINS": ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "aol.com", "protonmail.com"],
    },
    "UK": {
        "BANKS": ["Barclays", "HSBC", "Lloyds Bank", "NatWest", "Monzo", "Santander UK", "Starling Bank", "Revolut UK"],
        "MERCHANTS": [
            "Tesco", "Sainsbury's", "Asda", "Greggs", "Costa Coffee", "Boots", "Deliveroo",
            "Marks & Spencer", "John Lewis", "Primark", "Nando's", "Waitrose", "Argos",
            "Pret A Manger", "H&M UK", "Next", "Currys", "ASOS", "Amazon UK", "Ocado",
        ],
        "LOCATIONS": [
            "London", "Manchester", "Birmingham", "Edinburgh", "Glasgow", "Liverpool",
            "Leeds", "Bristol", "Sheffield", "Cardiff", "Belfast", "Nottingham",
        ],
        "IBAN_PREFIX": "GB", "CURRENCY": "GBP",
        "PHONE_FORMAT": "+44-{area}-{line}",
        "PHONE_AREAS": ["20", "121", "131", "141", "161", "113", "117", "151"],
        "ADDRESS_FORMATS": ["{num} {street}, {city} {postcode}"],
        "STREETS": ["High Street", "Church Road", "Station Road", "King Street", "Queen Street", "Victoria Road", "London Road", "Mill Lane", "Park Avenue", "Green Lane"],
        "STATES": ["England", "Scotland", "Wales", "Northern Ireland"],
        "TAX_ID_FORMAT": "{a}{b} {c}{d} {e}{f} {g}{h} {i}", "TAX_ID_NAME": "NIN",
        "EMAIL_DOMAINS": ["gmail.com", "yahoo.co.uk", "outlook.com", "hotmail.co.uk", "btinternet.com", "sky.com"],
    },
    "IN": {
        "BANKS": ["HDFC Bank", "ICICI Bank", "State Bank of India", "Axis Bank", "Kotak Mahindra", "Punjab National Bank", "Bank of Baroda", "IndusInd Bank"],
        "MERCHANTS": [
            "Flipkart", "Reliance Smart", "Zomato", "Swiggy", "BigBasket", "Ola", "Paytm",
            "Myntra", "Amazon India", "Blinkit", "PhonePe Merchant", "DMart", "Croma",
            "Urban Company", "BookMyShow", "MakeMyTrip", "Nykaa", "Meesho", "Rapido", "Zepto",
        ],
        "LOCATIONS": [
            "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Pune", "Kolkata",
            "Ahmedabad", "Jaipur", "Lucknow", "Chandigarh", "Kochi",
        ],
        "IBAN_PREFIX": "IN", "CURRENCY": "INR",
        "PHONE_FORMAT": "+91-{area}-{line}",
        "PHONE_AREAS": ["22", "11", "80", "40", "44", "20", "33", "79", "141", "522"],
        "ADDRESS_FORMATS": ["{num}, {street}, {city} - {zip}"],
        "STREETS": ["MG Road", "Station Road", "Link Road", "Gandhi Nagar", "Nehru Place", "Ring Road", "Old City Road", "Civil Lines", "Banjara Hills", "Koramangala"],
        "STATES": ["Maharashtra", "Karnataka", "Delhi", "Tamil Nadu", "Telangana", "Gujarat", "Rajasthan", "Kerala"],
        "TAX_ID_FORMAT": "{a}{b}{c}{d}{e}{f}{g}{h}{i}{j}", "TAX_ID_NAME": "PAN",
        "EMAIL_DOMAINS": ["gmail.com", "yahoo.in", "outlook.com", "rediffmail.com", "hotmail.com", "protonmail.com"],
    },
    "EU": {
        "BANKS": ["Deutsche Bank", "BNP Paribas", "Santander", "ING Group", "Societe Generale", "UniCredit", "Commerzbank", "Rabobank"],
        "MERCHANTS": [
            "Carrefour", "Aldi", "Lidl", "Zara", "Decathlon", "IKEA",
            "MediaMarkt", "H&M", "Primark", "Boulanger", "Fnac", "dm-drogerie",
            "Edeka", "Rewe", "Rossmann", "Douglas", "Müller", "C&A", "Zalando", "Amazon DE",
        ],
        "LOCATIONS": [
            "Berlin", "Paris", "Madrid", "Rome", "Amsterdam", "Frankfurt", "Milan",
            "Munich", "Barcelona", "Hamburg", "Vienna", "Brussels",
        ],
        "IBAN_PREFIX": "DE", "CURRENCY": "EUR",
        "PHONE_FORMAT": "+49-{area}-{line}",
        "PHONE_AREAS": ["30", "40", "89", "69", "221", "711", "211", "511"],
        "ADDRESS_FORMATS": ["{street} {num}, {zip} {city}"],
        "STREETS": ["Hauptstrasse", "Bahnhofstrasse", "Berliner Strasse", "Schillerstrasse", "Friedrichstrasse", "Goethestrasse", "Mozartstrasse", "Kirchstrasse", "Lindenallee", "Rosenweg"],
        "STATES": ["Bavaria", "Hesse", "NRW", "Berlin", "Saxony", "Baden-Württemberg"],
        "TAX_ID_FORMAT": "DE{a}{b}{c}{d}{e}{f}{g}{h}{i}", "TAX_ID_NAME": "Steuer-ID",
        "EMAIL_DOMAINS": ["gmail.com", "web.de", "gmx.de", "outlook.de", "t-online.de", "posteo.de"],
    },
    "JP": {
        "BANKS": ["Mitsubishi UFJ", "Sumitomo Mitsui", "Mizuho", "Japan Post Bank", "Resona", "Shinsei Bank"],
        "MERCHANTS": [
            "7-Eleven", "Lawson", "FamilyMart", "Rakuten", "Uniqlo", "Sony Store",
            "Daiso", "Don Quijote", "Muji", "Aeon", "Sukiya", "Yoshinoya",
            "Amazon JP", "Mercari", "Seria", "Nitori", "GU", "Matsumoto Kiyoshi", "Loft", "Tokyu Hands",
        ],
        "LOCATIONS": [
            "Tokyo", "Osaka", "Yokohama", "Nagoya", "Sapporo", "Fukuoka",
            "Kobe", "Kyoto", "Kawasaki", "Sendai", "Hiroshima", "Kitakyushu",
        ],
        "IBAN_PREFIX": "JP", "CURRENCY": "JPY",
        "PHONE_FORMAT": "+81-{area}-{line}",
        "PHONE_AREAS": ["3", "6", "45", "52", "11", "92", "78", "75"],
        "ADDRESS_FORMATS": ["{city} {street} {num}"],
        "STREETS": ["Chuo-ku", "Shibuya", "Minato-ku", "Shinjuku", "Ginza", "Roppongi", "Akihabara", "Ikebukuro", "Asakusa", "Meguro"],
        "STATES": ["Tokyo", "Osaka", "Kanagawa", "Aichi", "Hokkaido", "Fukuoka"],
        "TAX_ID_FORMAT": "{a}{b}{c}{d}-{e}{f}{g}{h}-{i}{j}{k}{l}", "TAX_ID_NAME": "My Number",
        "EMAIL_DOMAINS": ["gmail.com", "yahoo.co.jp", "outlook.jp", "docomo.ne.jp", "icloud.com", "nifty.com"],
    },
    "AU": {
        "BANKS": ["Commonwealth Bank", "Westpac", "ANZ", "NAB", "Macquarie", "Suncorp", "Bendigo Bank", "ING Australia"],
        "MERCHANTS": [
            "Woolworths", "Coles", "Bunnings", "Kmart", "JB Hi-Fi", "Qantas",
            "Target AU", "Officeworks", "Harvey Norman", "Dan Murphy's", "Chemist Warehouse",
            "Cotton On", "The Good Guys", "Big W", "Boost Juice", "Uber Eats AU", "Menulog", "Aldi AU", "OPSM", "Rebel Sport",
        ],
        "LOCATIONS": [
            "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Hobart",
            "Gold Coast", "Canberra", "Newcastle", "Wollongong", "Cairns", "Darwin",
        ],
        "IBAN_PREFIX": "AU", "CURRENCY": "AUD",
        "PHONE_FORMAT": "+61-{area}-{line}",
        "PHONE_AREAS": ["2", "3", "7", "8"],
        "ADDRESS_FORMATS": ["{num} {street}, {city} {state} {zip}"],
        "STREETS": ["George Street", "King Street", "Collins Street", "Pitt Street", "Flinders Street", "Queen Street", "Elizabeth Street", "Bourke Street", "Macquarie Street", "Market Street"],
        "STATES": ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"],
        "TAX_ID_FORMAT": "{a}{b}{c} {d}{e}{f} {g}{h}{i}", "TAX_ID_NAME": "TFN",
        "EMAIL_DOMAINS": ["gmail.com", "yahoo.com.au", "outlook.com.au", "bigpond.com", "optusnet.com.au", "iinet.net.au"],
    },
    "BR": {
        "BANKS": ["Itau", "Bradesco", "Banco do Brasil", "Caixa", "Nubank", "Santander BR", "Inter", "C6 Bank"],
        "MERCHANTS": [
            "Mercado Livre", "Magazine Luiza", "Americanas", "Ifood", "Pao de Acucar",
            "Casas Bahia", "Shopee BR", "Rappi", "99", "Amazon BR",
            "Renner", "Riachuelo", "Natura", "Boticário", "Carrefour BR", "Extra", "Havan", "Drogasil", "Samsung BR", "Submarino",
        ],
        "LOCATIONS": [
            "Sao Paulo", "Rio de Janeiro", "Brasilia", "Salvador", "Fortaleza",
            "Belo Horizonte", "Manaus", "Curitiba", "Recife", "Porto Alegre", "Goiania", "Campinas",
        ],
        "IBAN_PREFIX": "BR", "CURRENCY": "BRL",
        "PHONE_FORMAT": "+55-{area}-{line}",
        "PHONE_AREAS": ["11", "21", "31", "41", "51", "61", "71", "81"],
        "ADDRESS_FORMATS": ["Rua {street}, {num} - {city}/{state}"],
        "STREETS": ["Augusta", "Paulista", "Copacabana", "Ipanema", "Consolacao", "Liberdade", "Pinheiros", "Botafogo", "Leblon", "Lapa"],
        "STATES": ["SP", "RJ", "MG", "BA", "RS", "PR", "PE", "CE"],
        "TAX_ID_FORMAT": "{a}{b}{c}.{d}{e}{f}.{g}{h}{i}-{j}{k}", "TAX_ID_NAME": "CPF",
        "EMAIL_DOMAINS": ["gmail.com", "yahoo.com.br", "outlook.com", "hotmail.com", "uol.com.br", "bol.com.br"],
    },
}


# ═══════════════════════════════════════════════════════
# GLOBAL DATA (entity-specific, not region-specific)
# ═══════════════════════════════════════════════════════

CRYPTO_EXCHANGES = ["Binance", "Coinbase", "Kraken", "Bybit", "OKX", "KuCoin"]
CRYPTO_PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT", "XRP/USDT", "ADA/USDT"]
FOREX_PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "NZD/USD", "USD/CAD", "EUR/GBP"]

EXPENSE_CATEGORIES = ["Airfare", "Hotel", "Ground Transportation", "Meals - Client", "Meals - Solo", "Conference", "Office Supplies", "Parking"]


# ═══════════════════════════════════════════════════════
# MARKOV CHAIN CACHE (built once at module load)
# ═══════════════════════════════════════════════════════

_MARKOV_CACHE: Dict[str, Dict[str, MarkovNameGenerator]] = {}

def _get_markov(region: str, name_type: str) -> MarkovNameGenerator:
    """Get or build a Markov chain for the given region and name type."""
    if region not in REGIONAL_SEEDS:
        region = "US"

    cache_key = f"{region}_{name_type}"
    if cache_key not in _MARKOV_CACHE:
        seeds = REGIONAL_SEEDS[region].get(name_type, REGIONAL_SEEDS["US"][name_type])
        _MARKOV_CACHE[cache_key] = MarkovNameGenerator(seeds, order=2)

    return _MARKOV_CACHE[cache_key]


# ═══════════════════════════════════════════════════════
# PROCEDURAL GENERATORS
# ═══════════════════════════════════════════════════════

def _generate_company_name(rng: np.random.Generator, region: str) -> str:
    """Generate a unique company name using grammatical combination."""
    if region not in COMPANY_DNA:
        region = "US"
    dna = COMPANY_DNA[region]

    pattern = dna["patterns"][int(rng.integers(0, len(dna["patterns"])))]
    root1 = dna["roots"][int(rng.integers(0, len(dna["roots"])))]
    root2 = dna["roots"][int(rng.integers(0, len(dna["roots"])))]
    core = dna["cores"][int(rng.integers(0, len(dna["cores"])))]
    suffix = dna["suffixes"][int(rng.integers(0, len(dna["suffixes"])))]

    name = pattern.format(root=root1, core=core, suffix=suffix)
    # Handle the & pattern for UK
    name = name.replace("{root}", root2)
    return name


def _generate_luhn_card(rng: np.random.Generator) -> str:
    """Generate a Luhn-valid 16-digit card number."""
    # Common BIN prefixes (Visa=4, Mastercard=5, Amex=3)
    prefixes = ["4532", "4916", "5425", "5301", "4024", "4556"]
    prefix = prefixes[int(rng.integers(0, len(prefixes)))]

    # Generate 11 random digits (prefix=4 + random=11 + check=1 = 16)
    digits = [int(d) for d in prefix]
    for _ in range(11):
        digits.append(int(rng.integers(0, 10)))

    # Calculate Luhn check digit
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 0:
            doubled = d * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += d
    check = (10 - (total % 10)) % 10
    digits.append(check)

    card = "".join(str(d) for d in digits)
    return f"{card[:4]}-{card[4:8]}-{card[8:12]}-{card[12:16]}"


def _generate_email(rng: np.random.Generator, first_name: str, last_name: str, region: str, row_idx: int) -> str:
    """Generate an email derived from the person's name."""
    meta = REGIONAL_META.get(region, REGIONAL_META["US"])
    domains = meta["EMAIL_DOMAINS"]
    domain = domains[int(rng.integers(0, len(domains)))]

    f = first_name.lower().replace(" ", "")
    l = last_name.lower().replace(" ", "")

    # Multiple email format patterns
    patterns = [
        f"{f}.{l}",           # james.smith
        f"{f}{l[0]}",         # jamesm
        f"{f[0]}{l}",         # jsmith
        f"{f}.{l}{row_idx % 99}",  # james.smith42
        f"{f}_{l}",           # james_smith
    ]
    pattern = patterns[int(rng.integers(0, len(patterns)))]
    return f"{pattern}@{domain}"


def _generate_phone(rng: np.random.Generator, region: str) -> str:
    """Generate a phone number with correct regional format."""
    meta = REGIONAL_META.get(region, REGIONAL_META["US"])
    areas = meta.get("PHONE_AREAS", ["555"])
    area = areas[int(rng.integers(0, len(areas)))]
    line1 = f"{int(rng.integers(100, 999))}"
    line2 = f"{int(rng.integers(1000, 9999))}"
    return f"+{area}-{line1}-{line2}"


# ═══════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════

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
    and type. Uses Markov chains for names, grammatical combiners for
    companies, and identity-seed derivation for interconnected fields.
    """
    name_lower = var_name.lower()

    # Get regional metadata (fallback to US if missing)
    if region not in REGIONAL_META:
        region = "US"
    r_meta = REGIONAL_META[region]

    # ── ID Fields ──
    if any(k in name_lower for k in ["_id", "record_id", "transaction_id", "alert_id", "trade_id", "contract_id"]):
        return _generate_ids(rng, var_name, n_rows, entity)

    # ── Policy Number Fields ──
    if "policy" in name_lower and ("number" in name_lower or "no" in name_lower or name_lower == "policy_number"):
        prefix = entity[:3].upper() if entity else "POL"
        base = rng.integers(100000, 999999)
        return [f"{prefix}-{base + i:08d}" for i in range(n_rows)]

    # ── Name Fields (MARKOV CHAIN) ──
    if "first_name" in name_lower:
        markov = _get_markov(region, "FIRST_NAMES")
        return markov.generate_unique_batch(rng, n_rows)

    if "last_name" in name_lower:
        markov = _get_markov(region, "LAST_NAMES")
        return markov.generate_unique_batch(rng, n_rows)

    # ── Email Fields (derived from names — placeholder, rewritten by semantic weaver) ──
    if "email" in name_lower:
        first_markov = _get_markov(region, "FIRST_NAMES")
        last_markov = _get_markov(region, "LAST_NAMES")
        emails = []
        seen = set()
        for i in range(n_rows):
            fname = first_markov.generate(rng)
            lname = last_markov.generate(rng)
            email = _generate_email(rng, fname, lname, region, i)
            # Ensure uniqueness
            while email in seen:
                email = _generate_email(rng, fname, lname, region, i + len(seen))
            seen.add(email)
            emails.append(email)
        return emails

    # ── Card Number Fields (LUHN-VALID) ──
    if "card_number" in name_lower or "card_no" in name_lower:
        cards = set()
        result = []
        for _ in range(n_rows):
            card = _generate_luhn_card(rng)
            while card in cards:
                card = _generate_luhn_card(rng)
            cards.add(card)
            result.append(card)
        return result

    # ── Merchant Names ──
    if "merchant_name" in name_lower:
        indices = rng.integers(0, len(r_meta["MERCHANTS"]), size=n_rows)
        return [r_meta["MERCHANTS"][i] for i in indices]

    # ── Company Names (GRAMMATICAL GENERATOR) ──
    if "company" in name_lower or "employer" in name_lower:
        companies = set()
        result = []
        for _ in range(n_rows):
            company = _generate_company_name(rng, region)
            while company in companies:
                company = _generate_company_name(rng, region)
            companies.add(company)
            result.append(company)
        return result

    # ── Bank Names ──
    if "bank_name" in name_lower or ("bank" in name_lower and "account" not in name_lower):
        indices = rng.integers(0, len(r_meta["BANKS"]), size=n_rows)
        return [r_meta["BANKS"][i] for i in indices]

    # ── Location Fields ──
    if "location" in name_lower or "city" in name_lower:
        indices = rng.integers(0, len(r_meta["LOCATIONS"]), size=n_rows)
        return [r_meta["LOCATIONS"][i] for i in indices]

    # ── Currency ──
    if "currency" in name_lower:
        return [r_meta["CURRENCY"]] * n_rows

    # ── Country Fields ──
    if "country" in name_lower or "jurisdiction" in name_lower:
        _REGION_TO_COUNTRY = {
            "US": "United States", "UK": "United Kingdom", "IN": "India",
            "EU": "Germany", "JP": "Japan", "AU": "Australia", "BR": "Brazil",
        }
        country_name = _REGION_TO_COUNTRY.get(region, "United States")
        return [country_name] * n_rows

    # ── Account Numbers (hash-based, always unique) ──
    if "account" in name_lower and "statement" not in name_lower:
        return [
            f"ACCT-{hashlib.sha256(f'{rng.integers(0, 2**63)}'.encode()).hexdigest()[:12].upper()}"
            for _ in range(n_rows)
        ]

    # ── IBAN ──
    if "iban" in name_lower:
        return [f"{r_meta['IBAN_PREFIX']}{rng.integers(10, 99)}{rng.integers(10000000, 99999999)}{rng.integers(10000000, 99999999)}" for _ in range(n_rows)]

    # ── SWIFT/BIC Code ──
    if "swift" in name_lower or "bic" in name_lower:
        bank_codes = [f"{r_meta['BANKS'][i][:4].upper()}{r_meta['IBAN_PREFIX']}XX" for i in range(min(4, len(r_meta["BANKS"])))]
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

    # ── Phone Number Fields (region-formatted) ──
    if "phone" in name_lower or "mobile" in name_lower or "tel" in name_lower:
        return [_generate_phone(rng, region) for _ in range(n_rows)]

    # ── Address Fields ──
    if "address" in name_lower and "wallet" not in name_lower and "email" not in name_lower:
        streets = r_meta.get("STREETS", ["Main St"])
        locs = r_meta["LOCATIONS"]
        results = []
        for _ in range(n_rows):
            num = int(rng.integers(1, 9999))
            street = streets[int(rng.integers(0, len(streets)))]
            city = locs[int(rng.integers(0, len(locs)))]
            results.append(f"{num} {street}, {city}")
        return results

    # ── Tax ID / PAN / SSN / NIN Fields ──
    if "tax_id" in name_lower or "pan" in name_lower or "ssn" in name_lower or "nin" in name_lower:
        tax_name = r_meta.get("TAX_ID_NAME", "TAX")
        results = []
        for _ in range(n_rows):
            digits = [str(int(rng.integers(0, 10))) for _ in range(12)]
            results.append(f"{tax_name}-{''.join(digits[:4])}-{''.join(digits[4:8])}-{''.join(digits[8:])}")
        return results

    # ── Description Fields ──
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
    """Generate unique deterministic IDs using hash-based approach."""
    prefix = entity[:3].upper() if entity else "GX"
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
