"""Quick test for Entity Consistency Cache."""
import sys
sys.path.insert(0, ".")
import numpy as np
from stage_3.string_generators import weave_semantic_strings

def test_company():
    cols = {
        "company_name": np.array(["Globex","Acme","Umbrella","Globex","Initech","Acme","Umbrella","Globex","Initech","Acme"], dtype=object),
        "industry": np.array(["Tech","Finance","Healthcare","Energy","Retail","Mfg","Pharma","Agri","Consult","Aero"], dtype=object),
        "num_employees": np.array([20,50,100,55,30,80,200,15,40,90], dtype=float),
        "transaction_id": np.array([f"TXN-{i}" for i in range(10)], dtype=object),
    }
    cols = weave_semantic_strings(cols)
    # Globex rows 0,3,7 should all match row 0
    assert cols["industry"][3] == "Tech" and cols["industry"][7] == "Tech"
    assert cols["num_employees"][3] == 20 and cols["num_employees"][7] == 20
    # Acme rows 1,5,9 should all match row 1
    assert cols["industry"][5] == "Finance" and cols["industry"][9] == "Finance"
    assert cols["num_employees"][5] == 50 and cols["num_employees"][9] == 50
    print("COMPANY CONSISTENCY: PASSED")

def test_bank():
    cols = {
        "bank_name": np.array(["Chase","HDFC","Barclays","HDFC","Chase","Barclays"], dtype=object),
        "location": np.array(["NY","Mumbai","London","Delhi","Chicago","Manchester"], dtype=object),
    }
    cols = weave_semantic_strings(cols)
    assert cols["location"][0] == cols["location"][4], "Chase"
    assert cols["location"][1] == cols["location"][3], "HDFC"
    assert cols["location"][2] == cols["location"][5], "Barclays"
    print("BANK CONSISTENCY: PASSED")

def test_merchant():
    cols = {
        "merchant_name": np.array(["Amazon","Starbucks","Walmart","Amazon","Starbucks"], dtype=object),
        "merchant_category": np.array(["Retail","Food","Retail","Entertainment","Travel"], dtype=object),
    }
    cols = weave_semantic_strings(cols)
    assert cols["merchant_category"][0] == cols["merchant_category"][3], "Amazon"
    assert cols["merchant_category"][1] == cols["merchant_category"][4], "Starbucks"
    print("MERCHANT CONSISTENCY: PASSED")

if __name__ == "__main__":
    test_company()
    test_bank()
    test_merchant()
    print("\nALL ENTITY CONSISTENCY TESTS PASSED!")
