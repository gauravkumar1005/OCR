import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import type { FetchBaseQueryError, FetchBaseQueryMeta, QueryReturnValue } from "@reduxjs/toolkit/query";

import type {
  ApiResponse,
  DocumentDetail,
  DocumentSummary,
  MappedData,
  UploadDocumentInput,
  UploadDocumentResult
} from "@/features/documents/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

function unwrapResponse<T>(response: ApiResponse<T> | T) {
  if (response && typeof response === "object" && "data" in response) {
    return (response as ApiResponse<T>).data;
  }
  return response as T;
}

export const documentsApi = createApi({
  reducerPath: "documentsApi",
  baseQuery: fetchBaseQuery({
    baseUrl: API_BASE_URL
  }),
  tagTypes: ["Documents", "Document"],
  endpoints: (builder) => ({
    getDocumentsByClaimId: builder.query<DocumentSummary[], string>({
      query: (claimId) => `/api/v1/documents?claimId=${encodeURIComponent(claimId)}`,
      providesTags: (_result, _error, claimId) => [{ type: "Documents", id: claimId }]
    }),
    getDocumentById: builder.query<DocumentDetail, string>({
      query: (documentId) => `/api/v1/documents/${documentId}`,
      transformResponse: (response: ApiResponse<DocumentDetail>) => unwrapResponse(response) as DocumentDetail,
      providesTags: (_result, _error, documentId) => [{ type: "Document", id: documentId }]
    }),
    getRawOcrById: builder.query<Record<string, unknown> | null, string>({
      query: (documentId) => `/api/v1/documents/${documentId}/raw-ocr`,
      transformResponse: (response: ApiResponse<Record<string, unknown> | null>) => unwrapResponse(response)
    }),
    getMappedDataById: builder.query<MappedData, string>({
      query: (documentId) => `/api/v1/documents/${documentId}/mapped`,
      transformResponse: (response: ApiResponse<MappedData>) => unwrapResponse(response) as MappedData
    }),
    deleteDocument: builder.mutation<ApiResponse<{ documentId: string; deleted: boolean }>, string>({
      query: (documentId) => ({
        url: `/api/v1/documents/${documentId}`,
        method: "DELETE"
      }),
      invalidatesTags: (_result, _error, documentId) => [{ type: "Document", id: documentId }]
    }),
    uploadDocument: builder.mutation<UploadDocumentResult, UploadDocumentInput>({
      async queryFn(arg) {
        return new Promise<QueryReturnValue<UploadDocumentResult, FetchBaseQueryError, FetchBaseQueryMeta | undefined>>((resolve) => {
          const formData = new FormData();
          formData.append("claimId", arg.claimId);
          formData.append("documentType", arg.documentType);
          formData.append("file", arg.file);

          const xhr = new XMLHttpRequest();
          xhr.open("POST", `${API_BASE_URL}/api/v1/documents/upload`);
          xhr.responseType = "json";

          xhr.upload.onprogress = (event) => {
            if (event.lengthComputable && arg.onProgress) {
              const progress = Math.round((event.loaded / event.total) * 100);
              arg.onProgress(progress);
            }
          };

          xhr.onload = () => {
            const payload = xhr.response ?? JSON.parse(xhr.responseText || "{}");
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve({ data: payload as UploadDocumentResult });
              return;
            }

            resolve({
              error: {
                status: xhr.status,
                data: payload
              } as FetchBaseQueryError
            });
          };

          xhr.onerror = () => {
            resolve({
              error: {
                status: "FETCH_ERROR",
                error: "Upload failed"
              } as FetchBaseQueryError
            });
          };

          xhr.send(formData);
        });
      },
      invalidatesTags: (_result, _error, arg) => [
        { type: "Documents", id: arg.claimId }
      ]
    })
  })
});

export const {
  useGetDocumentsByClaimIdQuery,
  useGetDocumentByIdQuery,
  useLazyGetDocumentByIdQuery,
  useGetRawOcrByIdQuery,
  useGetMappedDataByIdQuery,
  useDeleteDocumentMutation,
  useUploadDocumentMutation
} = documentsApi;
