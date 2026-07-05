from app.backend.rag_pipeline import ask_question
import pprint

print("Running pipeline...")
result = ask_question("What is machine learning?")
pprint.pprint(result)
