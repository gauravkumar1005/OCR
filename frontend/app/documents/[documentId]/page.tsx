import { DocumentViewerScreen } from "@/components/document-viewer-screen";

export default async function Page({
  params
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;
  return <DocumentViewerScreen documentId={decodeURIComponent(documentId)} />;
}
