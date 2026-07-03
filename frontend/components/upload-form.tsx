"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Loader2, Upload } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { UploadDropzone } from "@/components/upload-dropzone";
import { useUploadDocumentMutation } from "@/features/documents/api";
import { rememberWorkspaceClaim } from "@/lib/workspace-storage";

const schema = z.object({
  claimId: z.string().min(1, "Claim ID is required").max(64, "Claim ID is too long"),
  documentType: z.string().min(1, "Document type is required")
});

type FormValues = z.infer<typeof schema>;

const documentTypes = [
  "combined_document",
  "discharge_summary",
  "investigation_report",
  "hospital_bill",
  "claim_form",
  "prescription",
  "lab_report"
];

export function UploadForm() {
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [uploadDocument, { isLoading }] = useUploadDocumentMutation();

  const defaultValues = useMemo(() => ({ claimId: "", documentType: "combined_document" }), []);
  const { register, handleSubmit, formState } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues
  });

  const onSubmit = handleSubmit(async (values) => {
    if (!selectedFile) {
      toast.error("Please select a PDF file");
      return;
    }

    try {
      setProgress(0);
      const result = await uploadDocument({
        claimId: values.claimId,
        documentType: values.documentType,
        file: selectedFile,
        onProgress: setProgress
      }).unwrap();

      toast.success(result.message || "Upload submitted successfully");
      rememberWorkspaceClaim(values.claimId);
      router.push(`/claims/${encodeURIComponent(values.claimId)}`);
    } catch (error) {
      toast.error("Upload failed. Please review the document and try again.");
    }
  });

  return (
    <Card className="overflow-hidden">
      <CardHeader className="border-b border-white/10 bg-white/[0.02]">
        <CardTitle>Upload a document package</CardTitle>
        <p className="text-sm text-slate-400">
          Upload a PDF to trigger Cloudinary storage, OCR dispatch, and mapped document generation.
        </p>
      </CardHeader>
      <CardContent className="space-y-6 p-5">
        <form onSubmit={onSubmit} className="space-y-6">
          <div className="grid gap-5 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="claimId">Claim ID</Label>
              <Input id="claimId" placeholder="CLM202600001" {...register("claimId")} />
              {formState.errors.claimId ? <p className="text-xs text-rose-300">{formState.errors.claimId.message}</p> : null}
            </div>
            <div className="space-y-2">
              <Label htmlFor="documentType">Document Type</Label>
              <Select id="documentType" defaultValue="combined_document" {...register("documentType")}>
                {documentTypes.map((type) => (
                  <option key={type} value={type}>
                    {type.replace(/_/g, " ")}
                  </option>
                ))}
              </Select>
              {formState.errors.documentType ? (
                <p className="text-xs text-rose-300">{formState.errors.documentType.message}</p>
              ) : null}
            </div>
          </div>

          <UploadDropzone file={selectedFile} onFileSelected={setSelectedFile} />

          <div className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <div className="flex items-center justify-between text-sm text-slate-300">
              <span>Upload progress</span>
              <span>{progress}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-white/5">
              <div className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-blue-500 to-emerald-400 transition-all duration-300" style={{ width: `${progress}%` }} />
            </div>
          </div>

          <div className="flex items-center justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setSelectedFile(null);
                setProgress(0);
              }}
            >
              Reset
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
              Submit upload
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
