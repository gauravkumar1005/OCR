import { ClaimDetailsScreen } from "@/components/claim-details-screen";

export default async function Page({
  params
}: {
  params: Promise<{ claimId: string }>;
}) {
  const { claimId } = await params;
  return <ClaimDetailsScreen claimId={decodeURIComponent(claimId)} />;
}
