import axios from "axios";

const STORAGE_KEY = "claim_ocr_api_base_url";
const DEFAULT_BASE_URL = "http://localhost:8000";

export function getBaseUrl() {
  return localStorage.getItem(STORAGE_KEY) || DEFAULT_BASE_URL;
}

export function setBaseUrl(url) {
  localStorage.setItem(STORAGE_KEY, url.replace(/\/+$/, ""));
}

export const api = axios.create({
  baseURL: getBaseUrl(),
});

api.interceptors.request.use((config) => {
  config.baseURL = getBaseUrl();
  return config;
});

// ---- Claims ----
export const uploadClaim = (file, fileNo, onProgress) => {
  const form = new FormData();
  form.append("file", file);
  if (fileNo) form.append("file_no", fileNo);
  return api.post("/claims/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (evt) => {
      if (onProgress && evt.total) {
        onProgress(Math.round((evt.loaded * 100) / evt.total));
      }
    },
  });
};

export const listClaims = (params) => api.get("/claims", { params });

export const getClaim = (claimId) => api.get(`/claims/${claimId}`);

export const deleteClaim = (claimId) => api.delete(`/claims/${claimId}`);

export const updateClaimStatus = (claimId, status) =>
  api.patch(`/claims/${claimId}/status`, { status });

// ---- Documents ----
export const listDocuments = (claimId) =>
  api.get(`/claims/${claimId}/documents`);

export const getDocument = (claimId, documentType) =>
  api.get(`/claims/${claimId}/documents/${documentType}`);

// Backend expects one field at a time: { key: "field_name", value: "new value" }
export const updateEntity = (claimId, documentType, key, value) =>
  api.patch(`/claims/${claimId}/documents/${documentType}/entities`, {
    key,
    value,
  });

// Convenience: save several changed fields by firing one PATCH per field.
export const updateEntities = async (claimId, documentType, changedFields) => {
  const entries = Object.entries(changedFields);
  const results = [];
  for (const [key, value] of entries) {
    results.push(await updateEntity(claimId, documentType, key, value));
  }
  return results;
};

export const checkHealth = () => api.get("/health");
