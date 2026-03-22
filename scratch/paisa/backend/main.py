import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, dashboard, ocr, tally, bank, cron
from db.database import init_db
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()
    print("Database tables initialized.")

origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(chat.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(ocr.router, prefix="/api")
app.include_router(tally.router, prefix="/api")
app.include_router(bank.router, prefix="/api")
app.include_router(cron.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "ok", "app": "Paisa AI Accountant Backend"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
