# Backwards compatibility redirect
from app.backend.services.nli_service import verify_claim

def verify_claim_nli(claim, context):
    res = verify_claim(claim, context)
    return {
        "claim": res["claim"],
        "label": res["label"],
        "score": res["score"]
    }