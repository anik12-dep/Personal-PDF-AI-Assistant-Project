
from sentence_transformers import SentenceTransformer
import chromadb

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

# Get page-aware collection
collection = client.get_collection(
    name="pdf_documents_v2"
)

# User question
question = input("\nAsk your PDF a question: ")

# Convert question into embedding
question_embedding = model.encode(question).tolist()

# Search relevant chunks
results = collection.query(
    query_embeddings=[question_embedding],
    n_results=3
)

print("\nRelevant PDF Information:\n")

for document, metadata in zip(
    results["documents"][0],
    results["metadatas"][0]
):
    print("--------------------------------")
    print("Source:", metadata["source"])
    print("Page:", metadata["page_number"])
    print("Content:", document)
