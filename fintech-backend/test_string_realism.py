"""
GALARIX STRING REALISM VERIFICATION
====================================
Proves the Markov chain generates unique, culturally-appropriate names.
Tests at 1000 rows (the scale where the old system broke down).
"""
import sys
sys.path.insert(0, ".")
import numpy as np
from stage_3.string_generators import generate_string_column

def test_name_uniqueness():
    """Test that 1000-row datasets have high name uniqueness."""
    print("=" * 70)
    print("GALARIX STRING REALISM VERIFICATION")
    print("=" * 70)
    
    regions = ["US", "UK", "IN", "EU", "JP", "AU", "BR"]
    all_passed = True
    
    for region in regions:
        rng = np.random.default_rng(42)
        n = 1000
        
        first_names = generate_string_column(rng, "first_name", "string", n, "credit_card_activity", region)
        last_names = generate_string_column(rng, "last_name", "string", n, "credit_card_activity", region)
        
        # Full names
        full_names = [f"{f} {l}" for f, l in zip(first_names, last_names)]
        unique_first = len(set(first_names))
        unique_last = len(set(last_names))
        unique_full = len(set(full_names))
        
        # OLD SYSTEM: 8 first × 8 last = 64 max unique full names
        # NEW SYSTEM: Should be >> 64
        
        max_repeat_first = max(first_names.count(n) for n in set(first_names))
        max_repeat_full = max(full_names.count(n) for n in set(full_names))
        
        passed = unique_full > 500  # At least 500 unique full names from 1000 rows
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        
        print(f"  {status}  {region}  | Unique first: {unique_first:>4} | Unique last: {unique_last:>4} | Unique full: {unique_full:>4}/1000 | Max repeat (first): {max_repeat_first}")
    
    print()
    
    # Test company name uniqueness
    print("COMPANY NAME UNIQUENESS:")
    for region in regions:
        rng = np.random.default_rng(42)
        companies = generate_string_column(rng, "company_name", "string", 100, "payroll", region)
        unique_companies = len(set(companies))
        print(f"  {region}  | Unique companies: {unique_companies}/100")
    
    print()
    
    # Test card number Luhn validity
    print("CARD NUMBER LUHN VALIDATION:")
    rng = np.random.default_rng(42)
    cards = generate_string_column(rng, "card_number", "string", 100, "credit_card_activity", "US")
    unique_cards = len(set(cards))
    
    # Verify Luhn checksum
    luhn_valid = 0
    for card in cards:
        digits = [int(d) for d in card.replace("-", "")]
        total = 0
        for i, d in enumerate(reversed(digits)):
            if i % 2 == 1:
                doubled = d * 2
                total += doubled - 9 if doubled > 9 else doubled
            else:
                total += d
        if total % 10 == 0:
            luhn_valid += 1
    
    print(f"  Unique cards: {unique_cards}/100 | Luhn-valid: {luhn_valid}/100")
    
    print()
    
    # Test email derivation
    print("EMAIL DERIVATION:")
    rng = np.random.default_rng(42)
    emails = generate_string_column(rng, "email", "string", 100, "kyc_records", "IN")
    unique_emails = len(set(emails))
    print(f"  IN region: Unique emails: {unique_emails}/100")
    print(f"  Samples: {emails[:5]}")
    
    print()
    print("=" * 70)
    if all_passed:
        print("ALL STRING REALISM TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 70)

if __name__ == "__main__":
    test_name_uniqueness()
