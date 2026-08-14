# =====================================================
# COVARIANCE ENGINE (Dynamic Correlations)
# =====================================================
# Injects multivariate relationship instructions into the
# statistical model. This ensures that columns are not 
# generated in isolation, but instead interact based on 
# financial ontology.
# =====================================================

import hashlib
from typing import Dict, Any, List

# Predefined Financial Ontology Relationships (The Monster Mapping)
CORE_RELATIONSHIPS = {
    ("income", "spending"): 0.75,
    ("salary", "expenditure"): 0.70,
    ("income", "credit_score"): 0.60,
    ("salary", "score"): 0.55,
    ("debt", "score"): -0.80,
    ("principal", "rate"): -0.40,  # High principal, often lower rate
    ("principal", "emi"): 0.95,    # Massive correlation
    ("rate", "score"): -0.60,      # High rate usually means lower score risk
    ("amount", "score"): -0.30,
    ("amount", "emi"): 0.90,
    ("age", "income"): 0.50,
    ("age", "salary"): 0.45,
    ("risk", "default"): 0.90,
    ("fraud", "score"): -0.70
}


def build_covariance_matrix(
    distributions: Dict[str, Any], 
    behavior: Dict[str, Any],
    variables: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Scans the available variables and builds a list of 
    directed correlation instructions for Stage 3.
    
    Returns a list of correlations:
    [{"var_a": "x", "var_b": "y", "coefficient": 0.85}]
    """
    correlations = []
    seen_pairs = set()  # Prevent duplicate A↔B / B↔A entries
    
    # Use the tensor signature to jitter the correlations
    signature = behavior.get("tensor_signature", "default")
    jitter_seed = int(hashlib.md5(signature.encode()).hexdigest()[:4], 16) / 65535
    jitter = (jitter_seed * 0.2) - 0.1 # ±0.1 jitter
    
    # Get all variable names (CRITICAL FIX: Use variables dict to include derived fields)
    if variables:
        var_names = list(variables.keys())
    else:
        var_names = list(distributions.keys())
    
    # Iterate through core relationships and check if both variables exist in this contract
    for (a_keyword, b_keyword), base_coeff in CORE_RELATIONSHIPS.items():
        # Find actual variable names that contain these keywords
        matches_a = [v for v in var_names if a_keyword in v.lower()]
        matches_b = [v for v in var_names if b_keyword in v.lower()]
        
        for var_a in matches_a:
            for var_b in matches_b:
                if var_a == var_b:
                    continue
                
                # Deduplicate: only keep one direction per pair
                pair_key = tuple(sorted([var_a, var_b]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                
                # Apply unique jitter to this prompt's correlation
                unique_coeff = round(max(-0.99, min(0.99, base_coeff + jitter)), 4)
                
                correlations.append({
                    "var_a": var_a,
                    "var_b": var_b,
                    "coefficient": unique_coeff,
                    "method": "pearson"
                })
                
    return correlations
