
from sentence_transformers import SentenceTransformer
import chromadb
import ollama

# 1. Load Embedding Model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 2. Connect to ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_collection(
    name="pdf_documents_v2"
)

# 3. Conversation Memory
chat_history = []

print("\n===== Personal PDF AI Assistant =====")
print("Ask questions about your PDF.")
print("Type 'exit' to stop the conversation.\n")

# 4. Start Conversation Loop
while True:

    question = input("\nYou: ").strip()

    if question.lower() in ["exit", "quit", "bye"]:
        print("\nAI: Goodbye! See you again.")
        break

    if not question:
        continue

    # 5. Convert Question into Embedding
    question_embedding = model.encode(question).tolist()

    # 6. Retrieve Relevant Chunks
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=5
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    # 7. Prepare Context
    context = "\n\n".join(documents)

    # 8. Prepare Current User Message
    user_message = f"""
    Context from PDF:
    {context}

    Question:
    {question}

    Answer using only the provided PDF context.
    """

    # 9. Prepare Messages with Conversation Memory
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful PDF assistant. "
                "Answer questions using only the provided PDF context. "
                "Use previous conversation to understand follow-up questions. "
                "If the answer is not available in the context, "
                "say that the PDF does not contain the answer."
            )
        }
    ]

    messages.extend(chat_history)

    messages.append({
        "role": "user",
        "content": user_message
    })

    # 10. Send Messages to Llama
    response = ollama.chat(
        model="llama3.2",
        messages=messages
    )

    answer = response["message"]["content"]

    # 11. Display Answer
    print("\n========== AI ANSWER ==========\n")
    print(answer)

    # 12. Display Source Citation
    print("\n========== SOURCE CITATION ==========\n")

    unique_sources = set()

    for metadata in metadatas:
        unique_sources.add((
            metadata["source"],
            metadata["page_number"]
        ))

    for source, page in sorted(unique_sources):
        print(f"PDF: {source} | Page: {page}")

    # 13. Save Conversation History
    chat_history.append({
        "role": "user",
        "content": user_message
    })

    chat_history.append({
        "role": "assistant",
        "content": answer
    })

    print("\n[Conversation memory updated]")
