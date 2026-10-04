from fastapi import FastAPI
from app.core.config import setting
from app.graph.investigation_graph import build_investigation_graph
from app.models.base import Base
from app.models.investigation import Investigation
from app.core.database import engine
from pydantic import BaseModel
from app.graph.workflow import graph
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title=setting.app_name,
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


Base.metadata.create_all(bind=engine)

class InvestigationRequest(BaseModel):
    query : str

@app.get("/")
def root():
    return {
        "message" : "FinInvestigator is Running",
        "version" : "0.1.0"
    }

@app.get("/health")
def health():
    return {
        "status" : "Ok"
    }

@app.post("/investigate")
def investigate(
    request: InvestigationRequest
):

    initial_state = {
        "query": request.query,
        "errors": []
    }

    result = graph.invoke(initial_state)

    return {
        "query": request.query,
        "company": result.get("company"),
        "report": result.get("final_report"),
        "errors": result.get("errors", [])
    }
