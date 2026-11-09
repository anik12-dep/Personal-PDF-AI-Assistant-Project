
from sentence_transformers import SentenceTransformer
import chromadb

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

# Get existing collection
collection = client.get_collection(
    name="pdf_documents"
)

# User question
question = "What are the advantages of sole proprietorship?"

# Convert question into embedding
question_embedding = model.encode(question).tolist()

# Search relevant chunks
results = collection.query(
    query_embeddings=[question_embedding],
    n_results=3
)

print("\nRelevant PDF Information:\n")

for document in results["documents"][0]:
    print("--------------------------------")
    print(document)
