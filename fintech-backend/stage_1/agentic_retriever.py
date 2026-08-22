import os
import ssl
import certifi
import httpx
from groq import Groq

# =====================================================
# AGENTIC RETRIEVER — Auto-expansion for failed prompts
# =====================================================
# Intercepts prompts that scored below 0.30 threshold.
# Reaches out to an LLM to quickly convert slang, tickers,
# or niche terminology into standard financial keywords.
# =====================================================

from typing import Tuple
from functools import lru_cache

@lru_cache(maxsize=1000)
def expand_prompt_agentically(raw_prompt: str) -> Tuple[str, bool]:
    """
    Acts as a 'brain' when the static keyword engine fails.
    Takes an obscure prompt (e.g. "Simulate TSLA buys") 
    and returns an expanded string of relevant financial terms.
    If it fails or timeouts, it gracefully returns the original.
    """
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return raw_prompt, True
            
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        http_client = httpx.Client(verify=ssl_context, timeout=3.0)
        client = Groq(api_key=api_key, http_client=http_client)

        system_msg = (
            "You are an agentic retrieval system for a behavioral synthetic data engine. "
            "Your job is ONLY to perform Query Expansion. "
            "Given a messy or obscure user prompt, identify the implicit financial domains "
            "and ANY relevant financial synonyms, entity types, or keywords related to it. "
            "The supported financial domains are: "
            "Loans, Credit Cards, Payroll, SaaS Billing, Investments, Insurance Claims, "
            "Bank Account Statements, Wire Transfers, ATM Withdrawals, Mortgage Records, "
            "Buy Now Pay Later (BNPL), KYC Records, AML Transaction Alerts, "
            "Crypto Trading, Forex Transactions, Options Trading, "
            "Expense Reports, Tax/W2 Records, P&L Statements, Invoice Financing. "
            "DO NOT write a conversational response. ONLY return a space-separated string "
            "of 10-15 highly relevant financial keywords that our NLP system can score. "
            "CRITICAL: If the user's prompt is completely random gibberish, nonsensical, "
            "or lacks any implied financial intent, you MUST return exactly the word: GARBAGE"
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": raw_prompt}
            ],
            temperature=0.0,
            max_completion_tokens=50,
        )

        expanded_terms = response.choices[0].message.content.strip()
        
        # Shortcircuit if the LLM detects absolute garbage
        if expanded_terms == "GARBAGE" or "GARBAGE" in expanded_terms:
            return raw_prompt, False
        
        return f"{raw_prompt} {expanded_terms}", False
        
    except Exception as e:
        # Failsafe: If Groq timeouts, is offline, or errors, degrade gracefully
        print(f"[Agentic Fallback Error] {str(e)}")
        return raw_prompt, True
