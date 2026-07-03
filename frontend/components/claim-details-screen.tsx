"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, FileStack } from "lucide-react";
import Link from "next/link";

import { DocumentCard } from "@/components/document-card";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useGetDocumentsByClaimIdQuery } from "@/features/documents/api";
import { rememberWorkspaceClaim } from "@/lib/workspace-storage";

export function ClaimDetailsScreen({ claimId }: { claimId: string }) {
  const { data: documents = [], isLoading, isError } = useGetDocumentsByClaimIdQuery(claimId);

  useEffect(() => {
    rememberWorkspaceClaim(claimId);
  }, [claimId]);

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Claim details"
        title={`Claim ${claimId}`}
        description="All documents for the selected claim are grouped here with processing state and upload metadata."
        actions={
          <Button asChild variant="outline">
            <Link href="/">
              <ArrowLeft className="h-4 w-4" />
              Back to dashboard
            </Link>
          </Button>
        }
      />

      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-4 p-5">
          <div>
            <p className="text-sm text-slate-400">Claim overview</p>
            <p className="mt-1 text-2xl font-semibold text-white">{documents.length} documents loaded</p>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-slate-300">
            <FileStack className="h-4 w-4" />
            Claim ID: {claimId}
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <Skeleton className="h-44 rounded-3xl" />
          <Skeleton className="h-44 rounded-3xl" />
          <Skeleton className="h-44 rounded-3xl" />
        </div>
      ) : isError ? (
        <Card className="border-rose-500/20">
          <CardContent className="p-6 text-sm text-rose-300">Failed to load documents for this claim.</CardContent>
        </Card>
      ) : documents.length === 0 ? (
        <Card>
          <CardContent className="space-y-3 p-8 text-center">
            <p className="text-lg font-medium text-white">No documents found</p>
            <p className="text-sm text-slate-400">Upload a PDF to start the OCR and mapping workflow for this claim.</p>
            <Button asChild>
              <Link href="/upload">Upload document</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {documents.map((document) => (
            <motion.div key={document.documentId} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
              <DocumentCard documentId={document.documentId} documentType={document.documentType} />
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
