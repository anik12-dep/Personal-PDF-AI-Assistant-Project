from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
from io import BytesIO
import ollama

# Create FastAPI Application
app = FastAPI(
    title="Personal PDF AI Assistant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import Memory Functions
from memory import (
    initialize_db,
    create_conversation,
    update_conversation_title,
    get_conversation_title,
    get_history,
    save_message,
    list_conversations
)

# Import Vector Store
from vector_store import model, collection, store_chunks

# Initialize Database
initialize_db()

def chunk_text(text, page_number, chunk_size=500, overlap=100):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append({
                "text": chunk,
                "page_number": page_number
            })

        start += chunk_size - overlap

    return chunks


# Request Model
class ChatRequest(BaseModel):
    conversation_id: str
    question: str


# Home API
@app.get("/")
def home():
    return {
        "message": "Personal PDF AI Assistant Backend is Running!"
    }


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file."
        )

    try:
        contents = await file.read()

        pdf_reader = PdfReader(BytesIO(contents))

        all_chunks = []
        total_characters = 0

        for page_number, page in enumerate(
            pdf_reader.pages, start=1
        ):

            text = page.extract_text() or ""

            total_characters += len(text)

            page_chunks = chunk_text(
                text,
                page_number
            )

            all_chunks.extend(page_chunks)

        if not all_chunks:
            raise HTTPException(
                status_code=400,
                detail="No extractable text found in PDF."
            )

        stored_chunks = store_chunks(
            all_chunks,
            file.filename
        )

        return {
            "filename": file.filename,
            "total_pages": len(pdf_reader.pages),
            "total_characters": total_characters,
            "total_chunks": len(all_chunks),
            "stored_chunks": stored_chunks,
            "message": "PDF uploaded successfully!"
        }

    except HTTPException:
        raise

    except Exception as e:
        print("PDF Upload Error:", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



# Create New Conversation
@app.post("/conversations")
def new_conversation():

    conversation_id = create_conversation()

    return {
        "message": "Conversation created successfully!",
        "conversation_id": conversation_id,
        "title": get_conversation_title(conversation_id)
    }


# Get All Conversations
@app.get("/conversations")
def get_all_conversations():

    conversations = list_conversations()

    return {
        "total_conversations": len(conversations),
        "conversations": [
            {
                "conversation_id": cid,
                "title": title,
                "created_at": created_at
            }
            for cid, title, created_at in conversations
        ]
    }


# Get Specific Conversation History
@app.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: str):

    conversations = list_conversations()
    valid_ids = [cid for cid, _, _ in conversations]

    if conversation_id not in valid_ids:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    history = get_history(conversation_id)

    return {
        "conversation_id": conversation_id,
        "title": get_conversation_title(conversation_id),
        "total_messages": len(history),
        "history": history
    }


# Chat API
@app.post("/chat")
def chat(request: ChatRequest):

    conversation_id = request.conversation_id
    question = request.question.strip()

    # Validate Question
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    # Validate Conversation
    conversations = list_conversations()
    valid_ids = [cid for cid, _, _ in conversations]

    if conversation_id not in valid_ids:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    try:

        # Load Previous History
        chat_history = get_history(conversation_id)

        # Generate Embedding
        question_embedding = model.encode(
            question
        ).tolist()

       
        # Search PDF Chunks
        documents = []
        metadatas = []

        total_chunks = collection.count()

        if total_chunks > 0:

            results = collection.query(
                query_embeddings=[question_embedding],
                n_results=min(5, total_chunks),
            )

            documents = results["documents"][0] or []
            metadatas = results["metadatas"][0] or []


        # Debug Retrieved Chunks
        print("\n========== RETRIEVED CHUNKS ==========")

        for i, (doc, metadata) in enumerate(
            zip(documents, metadatas), 1
        ):
            print(f"\nChunk {i}")
            print("Source:", metadata.get("source"))
            print("Page:", metadata.get("page_number"))
            print("Text:", doc)

        print("\n======================================\n")

        # Prepare PDF Context
        context_parts = []

        for doc, metadata in zip(documents, metadatas):

            context_parts.append(
                f"""
Source: {metadata.get('source', 'Unknown')}
Page: {metadata.get('page_number', 'Unknown')}

Content:
{doc}
"""
            )

        context = "\n\n".join(context_parts)

        if not context:
            context = "No relevant PDF context was found."

        # Prepare User Message
        user_message = f"""
PDF Context:
{context}

Current Question:
{question}

Instructions:
- Answer using only the provided PDF context.
- Use conversation history to understand follow-up questions.
- Do not treat previous AI answers as factual evidence.
- Do not invent information.
- If the PDF does not contain the answer, clearly say so.
"""

        # Prepare LLM Messages
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful Personal PDF AI Assistant. "
                    "Answer questions using only the provided PDF context. "
                    "Use conversation history only to understand follow-up "
                    "questions. Previous assistant answers are not factual "
                    "evidence. Never invent information. If the PDF context "
                    "does not contain the answer, clearly say that the "
                    "information is not available in the uploaded PDF."
                )
            }
        ]

        # Add Previous Chat History
        messages.extend(chat_history[-10:])

        # Add Current Question
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Generate AI Answer
        response = ollama.chat(
            model="llama3.2",
            messages=messages
        )

        answer = response["message"]["content"]

        # Prepare Source Citations
        unique_sources = set()

        for metadata in metadatas:

            unique_sources.add((
                metadata.get("source", "Unknown"),
                metadata.get("page_number", 0)
            ))

        sources = [
            {
                "pdf": source,
                "page": page
            }
            for source, page in sorted(unique_sources)
        ]

        # Save User Message
        save_message(
            conversation_id,
            "user",
            question
        )

        # Save AI Answer
        save_message(
            conversation_id,
            "assistant",
            answer
        )

        # Generate Title from First Question
        if not chat_history:

            title = " ".join(question.split()[:7])
            title = title.title()

            if len(title) > 50:
                title = title[:47] + "..."

            update_conversation_title(
                conversation_id,
                title
            )

        # Get Updated Title
        conversation_title = get_conversation_title(
            conversation_id
        )

        # Return Response
        return {
            "conversation_id": conversation_id,
            "title": conversation_title,
            "question": question,
            "answer": answer,
            "sources": sources,
            "message": "Conversation saved successfully!"
        }

    except HTTPException:
        raise

    except Exception as e:

        print("Chat Error:", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
