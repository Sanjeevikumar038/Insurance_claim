import uvicorn
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.config import load_config
# Load environment variables (e.g., from .env file)
load_config()

from src.review import review_claim

app = FastAPI(title="PS02 Insurance Claims Evidence Review Assistant")

# Serve the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_index():
    return FileResponse("static/index.html")

@app.get("/api/claims")
def list_claims():
    try:
        with open("data/claims/claims.json", "r") as f:
            claims = json.load(f)
        return claims
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ReviewRequest(BaseModel):
    claim_id: str

@app.post("/api/review")
def api_review_claim(req: ReviewRequest):
    result = review_claim(req.claim_id)
    return result

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
