"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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

type MetricsState = {
  ocrProcessing: number;
  completed: number;
  failed: number;
};

const EMPTY_METRICS: MetricsState = {
  ocrProcessing: 0,
  completed: 0,
  failed: 0
};

const EMPTY_DOCUMENTS: DocumentSummary[] = [];

function areMetricsEqual(left: MetricsState, right: MetricsState) {
  return left.ocrProcessing === right.ocrProcessing && left.completed === right.completed && left.failed === right.failed;
}

function buildMetrics(results: Array<{ processingStatus?: string | null } | null>): MetricsState {
  return {
    completed: results.filter((item) => item?.processingStatus === "COMPLETED").length,
    failed: results.filter((item) => item?.processingStatus === "FAILED").length,
    ocrProcessing: results.filter((item) => {
      const status = item?.processingStatus;
      return status === "OCR_IN_PROGRESS" || status === "MAPPING_IN_PROGRESS";
    }).length
  };
}

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

function DashboardMetrics({ claimId, mounted }: { claimId: string; mounted: boolean }) {
  const queryResult = useGetDocumentsByClaimIdQuery(claimId, {
    skip: !mounted || !claimId
  });
  const documents = mounted ? queryResult.data ?? EMPTY_DOCUMENTS : EMPTY_DOCUMENTS;
  const documentsSignature = useMemo(
    () => documents.map((doc) => `${doc.documentId}:${doc.processingStatus ?? ""}`).join("|"),
    [documents]
  );
  const stableDocuments = useMemo(() => documents, [documentsSignature]);
  const [triggerDocument] = useLazyGetDocumentByIdQuery();
  const triggerDocumentRef = useRef(triggerDocument);
  const [metrics, setMetrics] = useState<MetricsState>(EMPTY_METRICS);

  useEffect(() => {
    triggerDocumentRef.current = triggerDocument;
  }, [triggerDocument]);

  const loadMetrics = useCallback(
    async (isActive: () => boolean) => {
      if (!mounted || !claimId || stableDocuments.length === 0) {
        setMetrics((current) => (areMetricsEqual(current, EMPTY_METRICS) ? current : EMPTY_METRICS));
        return;
      }

      const results = await Promise.all(
        stableDocuments.map(async (doc) => {
          try {
            return await triggerDocumentRef.current(doc.documentId).unwrap();
          } catch {
            return null;
          }
        })
      );

      if (!isActive()) return;

      const nextMetrics = buildMetrics(results);
      setMetrics((current) => (areMetricsEqual(current, nextMetrics) ? current : nextMetrics));
    },
    [claimId, mounted, stableDocuments]
  );

  useEffect(() => {
    if (!mounted) return;

    let active = true;
    void loadMetrics(() => active);

    return () => {
      active = false;
    };
  }, [mounted, loadMetrics]);

  const displayValue = mounted ? documents.length : "...";
  const displayOcrProcessing = mounted ? (queryResult.isLoading ? "..." : metrics.ocrProcessing) : "...";
  const displayCompleted = mounted ? metrics.completed : "...";
  const displayFailed = mounted ? metrics.failed : "...";

  return (
    <>
      <StatCard label="Total Documents" value={displayValue} subtext={claimId ? `Claim ${claimId}` : "Open a claim to load documents"} icon={FileStack} />
      <StatCard label="OCR Processing" value={displayOcrProcessing} subtext="Queued or mapping in progress" icon={Loader2} />
      <StatCard label="Completed Documents" value={displayCompleted} subtext="Ready for review" icon={CheckCircle2} />
      <StatCard label="Failed Documents" value={displayFailed} subtext={mounted && queryResult.isError ? "Load failed" : "Needs attention"} icon={XCircle} />
    </>
  );
}

export function DashboardScreen() {
  const searchParams = useSearchParams();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const claimIdFromUrl = searchParams.get("claimId") ?? "";
  const workspaceClaims = mounted ? readWorkspaceClaims() : [];
  const claimId = claimIdFromUrl || (mounted ? workspaceClaims[0] ?? "" : "");
  const { data: documents = [], isLoading, isError } = useGetDocumentsByClaimIdQuery(claimId, {
    skip: !mounted || !claimId
  });

  const recentRows = mounted ? documents.slice(0, 8) : EMPTY_DOCUMENTS;
  const totalClaimsValue = mounted ? workspaceClaims.length : "...";

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
        <StatCard label="Total Claims" value={totalClaimsValue} subtext="Tracked in this workspace" icon={FileStack} />
        <DashboardMetrics claimId={claimId} mounted={mounted} />
      </div>

      <ClaimSearch initialClaimId={claimId} />

      <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Recent Uploads</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!mounted || !claimId ? (
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
                {mounted ? workspaceClaims.slice(0, 5).map((claim) => (
                  <Badge key={claim} variant="outline">
                    {claim}
                  </Badge>
                )) : null}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
