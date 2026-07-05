# Backwards compatibility redirect
from app.backend.services.nli_service import verify_answer as _verify_answer

def verify_answer(answer, retrieved_chunks):
    res = _verify_answer(answer, retrieved_chunks)
    return {
        "faithfulness_score": res["faithfulness_score"],
        "overall_verdict": res["overall_verdict"],
        "claim_results": res["claim_results"]
    }