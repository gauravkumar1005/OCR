"""
Optional persistent model server.

Every OCR job runs main.py as a brand-new subprocess, so the heavy YOLO
layout-detection model and the EDSR super-resolution model get reloaded
from disk on every single job even though both modules already have a
module-level cache - the cache just never survives past one subprocess.

This process loads both models ONCE at startup and keeps them warm for
as long as it stays running. main.py's subprocess calls into it (via
model_client.py) instead of loading the models itself, whenever
OCR_MODEL_SERVER_URL is set and this server is reachable.

This is entirely optional. If you don't run this, nothing changes -
main.py falls back to loading models itself exactly as before.

Usage:
    python model_server.py
    # then, in .env (for both api.py and the main.py subprocess it spawns):
    OCR_MODEL_SERVER_URL=http://localhost:9100
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parent
sys.path.append(str(ENGINE_ROOT))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from OCR_Extraction_folder.layout_block_detection import (
    _detect_layout_local,
    load_model as load_layout_model,
)
from OCR_Extraction_folder.super_resolution import (
    _apply_super_resolution_local,
    load_sr_model,
)

app = FastAPI(title="Claim OCR Model Server", version="1.0.0")


class LayoutDetectRequest(BaseModel):
    image_path: str
    layout_output_folder: str
    cropped_output_folder: str
    conf_threshold: float = 0.35
    imgsz: int = 1024


class SuperResRequest(BaseModel):
    image_path: str
    output_folder: str


@app.on_event("startup")
async def _warm_models() -> None:
    print("[MODEL_SERVER] Warming models...")
    load_layout_model()
    load_sr_model()
    print("[MODEL_SERVER] Models ready - staying warm for subsequent jobs.")


@app.post("/layout/detect")
async def layout_detect(payload: LayoutDetectRequest):
    try:
        return _detect_layout_local(
            payload.image_path,
            payload.layout_output_folder,
            payload.cropped_output_folder,
            conf_threshold=payload.conf_threshold,
            imgsz=payload.imgsz,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/superres/enhance")
async def superres_enhance(payload: SuperResRequest):
    try:
        output_path = _apply_super_resolution_local(payload.image_path, payload.output_folder)
        return {"output_path": output_path}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "model-server"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("MODEL_SERVER_PORT", "9100"))
    uvicorn.run(app, host="0.0.0.0", port=port)
