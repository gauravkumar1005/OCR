# Insurance Claim Document Management Backend

FastAPI backend for a claim-centric insurance document management platform.

## Stack

- Python 3.12
- FastAPI
- Pydantic v2
- MongoDB Atlas
- Beanie ODM
- Motor
- Cloudinary
- httpx
- python-dotenv
- Loguru or standard logging
- Uvicorn

## What This Phase Covers

- Claim creation and listing
- Claim-scoped document upload and retrieval
- Cloudinary upload and deletion
- MongoDB persistence for claims, documents, OCR results, and mapped results
- External OCR client integration
- Raw OCR storage exactly as returned
- Mapper placeholder service
- Request ID middleware, CORS, and centralized error handling

## Claim API

- `POST /api/v1/claims`
  - Request body: `{ "claimId": "CLM202600001" }`
- `GET /api/v1/claims`
- `GET /api/v1/claims/{claimId}`

## Run

```bash
venv\Scripts\activate
uvicorn app.main:app --reload
```

## Notes

- OCR is external and intentionally not implemented here.
- Mapper logic is intentionally a no-op placeholder for this phase.
- Documents are soft-deleted in MongoDB and removed from Cloudinary as cleanup.
