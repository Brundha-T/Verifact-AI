from transformers import pipeline

# We can use MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli
nli_pipeline = pipeline("text-classification", model="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli")

context = "This type of AI does not yet fully exist. Machine Learning Machine Learning is a subset of AI where computers learn patterns from data instead of being explicitly programmed. Supervised Learning In supervised learning, models are trained using labeled data. Unsupervised Learning In unsupervised learning, models identify patterns from unlabeled data. Deep Learning Deep Learning is a subset of machine learning that uses neural networks with many layers. It"
claim = "Machine learning is a subset of AI where computers learn patterns from data instead of being explicitly programmed."

print("Using text/text_pair:")
print(nli_pipeline({"text": context, "text_pair": claim}))
