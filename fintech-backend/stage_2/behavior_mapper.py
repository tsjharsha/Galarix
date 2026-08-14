# =====================================================
# BEHAVIOR MAPPER
# =====================================================
# Maps the explicit Intent from the DataContract into
# the concrete mathematical multipliers.
# =====================================================

from typing import Dict, Any
from stage_2.tensor_engine import calculate_continuous_tensors

def map_behavior(prompt: str, intent: Dict[str, Any]) -> Dict[str, float]:
    """
    Takes the raw prompt and the enriched intent block
    and returns a unique set of continuous mathematical tensors.
    """
    return calculate_continuous_tensors(prompt, intent)

