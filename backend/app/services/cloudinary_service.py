from __future__ import annotations

import asyncio
import io
from uuid import uuid4

import cloudinary
import cloudinary.uploader

from app.core.config import Settings
from app.exceptions.base import CloudinaryException


class CloudinaryService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True,
            )

    async def upload_file(
        self,
        *,
        file_bytes: bytes,
        file_name: str,
        mime_type: str,
    ) -> dict[str, str]:
        public_id = f"documents/{uuid4()}"
        file_obj = io.BytesIO(file_bytes)

        try:
            result = await asyncio.to_thread(
                cloudinary.uploader.upload,
                file_obj,
                resource_type="auto",
                public_id=public_id,
                overwrite=False,
            )
            return {
                "secure_url": result["secure_url"],
                "public_id": result["public_id"],
                "resource_type": result.get("resource_type", "auto"),
                "mime_type": mime_type,
            }
        except Exception as exc:  # noqa: BLE001
            raise CloudinaryException("Failed to upload file to Cloudinary") from exc

    async def delete_file(self, *, public_id: str, resource_type: str = "raw") -> None:
        try:
            await asyncio.to_thread(
                cloudinary.uploader.destroy,
                public_id,
                resource_type=resource_type,
            )
        except Exception as exc:  # noqa: BLE001
            raise CloudinaryException("Failed to delete file from Cloudinary") from exc
