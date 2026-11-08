
from fastapi import FastAPI, UploadFile, File

app = FastAPI()

@app.get("/")
def home():
    return {
        "message": "Personal PDF AI Assistant is Running!"
    }


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "message": "PDF uploaded successfully!"
    }

