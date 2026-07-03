"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, FileStack, Loader2, XCircle } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";
import { useLazyGetDocumentByIdQuery, useGetDocumentsByClaimIdQuery } from "@/features/documents/api";

import { ClaimSearch } from "@/components/claim-search";
import type { DocumentSummary } from "@/features/documents/types";
import { DataTable } from "@/components/data-table";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/status-badge";
import { readWorkspaceClaims } from "@/lib/workspace-storage";

function StatCard({
  label,
  value,
  subtext,
  icon: Icon
}: {
  label: string;
  value: string | number;
  subtext?: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <Card className="relative overflow-hidden">
      <div className="absolute inset-0 bg-aurora opacity-25" />
      <CardContent className="relative space-y-3 p-5">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-slate-400">{label}</p>
          <Icon className="h-5 w-5 text-cyan-300" />
        </div>
        <div className="text-3xl font-semibold tracking-tight text-white">{value}</div>
        {subtext ? <p className="text-xs text-slate-400">{subtext}</p> : null}
      </CardContent>
    </Card>
  );
}

const recentUploadColumns: ColumnDef<DocumentSummary>[] = [
  {
    header: "Document",
    cell: ({ row }) => (
      <div className="space-y-1">
        <p className="font-medium text-white">{row.original.documentId}</p>
        <p className="text-xs text-slate-400">{row.original.documentType ?? "Unknown type"}</p>
      </div>
    )
  },
  {
    header: "Status",
    cell: ({ row }) => <StatusBadge value={row.original.processingStatus} />
  },
  {
    header: "Action",
    cell: ({ row }) => (
      <Button asChild variant="ghost" size="sm">
        <a href={`/documents/${row.original.documentId}`}>Open</a>
      </Button>
    )
  }
];

function DashboardMetrics({ claimId }: { claimId: string }) {
  const { data: documents = [], isLoading, isError } = useGetDocumentsByClaimIdQuery(claimId, {
    skip: !claimId
  });
  const [triggerDocument] = useLazyGetDocumentByIdQuery();
  const [metrics, setMetrics] = useState({ ocrProcessing: 0, completed: 0, failed: 0 });

  useEffect(() => {
    let active = true;

    async function loadMetrics() {
      if (!claimId || documents.length === 0) {
        setMetrics({ ocrProcessing: 0, completed: 0, failed: 0 });
        return;
      }

      const results = await Promise.all(
        documents.map(async (doc) => {
          try {
            return await triggerDocument(doc.documentId).unwrap();
          } catch {
            return null;
          }
        })
      );

      if (!active) return;

      setMetrics({
        completed: results.filter((item) => item?.processingStatus === "COMPLETED").length,
        failed: results.filter((item) => item?.processingStatus === "FAILED").length,
        ocrProcessing: results.filter((item) => {
          const status = item?.processingStatus;
          return status === "OCR_IN_PROGRESS" || status === "MAPPING_IN_PROGRESS";
        }).length
      });
    }

    loadMetrics();

    return () => {
      active = false;
    };
  }, [claimId, documents, triggerDocument]);

  return (
    <>
      <StatCard label="Total Documents" value={documents.length} subtext={claimId ? `Claim ${claimId}` : "Open a claim to load documents"} icon={FileStack} />
      <StatCard label="OCR Processing" value={isLoading ? "..." : metrics.ocrProcessing} subtext="Queued or mapping in progress" icon={Loader2} />
      <StatCard label="Completed Documents" value={metrics.completed} subtext="Ready for review" icon={CheckCircle2} />
      <StatCard label="Failed Documents" value={metrics.failed} subtext={isError ? "Load failed" : "Needs attention"} icon={XCircle} />
    </>
  );
}

export function DashboardScreen() {
  const searchParams = useSearchParams();
  const claimId = searchParams.get("claimId") ?? readWorkspaceClaims()[0] ?? "";
  const workspaceClaims = readWorkspaceClaims();
  const { data: documents = [], isLoading, isError } = useGetDocumentsByClaimIdQuery(claimId, {
    skip: !claimId
  });

  const recentRows = documents.slice(0, 8);

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Operations dashboard"
        title="Insurance Document Intelligence Platform"
        description="Track OCR jobs, review incoming documents, and jump into claim-level analysis in a polished enterprise workspace."
        actions={
          <Button asChild variant="outline">
            <a href="/upload">Upload document</a>
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Total Claims" value={workspaceClaims.length} subtext="Tracked in this workspace" icon={FileStack} />
        <DashboardMetrics claimId={claimId} />
      </div>

      <ClaimSearch initialClaimId={claimId} />

      <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Recent Uploads</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!claimId ? (
              <div className="rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-slate-400">
                Search a claim ID to view uploads and processing status.
              </div>
            ) : isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
            ) : isError ? (
              <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-5 text-sm text-rose-200">
                Failed to load documents for this claim.
              </div>
            ) : (
              <DataTable
                columns={recentUploadColumns}
                data={recentRows}
                emptyState="No documents found for this claim."
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Workspace notes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-slate-300">
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="font-medium text-white">Claim navigation</p>
              <p className="mt-2 text-slate-400">Search any claim ID to inspect its upload pipeline and open the viewer.</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="font-medium text-white">Status model</p>
              <p className="mt-2 text-slate-400">Documents move from OCR in progress to completed or failed after mapping completes.</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="font-medium text-white">Recent claim activity</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {workspaceClaims.slice(0, 5).map((claim) => (
                  <Badge key={claim} variant="outline">
                    {claim}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
