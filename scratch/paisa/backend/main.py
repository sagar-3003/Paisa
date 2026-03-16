from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, dashboard, ocr, tally, bank
from db.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    await init_db()
    print("Database tables initialized.")
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(chat.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(ocr.router, prefix="/api")
app.include_router(tally.router, prefix="/api")
app.include_router(bank.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "ok", "app": "Paisa AI Accountant Backend"}
