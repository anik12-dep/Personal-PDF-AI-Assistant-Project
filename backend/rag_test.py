
from sentence_transformers import SentenceTransformer
import chromadb
import ollama

# 1. Load Embedding Model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 2. Connect to ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_collection(
    name="pdf_documents"
)

# 3. User Question
question = input("\nAsk your PDF a question: ")

# 4. Convert Question into Embedding
question_embedding = model.encode(question).tolist()

# 5. Retrieve Relevant Chunks
results = collection.query(
    query_embeddings=[question_embedding],
    n_results=5
)

# 6. Prepare Context
context = "\n\n".join(results["documents"][0])

# 7. Send Context to Llama
response = ollama.chat(
    model="llama3.2",
    messages=[
        {
            "role": "system",
            "content": (
                "You are a helpful PDF assistant. "
                "Answer questions using only the provided context. "
                "If the answer is not available in the context, "
                "say that the PDF does not contain the answer."
            )
        },
        {
            "role": "user",
            "content": f"""
            Context from PDF:
            {context}

            Question:
            {question}

            Give a clear and simple answer.
            """
        }
    ]
)

# 8. Display Final Answer
print("\n========== AI ANSWER ==========\n")
print(response["message"]["content"])
