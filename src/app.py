import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from config import settings
from pathlib import Path
from embeddings import build_vector_store
from rag_chain import review_snippet
from docx_utils import annotate_docx
import uvicorn
from rich import print
import shutil, uuid

app = FastAPI(title="ADGM RAG Compliance Service")

# Ensure dirs
Path(settings.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.ADGM_REF_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.TEMPLATES_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.CHROMA_PERSIST).mkdir(parents=True, exist_ok=True)

@app.post("/ingest/rebuild")
async def rebuild_vector_store(refresh: bool = False):
    try:
        build_vector_store(refresh=refresh)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok", "message": "vector store built"}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    # Save upload
    uid = uuid.uuid4().hex
    upload_path = os.path.join(settings.UPLOADS_DIR, f"{uid}_{file.filename}")
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # Simple: extract text snippet from docx or pdf (first 5000 chars)
    from ingestion import load_docx_text, load_pdf_text
    ext = Path(upload_path).suffix.lower()
    if ext == ".docx":
        text = load_docx_text(upload_path)
    elif ext == ".pdf":
        text = load_pdf_text(upload_path)
    else:
        raise HTTPException(400, "Unsupported file type.")
    snippet = text[:4000]
    # Run RAG review on snippet (the chain returns result + source docs)
    res = review_snippet(snippet)
    # parse LLM output - ideally structured JSON (we encourage the prompt to return JSON); for now keep raw
    raw = res.get("result") if isinstance(res, dict) else res
    # TODO: parse into annotations (we assume LLM returns mapping)
    # For demo: create simple annotation searching for flagged keywords (this should be replaced by parsed LLM output)
    annotations = {}
    # naive example: if 'jurisdiction' in raw → annotate
    if "jurisdiction" in raw.lower():
        annotations["jurisdiction"] = {"comment": "Ensure jurisdiction specifies 'ADGM' and ADGM Courts where applicable.", "severity":"High"}
    # Create annotated docx
    reviewed_path, meta_json = annotate_docx(upload_path, annotations)
    return JSONResponse({"analysis": raw, "reviewed_docx": reviewed_path, "comments_json": meta_json})

@app.get("/download")
async def download(path: str):
    if not os.path.exists(path):
        raise HTTPException(404, "file not found")
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=Path(path).name)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
