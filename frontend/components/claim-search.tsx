"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter, useSearchParams } from "next/navigation";
import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { rememberWorkspaceClaim } from "@/lib/workspace-storage";

const schema = z.object({
  claimId: z.string().min(1, "Claim ID is required").max(64, "Claim ID is too long")
});

type FormValues = z.infer<typeof schema>;

export function ClaimSearch({ initialClaimId }: { initialClaimId?: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { register, handleSubmit, reset } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { claimId: initialClaimId ?? searchParams.get("claimId") ?? "" }
  });

  useEffect(() => {
    if (initialClaimId) {
      reset({ claimId: initialClaimId });
    }
  }, [initialClaimId, reset]);

  const onSubmit = handleSubmit(({ claimId }) => {
    rememberWorkspaceClaim(claimId);
    router.push(`/claims/${encodeURIComponent(claimId)}`);
  });

  return (
    <form onSubmit={onSubmit} className="glass-panel flex flex-col gap-4 rounded-3xl p-5 md:flex-row md:items-end">
      <div className="flex-1 space-y-2">
        <Label htmlFor="claimId">Claim ID</Label>
        <Input id="claimId" placeholder="CLM202600001" {...register("claimId")} />
      </div>
      <Button type="submit" className="md:w-auto">
        <Search className="h-4 w-4" />
        Open claim
      </Button>
    </form>
  );
}
