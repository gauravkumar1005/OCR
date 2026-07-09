# Claim OCR Setup

Claim OCR is a three-part system for uploading claims PDFs, extracting OCR data, and reviewing the structured output in a browser.

## Architecture

- `backend/` is the FastAPI service that stores claim records in MongoDB, accepts uploads, dispatches OCR jobs, and receives OCR callbacks.
- `engine/` is the OCR processing service and batch pipeline. It exposes a small FastAPI launcher and also runs the full extraction pipeline as a subprocess.
- `frontend/` is the React + Vite review desk used to upload claims, monitor processing, and edit extracted fields.

## End-To-End Flow

1. A user uploads a PDF from the frontend.
2. The frontend sends the file to `POST /claims/upload` on the backend.
3. The backend uploads the file to Cloudinary, creates a claim record in MongoDB, and dispatches an OCR job to the engine.
4. The engine runs `engine/main.py`, writes intermediate artifacts under `engine/RESULT/`, and sends the final OCR payload back to the backend callback endpoint.
5. The backend stores the raw OCR document data in MongoDB and exposes it through `GET /claims/{claim_id}`.
6. The frontend polls the claim until processing completes, then allows the reviewer to edit extracted entities and update claim status.

## Setup Order

1. Start MongoDB.
2. Configure the backend `.env` file.
3. Configure the engine `.env` file with the Groq API key and callback settings.
4. Start the backend API.
5. Start the engine API.
6. Start the frontend.

## Local Ports

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Engine API: `http://localhost:8001`

## Environment Summary

### Backend

- `MONGO_URI`
- `MONGO_DB_NAME`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`
- `OCR_ENGINE_URL`
- `BACKEND_PUBLIC_URL`
- `APP_NAME`
- `ENV`
- `CORS_ORIGINS`

### Engine

- `GROQ_API_KEY`
- `OCR_PDF_PATH`
- `OCR_CALLBACK_URL`
- `OCR_CALLBACK_METHOD`
- `OCR_CLAIM_ID`
- `OCR_DOCUMENT_ID`
- `OCR_DOCUMENT_TYPE`
- `OCR_FILE_URL`
- `OCR_MIME_TYPE`
- `OCR_MAX_PAGES` or `MAX_PDF_PAGES`
- `OCR_RESULT_ROOT`
- `OCR_RUN_ID`

### Frontend

- No build-time `.env` is required by default.
- The API base URL is stored in browser `localStorage` and can be changed from the settings modal.

## Development Commands

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Engine API

```bash
cd engine
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn api:app --reload --port 8001
```

### Engine Pipeline

```bash
cd engine
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Highlights

### Backend

- `POST /claims/upload`
- `POST /claims`
- `GET /claims`
- `GET /claims/{claim_id}`
- `PATCH /claims/{claim_id}/status`
- `DELETE /claims/{claim_id}`
- `POST /claims/{claim_id}/documents`
- `POST /claims/{claim_id}/documents/bulk`
- `POST|PATCH /claims/{claim_id}/documents/callback`
- `GET /uploads/cloudinary-signature`
- `POST /uploads/pdf`
- `GET /health`

### Engine

- `POST /ocr/process`
- `POST /run`
- `GET /health`

## Deployment Notes

- Keep backend, engine, and frontend base URLs aligned in deployment.
- Set `BACKEND_PUBLIC_URL` to a publicly reachable callback URL when the engine runs outside the backend process.
- Set `OCR_ENGINE_URL` in the backend to the deployed engine API URL.
- Lock down CORS in production instead of using the default wildcard setting.
- Store secrets only in environment variables, never in committed `.env` files.

## Common Issues

- MongoDB connection failures usually mean `MONGO_URI` is wrong or MongoDB is not running.
- Missing `GROQ_API_KEY` will stop the engine pipeline at startup.
- `pdf2image` requires the system PDF conversion dependency stack to be installed.
- If the frontend cannot reach the API, update the base URL from the settings modal and test the connection.
- Large PDFs can be slow because the pipeline writes many intermediate artifacts under `engine/RESULT/`.


