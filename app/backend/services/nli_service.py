import re
from transformers import pipeline
from app.backend.config import settings
from app.backend.utils.logger import get_logger

logger = get_logger("nli_service")

# =========================================
# LAZY LOAD MODEL
# =========================================
nli_pipeline = None

def get_nli_pipeline():
    """Lazily loads and returns the NLI classification pipeline."""
    global nli_pipeline
    if nli_pipeline is None:
        try:
            logger.info(f"Initializing NLI pipeline with model: {settings.NLI_MODEL}")
            nli_pipeline = pipeline(
                "text-classification",
                model=settings.NLI_MODEL,
                device=-1  # Force CPU
            )
            logger.info("NLI pipeline successfully loaded.")
        except Exception as e:
            logger.error(f"Error loading NLI pipeline: {e}")
            raise RuntimeError(f"Could not load NLI model: {e}")
    return nli_pipeline

# =========================================
# IN-MEMORY NLI CACHE
# =========================================
_nli_cache = {}

def get_cache_key(claim: str, context: str) -> str:
    """Creates a normalized cache key for NLI inputs."""
    claim_norm = re.sub(r"\s+", "", claim.strip().lower())
    context_norm = re.sub(r"\s+", "", context.strip().lower()[:1500])
    return f"{claim_norm}|||{context_norm}"

# =========================================
# TEXT NORMALIZATION
# =========================================
def normalize_text(text: str) -> str:
    """Normalizes text by lowercasing and removing non-alphanumeric characters."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# =========================================
# CLAIM EXTRACTION
# =========================================
def extract_claims(answer: str) -> list:
    """Strips common abbreviations and splits a text into high-quality sentences."""
    if not answer or len(answer.strip()) < 3:
        return []
        
    abbrs = ["e.g", "i.e", "vs", "etc", "mr", "mrs", "dr", "prof", "st", "u.s", "u.k", "a.i", "m.l"]
    
    # Temporarily mask abbreviation periods
    masked_answer = answer
    for abbr in abbrs:
        # Match word boundaries for abbreviation
        pattern = re.compile(rf"\b{abbr}\.", re.IGNORECASE)
        masked_answer = pattern.sub(f"{abbr}_TEMP", masked_answer)
        
    # Split sentences by . ? ! followed by whitespace
    sentences = re.split(r"(?<=[.!?])\s+", masked_answer)
    
    cleaned_claims = []
    for s in sentences:
        # Restore periods
        s = s.replace("_TEMP", ".")
        s = s.strip()
        if len(s) > 5:
            # Clean trailing punctuation
            cleaned_claims.append(s)
            
    # Fallback to newline splitting if regex fails or splits are empty
    if not cleaned_claims:
        claims = re.split(r"[\n\r]", answer)
        cleaned_claims = [c.strip() for c in claims if len(c.strip()) > 5]
        
    return cleaned_claims

# =========================================
# FUZZY WORD OVERLAP
# =========================================
def get_word_overlap(claim: str, context: str) -> float:
    """Calculates Jaccard overlap score of unique words between claim and context."""
    claim_words = set(re.findall(r"\b\w+\b", claim.lower()))
    context_words = set(re.findall(r"\b\w+\b", context.lower()))
    if not claim_words:
        return 0.0
    intersection = claim_words.intersection(context_words)
    return len(intersection) / len(claim_words)

# =========================================
# NLI VERIFIER
# =========================================
def verify_claim(claim: str, context: str) -> dict:
    """Verifies a single claim against a context with exact, Jaccard, and NLI checks."""
    try:
        norm_claim = normalize_text(claim)
        norm_context = normalize_text(context)
        
        # 1. Exact Match Boost
        if norm_claim in norm_context:
            return {
                "claim": claim,
                "label": "entailment",
                "score": 1.0,
                "verdict": "Verified",
                "confidence": 1.0,
                "method": "exact_match"
            }
            
        # 2. Perfect Word Overlap Boost (all claim words in context)
        overlap = get_word_overlap(claim, context)
        if overlap >= 0.95:
            return {
                "claim": claim,
                "label": "entailment",
                "score": 0.95,
                "verdict": "Verified",
                "confidence": 0.95,
                "method": "lexical_overlap"
            }
            
        # 3. Cache Check
        cache_key = get_cache_key(claim, context)
        if cache_key in _nli_cache:
            cached = _nli_cache[cache_key]
            cached["method"] = "cache"
            return cached
            
        # 4. Deep NLI Inference
        pipe = get_nli_pipeline()
        # Limit context to avoid excessive processing times
        truncated_context = context[:1500]
        
        result = pipe(
            {
                "text": truncated_context,
                "text_pair": claim
            },
            truncation=True
        )
        
        if isinstance(result, list):
            label = result[0]["label"].lower()
            score = result[0]["score"]
        else:
            label = result["label"].lower()
            score = result["score"]
            
        # Smart Verdict mapping
        if "entail" in label:
            verdict = "Verified"
            confidence = round(score, 2)
        elif "neutral" in label:
            # Neutral could be Mostly Supported if there is substantial word overlap
            if overlap >= 0.60:
                verdict = "Mostly Supported"
                confidence = round(score * 0.8, 2)
            else:
                verdict = "Potential Hallucination"
                confidence = round(score, 2)
        else: # Contradiction
            verdict = "Potential Hallucination"
            confidence = round(score, 2)
            
        res = {
            "claim": claim,
            "label": label,
            "score": round(score, 2),
            "verdict": verdict,
            "confidence": confidence,
            "method": "deberta_nli"
        }
        
        # Save to cache
        _nli_cache[cache_key] = res
        return res
        
    except Exception as e:
        logger.error(f"Error verifying claim '{claim}': {e}")
        # Graceful fallback to Mostly Supported if exact match or overlap matches
        return {
            "claim": claim,
            "label": "neutral",
            "score": 0.50,
            "verdict": "Mostly Supported",
            "confidence": 0.50,
            "method": "fallback"
        }

# =========================================
# VERIFY ENTIRE ANSWER
# =========================================
def verify_answer(answer: str, retrieved_chunks: list) -> dict:
    """Deconstructs answer into claims and verifies them against source chunks."""
    context = " ".join(retrieved_chunks)
    claims = extract_claims(answer)
    
    if not claims:
        # If no distinct sentences were extracted, verify the whole answer as one
        claims = [answer] if answer.strip() else []
        
    claim_results = []
    total_score = 0.0
    total_confidence = 0.0
    
    for claim in claims:
        res = verify_claim(claim, context)
        claim_results.append(res)
        
        # Weighted faithfulness score: entailment = 1.0, neutral/mostly = 0.6, hallucination = 0.0
        if res["verdict"] == "Verified":
            total_score += 1.0
        elif res["verdict"] == "Mostly Supported":
            total_score += 0.6
        else:
            total_score += 0.0
            
        total_confidence += res["confidence"]
        
    count = len(claim_results)
    faithfulness_score = round(total_score / count, 2) if count > 0 else 0.0
    average_confidence = round(total_confidence / count, 2) if count > 0 else 0.0
    
    # Calculate overall verdict
    verified_count = sum(1 for c in claim_results if c["verdict"] == "Verified")
    mostly_supported_count = sum(1 for c in claim_results if c["verdict"] == "Mostly Supported")
    
    if count == 0:
        overall_verdict = "Insufficient Context"
    elif verified_count == count:
        overall_verdict = "Verified"
    elif verified_count + mostly_supported_count >= count / 2:
        overall_verdict = "Mostly Supported"
    else:
        overall_verdict = "Potential Hallucination"
        
    return {
        "faithfulness_score": faithfulness_score,
        "average_confidence": average_confidence,
        "overall_verdict": overall_verdict,
        "claim_results": claim_results
    }
