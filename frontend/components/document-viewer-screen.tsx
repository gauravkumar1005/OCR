"use client";

import { useEffect } from "react";
import { ArrowLeft, FileSearch } from "lucide-react";
import Link from "next/link";

import { MappedDataPanels } from "@/components/mapped-data-panels";
import { PageHeader } from "@/components/page-header";
import { PdfViewer } from "@/components/pdf-viewer";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useGetDocumentByIdQuery, useGetMappedDataByIdQuery } from "@/features/documents/api";
import { rememberWorkspaceClaim } from "@/lib/workspace-storage";

export function DocumentViewerScreen({ documentId }: { documentId: string }) {
  const { data: document, isLoading: documentLoading, isError: documentError } = useGetDocumentByIdQuery(documentId);
  const { data: mappedData, isLoading: mappedLoading, isError: mappedError } = useGetMappedDataByIdQuery(documentId);

  useEffect(() => {
    if (document?.claimId) {
      rememberWorkspaceClaim(document.claimId);
    }
  }, [document?.claimId]);

  const isLoading = documentLoading || mappedLoading;
  const hasError = documentError || mappedError;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Document viewer"
        title={document ? document.fileName : `Document ${documentId}`}
        description="Split-screen review of the uploaded PDF and the frontend-friendly mapped data."
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
        <div className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
          <Skeleton className="h-[760px] rounded-3xl" />
          <div className="space-y-4">
            <Skeleton className="h-40 rounded-3xl" />
            <Skeleton className="h-40 rounded-3xl" />
            <Skeleton className="h-40 rounded-3xl" />
          </div>
        </div>
      ) : hasError || !document ? (
        <Card className="border-rose-500/20">
          <CardContent className="p-6 text-sm text-rose-300">Failed to load document details.</CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
          <PdfViewer fileUrl={document.cloudinaryUrl} />
          <div className="space-y-6">
            <Card>
              <CardContent className="flex flex-wrap items-center justify-between gap-3 p-5">
                <div>
                  <p className="text-sm text-slate-400">Document reference</p>
                  <p className="mt-1 text-lg font-semibold text-white">{document.documentType ?? "Unknown document"}</p>
                </div>
                <div className="rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-xs text-slate-300">
                  {document.documentId}
                </div>
              </CardContent>
            </Card>
            <MappedDataPanels mappedData={mappedData ?? null} />
          </div>
        </div>
      )}
    </div>
  );
}
