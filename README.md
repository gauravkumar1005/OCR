# Insurance Document Intelligence Platform

Enterprise-grade platform for uploading insurance documents, associating them with Claim IDs, storing files in Cloudinary, dispatching OCR jobs to a separate OCR engine, receiving OCR callbacks, and presenting mapped results in a modern Next.js frontend.

---

## Overview

This platform supports the full document intelligence flow:

- Upload insurance documents
- Associate documents with Claim IDs
- Store uploaded files in Cloudinary
- Dispatch each document to an external OCR engine over HTTP
- Receive OCR callbacks after processing completes
- Persist raw OCR JSON in MongoDB
- Generate frontend-friendly mapped JSON through the mapper architecture
- Expose document retrieval APIs for the frontend

The OCR engine runs as a separate service in `OCR-eng/` and communicates with the FastAPI backend through HTTP.

---

## Current Features

- Claim-based document upload
- Multiple document types with a default of `combined_document`
- Cloudinary file storage
- MongoDB persistence with Beanie ODM
- FastAPI backend with structured service/repository layers
- Asynchronous OCR dispatch
- OCR callback endpoint for completed or failed jobs
- Raw OCR JSON storage
- Mapper architecture with strategy-based mappers
- REST APIs for document retrieval and deletion
- Swagger/OpenAPI documentation
- Next.js frontend dashboard
- Upload page with drag-and-drop PDF support
- Claim details page grouped by Claim ID
- Split-screen document viewer with PDF preview and mapped data panels

---

## Project Structure

```text
Insurance Document Intelligence Platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── database/
│   │   ├── dependencies/
│   │   ├── exceptions/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   └── config/mapping/
│   ├── requirements.txt
│   ├── .env.example
│   └── venv/ (local only)
├── frontend/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── lib/
│   ├── store/
│   ├── package.json
│   ├── package-lock.json
│   └── .env.example
├── OCR-eng/
│   ├── app.py
│   ├── main.py
│   ├── OCR_Extraction_folder/
│   ├── document_grouper/
│   ├── project/
│   ├── models/
│   ├── requirements.txt
│   └── temp/ and RESULT/ (generated)
├── README.md
└── .gitignore
```

---

## Tech Stack

### Backend

- FastAPI
- Python
- Beanie ODM
- Motor / MongoDB
- MongoDB Atlas compatible configuration
- Pydantic v2
- Cloudinary
- requests
- Uvicorn

### OCR Engine

- Flask
- Python
- requests
- OCR / document processing pipeline modules in `OCR-eng/`

### Frontend

- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- Redux Toolkit
- RTK Query
- React Hook Form
- Zod
- React Dropzone
- React PDF
- TanStack Table
- Lucide React
- Framer Motion
- Sonner
- Local shadcn-style UI primitives

---

## Installation

### Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### OCR Engine

```powershell
cd OCR-eng
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env.local
```

---

## Environment Variables

### Backend `backend/.env.example`

| Variable | Description |
|---|---|
| `APP_NAME` | FastAPI application name |
| `API_PREFIX` | Base API prefix used by backend routes |
| `MONGODB_URI` | MongoDB connection string |
| `DATABASE_NAME` | MongoDB database name |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `OCR_ENGINE_URL` | OCR engine base URL for dispatching OCR jobs. For local development, point this to `http://127.0.0.1:8001` |
| `OCR_API_KEY` | Optional bearer token forwarded to the OCR engine |
| `MAX_UPLOAD_SIZE` | Maximum upload size in bytes |
| `LOG_LEVEL` | Application log level |
| `CORS_ORIGINS` | Allowed CORS origins |

### Frontend `frontend/.env.example`

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend base URL used by the Next.js client |

### OCR Engine configuration

The OCR engine currently keeps its local runtime configuration in `OCR-eng/project/config.py`. There is not a committed `.env.example` for that service yet.

---

## Running the Project

### Backend

```powershell
cd backend
venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### OCR Engine

```powershell
cd OCR-eng
venv\Scripts\Activate.ps1
python app.py
```

### Frontend

```powershell
cd frontend
npm run dev
```

---

## API Documentation

Swagger UI is available from the FastAPI backend at:

```text
http://127.0.0.1:8000/docs
```

---

## Workflow

```text
Document Upload
↓
Cloudinary
↓
OCR Engine
↓
OCR Callback
↓
Raw OCR
↓
Mapper
↓
Mapped JSON
↓
Frontend
```

---

## Implemented APIs

### Backend

- `GET /health`
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents?claimId={claimId}`
- `GET /api/v1/documents/{documentId}`
- `GET /api/v1/documents/{documentId}/raw-ocr`
- `GET /api/v1/documents/{documentId}/mapped`
- `DELETE /api/v1/documents/{documentId}`
- `POST /api/ocr/callback`
- `PATCH /api/ocr/callback`

### OCR Engine

- `GET /health`
- `POST /ocr/process`

---

## Future Roadmap

- Additional document mappers
- Claim Aggregator
- Investigation Dashboard
- AI Validation
- Fraud Detection
- Cross-document comparison

---

## License

MIT
