"use client";

import { useEffect } from "react";
import { ArrowLeft, FileSearch } from "lucide-react";
import Link from "next/link";

import { MappedDataPanels } from "@/components/mapped-data-panels";
import { PageHeader } from "@/components/page-header";
import { PdfViewer } from "@/components/pdf-viewer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useGetDocumentByIdQuery, useGetMappedDataByIdQuery, useGetRawOcrByIdQuery } from "@/features/documents/api";
import { formatDate, formatStatus } from "@/lib/format";
import { rememberWorkspaceClaim } from "@/lib/workspace-storage";

const SHOW_PDF_VIEWER = false;

export function DocumentViewerScreen({ documentId }: { documentId: string }) {
  const { data: document, isLoading: documentLoading, isError: documentError } = useGetDocumentByIdQuery(documentId);
  const { data: mappedData, isLoading: mappedLoading, isError: mappedError } = useGetMappedDataByIdQuery(documentId);
  const { data: rawOcr, isLoading: rawLoading, isError: rawError } = useGetRawOcrByIdQuery(documentId);

  useEffect(() => {
    if (document?.claimId) {
      rememberWorkspaceClaim(document.claimId);
    }
  }, [document?.claimId]);

  const isLoading = documentLoading || mappedLoading || rawLoading;
  const hasError = documentError || mappedError || rawError;
  const pageTitle = document ? document.fileName : `Document ${documentId}`;
  const dataSourceLabel = mappedData ? "Mapped data" : rawOcr ? "Raw OCR JSON" : "No extracted data yet";

  return (
    <div className="space-y-8 pb-10">
      <PageHeader
        eyebrow="Document details"
        title={pageTitle}
        description="Review the extracted claim information in a single enterprise view. The PDF panel is temporarily disabled during development to keep verification focused on extracted data."
        actions={
          <>
            {document?.claimId ? (
              <Button asChild variant="outline">
                <Link href={`/claims/${encodeURIComponent(document.claimId)}`}>
                  <ArrowLeft className="h-4 w-4" />
                  Back to claim
                </Link>
              </Button>
            ) : null}
            <Button asChild variant="ghost">
              <Link href="/">
                <FileSearch className="h-4 w-4" />
                Dashboard
              </Link>
            </Button>
          </>
        }
      />

      {isLoading ? (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Skeleton className="h-28 rounded-3xl" />
            <Skeleton className="h-28 rounded-3xl" />
            <Skeleton className="h-28 rounded-3xl" />
            <Skeleton className="h-28 rounded-3xl" />
          </div>
          <Skeleton className="h-[420px] rounded-3xl" />
          <Skeleton className="h-[420px] rounded-3xl" />
        </div>
      ) : hasError || !document ? (
        <Card className="border-rose-500/20 bg-slate-950/60">
          <CardContent className="p-6 text-sm text-rose-300">Failed to load document details.</CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Card className="border-white/10 bg-slate-950/60 shadow-lg shadow-black/10">
              <CardContent className="p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Claim ID</p>
                <p className="mt-2 break-words text-lg font-semibold text-white">{document.claimId}</p>
              </CardContent>
            </Card>
            <Card className="border-white/10 bg-slate-950/60 shadow-lg shadow-black/10">
              <CardContent className="p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Document Type</p>
                <p className="mt-2 break-words text-lg font-semibold text-white">{document.documentType ?? "Unknown document"}</p>
              </CardContent>
            </Card>
            <Card className="border-white/10 bg-slate-950/60 shadow-lg shadow-black/10">
              <CardContent className="p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">OCR Status</p>
                <p className="mt-2 text-lg font-semibold text-white">{formatStatus(document.ocrStatus)}</p>
              </CardContent>
            </Card>
            <Card className="border-white/10 bg-slate-950/60 shadow-lg shadow-black/10">
              <CardContent className="p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Processing Status</p>
                <p className="mt-2 text-lg font-semibold text-white">{formatStatus(document.processingStatus)}</p>
              </CardContent>
            </Card>
          </div>

          <Card className="border-white/10 bg-slate-950/60 shadow-lg shadow-black/10">
            <CardContent className="flex flex-wrap items-center justify-between gap-3 p-5">
              <div>
                <p className="text-sm text-slate-400">Document reference</p>
                <p className="mt-1 text-base font-semibold text-white">{document.documentId}</p>
                <p className="mt-1 text-xs text-slate-500">Uploaded {formatDate(document.createdAt)}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">Source: {dataSourceLabel}</Badge>
                <Badge variant="outline">Upload: {document.uploadStatus}</Badge>
              </div>
            </CardContent>
          </Card>

          <div className="rounded-3xl border border-white/10 bg-white/[0.02] p-4 md:p-6">
            {SHOW_PDF_VIEWER ? <PdfViewer fileUrl={document.cloudinaryUrl} /> : null}

            <div className={`${SHOW_PDF_VIEWER ? "mt-6" : ""} max-h-[calc(100vh-320px)] overflow-y-auto pr-1 scrollbar-thin`}>
              <MappedDataPanels mappedData={mappedData ?? null} rawOcr={rawOcr ?? null} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
