
from fastapi import FastAPI, UploadFile, File, HTTPException
from pypdf import PdfReader
from io import BytesIO

# Import Vector Store
from vector_store import store_chunks


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


app = FastAPI(
    title="Personal PDF AI Assistant",
    description="Upload PDF and ask questions with source citations",
    version="1.1.0"
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

        all_chunks = []
        total_characters = 0

        # Extract text page by page
        for page_number, page in enumerate(pdf.pages, start=1):

            page_text = page.extract_text() or ""

            total_characters += len(page_text)

            # Create chunks with page numbers
            page_chunks = chunk_text(
                page_text,
                page_number=page_number,
                chunk_size=500,
                overlap=100
            )

            all_chunks.extend(page_chunks)

        if not all_chunks:
            raise HTTPException(
                status_code=400,
                detail="No extractable text found in this PDF"
            )

        # Store chunks with metadata
        stored_chunks = store_chunks(
            all_chunks,
            file.filename
        )

        return {
            "filename": file.filename,
            "total_pages": len(pdf.pages),
            "total_characters": total_characters,
            "total_chunks": len(all_chunks),
            "stored_chunks": stored_chunks,
            "message": "PDF uploaded and stored successfully!",
            "chunks": all_chunks
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
