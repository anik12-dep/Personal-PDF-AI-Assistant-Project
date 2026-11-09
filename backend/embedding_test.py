
from sentence_transformers import SentenceTransformer
from sentence_transformers import util

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Two example sentences
sentences = [
    "Leadership motivates employees.",
    "A good leader inspires workers.",
    "Machine learning uses algorithms."
]

# Generate embeddings
embeddings = model.encode(sentences)

# Show embeddings
print("Embedding shape:", embeddings.shape)

# Calculate similarity
similarity = util.cos_sim(
    embeddings[0],
    embeddings[1]
)

print("Similarity score:", similarity.item())
