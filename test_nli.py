from app.backend.nli_verifier import verify_claim_nli

context = "Machine learning learns from data."

claim = "Machine learning learns from data."

result = verify_claim_nli(claim, context)

print(result)