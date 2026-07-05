from transformers import pipeline

nli_pipeline = pipeline("text-classification", model="facebook/bart-large-mnli")

context = "Machine Learning Machine Learning is a subset of AI where computers learn patterns from data instead of being explicitly programmed."
claim = "Machine learning is a subset of AI where computers learn patterns from data instead of being explicitly programmed."

print("Using </s></s>:")
print(nli_pipeline(f"{context}</s></s>{claim}"))

print("Using text/text_pair:")
print(nli_pipeline({"text": context, "text_pair": claim}))
