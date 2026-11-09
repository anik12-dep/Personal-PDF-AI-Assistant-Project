
from sentence_transformers import SentenceTransformer
import chromadb
import ollama

from memory import (
    initialize_db,
    create_conversation,
    get_history,
    save_message,
    list_conversations
)

# 1. Initialize Database
initialize_db()

# 2. Load Embedding Model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 3. Connect to ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_collection(
    name="pdf_documents_v2"
)

print("\n===== Personal PDF AI Assistant =====")

# 4. Choose Conversation
print("\n1. Start New Conversation")
print("2. Continue Previous Conversation")

choice = input("\nChoose (1/2): ").strip()

if choice == "2":

    conversations = list_conversations()

    if conversations:

        print("\nPrevious Conversations:")

        for index, (conversation_id, created_at) in enumerate(
            conversations, start=1
        ):
            print(f"{index}. {conversation_id} | {created_at}")

        selected_id = input(
            "\nEnter Conversation ID: "
        ).strip()

        if any(cid == selected_id for cid, _ in conversations):
            conversation_id = selected_id
            chat_history = get_history(conversation_id)
            print("\nPrevious conversation loaded!")

        else:
            print("\nInvalid ID. Starting new conversation.")
            conversation_id = create_conversation()
            chat_history = []

    else:
        print("\nNo previous conversations found.")
        conversation_id = create_conversation()
        chat_history = []

else:

    conversation_id = create_conversation()
    chat_history = []


print("\nYour Conversation ID:")
print(conversation_id)

print("\nType 'exit' to stop the conversation.\n")


# 5. Conversation Loop
while True:

    question = input("\nYou: ").strip()

    if question.lower() in ["exit", "quit", "bye"]:
        print("\nAI: Conversation saved. Goodbye!")
        break

    if not question:
        continue

    # 6. Convert Question into Embedding
    question_embedding = model.encode(question).tolist()

    # 7. Retrieve Relevant PDF Chunks
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=5
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    # 8. Prepare PDF Context
    context = "\n\n".join(documents)

    user_message = f"""
Context from PDF:
{context}

Question:
{question}

Answer using only the provided PDF context.
"""


    # 9. Prepare Conversation Messages
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful PDF assistant. "
                "Answer using only the provided PDF context. "
                "Use previous conversation to understand follow-up questions. "
                "If the answer is unavailable in the context, "
                "say that the PDF does not contain the answer."
            )
        }
    ]

    messages.extend(chat_history)

    messages.append({
        "role": "user",
        "content": user_message
    })


    # 10. Ask Ollama
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


    # 13. Save Messages to SQLite
    save_message(
        conversation_id,
        "user",
        question
    )

    save_message(
        conversation_id,
        "assistant",
        answer
    )

    # Update current session memory
    chat_history.append({
        "role": "user",
        "content": question
    })

    chat_history.append({
        "role": "assistant",
        "content": answer
    })

    print("\n[Persistent conversation memory saved]")
