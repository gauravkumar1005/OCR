"""
Central configuration for the backend.
All values are read from environment variables (see .env.example).
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ---- MongoDB ----
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "claims_db"

    # ---- Cloudinary (used only if backend itself needs to talk to Cloudinary,
    # e.g. to fetch the uploaded file for the OCR engine) ----
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # ---- OCR engine ----
    # If the OCR engine runs as a separate microservice, point to its URL.
    # If it runs in-process / as a subprocess, this can be left blank.
    OCR_ENGINE_URL: str = "http://localhost:9000"

    # ---- Backend ----
    BACKEND_PUBLIC_URL: str = "http://localhost:8000"

    # ---- App ----
    APP_NAME: str = "Claim OCR Backend"
    ENV: str = "development"
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"


settings = Settings()
