"use client";

import Link from "next/link";
import { CalendarDays, ChevronRight, FileText } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/status-badge";
import { useGetDocumentByIdQuery } from "@/features/documents/api";
import { formatDate } from "@/lib/format";

export function DocumentCard({
  documentId,
  documentType
}: {
  documentId: string;
  documentType: string | null;
}) {
  const { data, isLoading, isError } = useGetDocumentByIdQuery(documentId);

  if (isLoading) {
    return <Skeleton className="h-44 rounded-3xl" />;
  }

  if (isError || !data) {
    return (
      <Card className="border-rose-500/20">
        <CardContent className="p-5 text-sm text-rose-300">Failed to load document details.</CardContent>
      </Card>
    );
  }

  return (
    <Card className="group transition hover:border-cyan-400/30 hover:shadow-glow">
      <CardHeader className="flex-row items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 rounded-2xl bg-cyan-400/10 p-3 text-cyan-300">
            <FileText className="h-5 w-5" />
          </div>
          <div className="space-y-1">
            <CardTitle>{documentType ?? data.documentType ?? "Document"}</CardTitle>
            <p className="text-sm text-slate-400">{data.fileName}</p>
          </div>
        </div>
        <Link href={`/documents/${documentId}`} className="rounded-full border border-white/10 p-2 text-slate-300 transition hover:bg-white/5 hover:text-white">
          <ChevronRight className="h-4 w-4" />
        </Link>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge value={data.processingStatus} />
          <StatusBadge value={data.ocrStatus} />
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <CalendarDays className="h-4 w-4" />
          <span>Uploaded {formatDate(data.createdAt)}</span>
        </div>
      </CardContent>
    </Card>
  );
}
