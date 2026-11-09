
import chromadb
from sentence_transformers import SentenceTransformer
import uuid

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to persistent ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

# Create a new collection for page-aware documents
collection = client.get_or_create_collection(
    name="pdf_documents_v2"
)


def store_chunks(chunks, filename):

    # Extract text from chunks
    documents = [chunk["text"] for chunk in chunks]

    # Generate embeddings
    embeddings = model.encode(documents)

    # Generate unique IDs
    ids = [str(uuid.uuid4()) for _ in chunks]

    # Store metadata with page numbers
    metadatas = [
        {
            "source": filename,
            "page_number": chunk["page_number"]
        }
        for chunk in chunks
    ]

    # Store everything in ChromaDB
    if documents:
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )

    print(f"Successfully stored {len(documents)} chunks!")

    return len(documents)


print("Page-aware Vector Store initialized successfully!")
