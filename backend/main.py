
from fastapi import FastAPI, UploadFile, File, HTTPException
from pypdf import PdfReader
from io import BytesIO

# Import Vector Store
from vector_store import store_chunks


def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


app = FastAPI(
    title="Personal PDF AI Assistant",
    description="Upload PDF and extract text from it",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Personal PDF AI Assistant is Running!"
    }


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file"
        )

    try:
        contents = await file.read()

        pdf = PdfReader(BytesIO(contents))

        extracted_text = ""

        for page in pdf.pages:
            extracted_text += page.extract_text() or ""

        # Text Chunking
        chunks = chunk_text(
            extracted_text,
            chunk_size=500,
            overlap=100
        )

        # Store chunks in ChromaDB
        stored_chunks = store_chunks(
            chunks,
            file.filename
        )

        return {
            "filename": file.filename,
            "total_pages": len(pdf.pages),
            "total_characters": len(extracted_text),
            "total_chunks": len(chunks),
            "stored_chunks": stored_chunks,
            "message": "PDF uploaded and stored successfully!",
            "chunks": chunks
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
