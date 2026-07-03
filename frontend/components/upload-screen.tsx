"use client";

import { PageHeader } from "@/components/page-header";
import { UploadForm } from "@/components/upload-form";

export function UploadScreen() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Document intake"
        title="Upload document"
        description="Send a PDF to the backend, trigger OCR asynchronously, and route the claim into the mapping engine."
      />
      <UploadForm />
    </div>
  );
}
