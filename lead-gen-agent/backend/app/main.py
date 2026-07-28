from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import leads, jobs

app = FastAPI(title="Lead Gen Agent API")

# Allows your React dev server (usually localhost:5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads.router)
app.include_router(jobs.router)

@app.get("/health")
def health():
    return {"status": "ok"}