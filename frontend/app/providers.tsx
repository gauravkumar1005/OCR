"use client";

import { useEffect } from "react";
import { Provider } from "react-redux";
import { pdfjs } from "react-pdf";
import { Toaster } from "sonner";

import { store } from "@/store/store";

export function Providers({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    pdfjs.GlobalWorkerOptions.workerSrc = new URL(
      "pdfjs-dist/build/pdf.worker.min.mjs",
      import.meta.url
    ).toString();
  }, []);

  return (
    <Provider store={store}>
      {children}
      <Toaster richColors position="top-right" closeButton />
    </Provider>
  );
}
