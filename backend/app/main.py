from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from app.api.chat import router as chat_router

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": f"{settings.APP_NAME} is running!"}
