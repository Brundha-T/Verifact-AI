from app.backend.rag_pipeline import ask_question

question = input("Ask Question: ")

result = ask_question(question)

print("\n========== ANSWER ==========\n")

print(result["answer"])

print("\n========== RETRIEVED CHUNKS ==========\n")

for i, chunk in enumerate(result["retrieved_chunks"]):

    print(f"\n--- Chunk {i+1} ---\n")

    print(chunk)