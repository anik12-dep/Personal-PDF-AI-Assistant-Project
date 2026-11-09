
import chromadb
from sentence_transformers import SentenceTransformer
import uuid

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to persistent ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

# Create or get collection
collection = client.get_or_create_collection(
    name="pdf_documents"
)


def store_chunks(chunks, filename):
    # Convert text chunks into embeddings
    embeddings = model.encode(chunks)

    # Generate unique IDs
    ids = [str(uuid.uuid4()) for _ in chunks]

    # Store everything in ChromaDB
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings.tolist(),
        metadatas=[
            {"source": filename} for _ in chunks
        ]
    )

    print(f"Successfully stored {len(chunks)} chunks!")

    return len(chunks)


print("Vector Store initialized successfully!")
