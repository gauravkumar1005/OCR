"use client";

import { useMemo, useState } from "react";
import { Document, Page } from "react-pdf";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function PdfViewer({ fileUrl }: { fileUrl: string | null }) {
  const [pageCount, setPageCount] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.05);

  const options = useMemo(() => ({ cMapUrl: "/cmaps/", standardFontDataUrl: "/standard_fonts/" }), []);

  if (!fileUrl) {
    return (
      <Card className="h-full">
        <CardContent className="flex h-full min-h-[520px] items-center justify-center p-6 text-center text-slate-400">
          Select a document to preview the PDF.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full overflow-hidden">
      <CardHeader className="border-b border-white/10 bg-white/[0.02]">
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>Document Preview</CardTitle>
            <p className="mt-1 text-sm text-slate-400">Rendered with React PDF</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setScale((value) => Math.max(0.6, value - 0.1))}>
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={() => setScale((value) => Math.min(1.8, value + 0.1))}>
              <ZoomIn className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 p-4">
        <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-300">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPageNumber((value) => Math.max(1, value - 1))}
            disabled={pageNumber <= 1}
          >
            <ChevronLeft className="h-4 w-4" />
            Prev
          </Button>
          <span>
            Page {pageNumber} / {pageCount || "?"}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPageNumber((value) => Math.min(pageCount || value + 1, value + 1))}
            disabled={pageCount > 0 && pageNumber >= pageCount}
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex min-h-[640px] justify-center overflow-auto rounded-3xl border border-white/10 bg-slate-950/50 p-4">
          <Document
            file={fileUrl}
            options={options}
            onLoadSuccess={({ numPages }) => {
              setPageCount(numPages);
              setPageNumber(1);
            }}
            loading={<Skeleton className="h-[640px] w-full max-w-3xl" />}
            error={<div className="text-sm text-rose-300">PDF preview is unavailable for this document.</div>}
          >
            <Page
              pageNumber={pageNumber}
              scale={scale}
              renderTextLayer={false}
              renderAnnotationLayer={false}
              loading={<Skeleton className="h-[640px] w-full max-w-3xl" />}
              className="shadow-2xl"
            />
          </Document>
        </div>
      </CardContent>
    </Card>
  );
}
