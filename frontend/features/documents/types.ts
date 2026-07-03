export type UploadProgressHandler = (progress: number) => void;

export type ApiResponse<T> = {
  success: boolean;
  message: string;
  data: T | null;
};

export type DocumentStatus = "PENDING" | "OCR_IN_PROGRESS" | "OCR_COMPLETED" | "MAPPING_IN_PROGRESS" | "COMPLETED" | "FAILED";
export type OCRStatus = "processing" | "completed" | "failed";

export type DocumentSummary = {
  documentId: string;
  documentType: string | null;
  processingStatus: DocumentStatus;
};

export type DocumentDetail = {
  documentId: string;
  claimId: string;
  documentType: string | null;
  fileName: string;
  mimeType: string;
  cloudinaryUrl: string;
  uploadStatus: "UPLOADED" | "FAILED";
  processingStatus: DocumentStatus;
  ocrStatus: OCRStatus;
  error: string | null;
  fileSize: number;
  createdAt: string;
  updatedAt: string;
  mappedSummary?: Record<string, unknown> | null;
};

export type MappedData = {
  summary?: Record<string, unknown>;
  sections?: Array<Record<string, unknown>>;
  tables?: Array<Record<string, unknown>>;
  metadata?: Record<string, unknown>;
} | null;

export type UploadDocumentInput = {
  claimId: string;
  documentType: string;
  file: File;
  onProgress?: UploadProgressHandler;
};

export type UploadDocumentResult = ApiResponse<DocumentDetail>;
