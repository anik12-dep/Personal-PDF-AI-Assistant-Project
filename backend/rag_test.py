
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

# 3. User Question
question = input("\nAsk your PDF a question: ")

# 4. Convert Question into Embedding
question_embedding = model.encode(question).tolist()

# 5. Retrieve Relevant Chunks
results = collection.query(
    query_embeddings=[question_embedding],
    n_results=5
)

documents = results["documents"][0]
metadatas = results["metadatas"][0]

# 6. Prepare Context
context = "\n\n".join(documents)

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

# 9. Display Source Citation
print("\n========== SOURCE CITATION ==========\n")

if documents:
    unique_sources = set()

    for metadata in metadatas:
        source = metadata["source"]
        page = metadata["page_number"]

        unique_sources.add((source, page))

    for source, page in sorted(unique_sources):
        print(f"PDF: {source} | Page: {page}")
else:
    print("No source information found.")
