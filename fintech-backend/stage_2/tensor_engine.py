# =====================================================
# TENSOR ENGINE (Continuous Multipliers)
# =====================================================
# This engine eliminates discrete "buckets" for Scale and Risk.
# Instead, it uses a deterministic Hash-Based derivation to
# calculate unique, continuous floating-point tensors for
# every single unique prompt.
# =====================================================

import hashlib
from typing import Dict, Any

# Base multiplier centroids for continuous mapping
# These act as the "centers of mass" for our continuous tensors
SCALE_CENTROIDS = {
    "tiny": 0.1,
    "small": 0.5,
    "medium": 1.0,
    "large": 2.5,
    "massive": 10.0
}

RISK_CENTROIDS = {
    "low": 0.5,
    "medium": 1.0,
    "high": 2.5,
    "extreme": 5.0
}

def calculate_continuous_tensors(prompt: str, intent: Dict[str, Any]) -> Dict[str, float]:
    """
    Computes a unique set of continuous multipliers for a prompt.
    
    Logic:
    1. Resolve the base multiplier from the intent centroid.
    2. Generate a 'Fluctuation Factor' using SHA-256(prompt).
    3. Apply the fluctuation (±10%) to the centroid to create 
       a unique, personalized statistical signature.
    """
    # 1. Deterministic Prompt Hash (0.0 to 1.0)
    prompt_seed = hashlib.sha256(prompt.encode()).hexdigest()
    # Use the first 8 characters to get a stable float
    hash_int = int(prompt_seed[:8], 16)
    normalized_hash = hash_int / 0xFFFFFFFF 
    
    # Fluctuation range: 0.9 to 1.1 (±10%)
    # This ensures "large" prompts are all unique but stay in the "large" neighborhood.
    fluctuation = 0.9 + (normalized_hash * 0.2)
    
    # 2. Extract Intent Centroids
    risk_level = intent.get("risk", "medium")
    scale_level = intent.get("scale", "medium")
    
    base_m_mu = SCALE_CENTROIDS.get(scale_level, 1.0)
    base_m_var = RISK_CENTROIDS.get(risk_level, 1.0)
    
    # 3. Compute continuous tensors
    # Complexity Note: We also shift volume slightly by a different hash slice
    vol_hash = int(prompt_seed[8:16], 16) / 0xFFFFFFFF
    vol_fluctuation = 0.8 + (vol_hash * 0.4) # ±20% for volume
    
    # Base volume multipliers from behavior_config (to maintain compatibility)
    volume_base = 1.0
    if scale_level == "tiny": volume_base = 0.01
    elif scale_level == "small": volume_base = 0.1
    elif scale_level == "large": volume_base = 10.0
    elif scale_level == "massive": volume_base = 100.0
    
    # Final Continuous Tensors
    continuous_behavior = {
        "mean_multiplier": round(base_m_mu * fluctuation, 6),
        "variance_multiplier": round(base_m_var * fluctuation, 6),
        "volume_multiplier": round(volume_base * vol_fluctuation, 6),
        "anomaly_rate": round(min(0.5, (base_m_var * 0.05) * fluctuation), 4),
        "tensor_signature": prompt_seed[:16] # For traceability and audit
    }
    
    return continuous_behavior
