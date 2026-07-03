"use client";

import { useMemo } from "react";
import { useDropzone } from "react-dropzone";
import { FileUp, FileText } from "lucide-react";

import { cn } from "@/lib/utils";

export function UploadDropzone({
  file,
  onFileSelected
}: {
  file: File | null;
  onFileSelected: (file: File | null) => void;
}) {
  const acceptedFileTypes = useMemo(
    () => ({
      "application/pdf": [".pdf"]
    }),
    []
  );

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    accept: acceptedFileTypes,
    multiple: false,
    noClick: !!file,
    onDrop: (acceptedFiles) => {
      onFileSelected(acceptedFiles[0] ?? null);
    }
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "glass-panel flex cursor-pointer flex-col items-center justify-center rounded-3xl border border-dashed p-8 text-center transition",
        isDragActive ? "border-cyan-400/60 bg-cyan-400/10" : "border-white/10 hover:border-cyan-400/30 hover:bg-white/[0.04]"
      )}
      onClick={() => {
        if (!file) open();
      }}
    >
      <input {...getInputProps()} />
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/5 text-cyan-300">
        {file ? <FileText className="h-7 w-7" /> : <FileUp className="h-7 w-7" />}
      </div>
      <div className="mt-4 space-y-2">
        <p className="text-base font-semibold text-white">
          {file ? file.name : isDragActive ? "Drop the PDF here" : "Drag and drop your PDF"}
        </p>
        <p className="text-sm text-slate-400">
          PDF only. Uploads are sent directly to the document intelligence pipeline.
        </p>
      </div>

      {file ? (
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onFileSelected(null);
          }}
          className="mt-5 rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:bg-white/5 hover:text-white"
        >
          Remove file
        </button>
      ) : null}
    </div>
  );
}
